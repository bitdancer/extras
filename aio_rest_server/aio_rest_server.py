"""
asyncio (aiohttp) based REST server.

"""

import asyncio
import json
import logging
import time
from urllib.parse import urlparse, parse_qsl
from inspect import signature

import aiohttp
from aiohttp.errors import HttpProcessingError
from aiohttp.log import access_logger
from multidict import MultiDict
import aiohttp.server
from aiohttp.server import RESPONSES

log = logging.getLogger('aio_rest_server')


"""
REST routing.

A Router object records which paths should result in calls to which
functions.  The method handles_path is a decorator, and does the route
registration.  A REST server class is required to define a class level
attribute 'router' that points to a Router instance.  Decorating a
function with @router.handles_path(method, path) then declares that that
particular function or method handles a particular REST call, optionally with
'$' characters representing variable parts of the path.
A router's resolve method takes a real path and method
and returns the name of the handler and a list of arguments extracted from the
URL according to the '$' references in the matching route.

"""

# method constants
GET  = 'GET'
POST = 'POST'
PUT  = 'PUT'
DELETE = 'DELETE'


class Router(dict):

    part = 'root'

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.handlers = {}

    def __missing__(self, key):
        r = self[key] = Router()
        r.part = key
        return r

    def _split_path(self, path):
        parts = path.split('/')
        if not parts[-1]:
            # Ignore trailing slashes.
            parts.pop()
        return parts

    def set_handler_for_path(self, method, path, handler):
        parts = self._split_path(path)
        router = self
        for part in parts:
            router = router[part]
        if method in router.handlers:
            raise ValueError("duplicate path {}".format(path))
        router.handlers[method] = handler

    def resolve(self, method, path):
        parts = self._split_path(path)
        router = self
        args = []
        for part in parts:
            if part not in router:
                if '$' not in router:
                    return None, None
                args.append(part)
                router = router.get('$')
            else:
                router = router.get(part)
        if method not in router.handlers:
            return None, None
        return router.handlers[method], args

    def __repr__(self):
        return 'Router(part={}, handlers={}, dict={}'.format(
            self.part, self.handlers, super().__repr__())

    def handles_path(self, method, path):
        def add_handler(handler):
            self.set_handler_for_path(method, path, handler.__name__)
            return handler
        return add_handler


"""
HTTP Request handling.

REST method handlers are decorated with @handles_path(method, path), where path
is a URL with any variable parts that should be passed in as function arguments
replaced by '$' characters, and method is one of the constants above.  For
example:

@asyncio.coroutine
@router.handles_path(POST, '/resource/$/items/$')
def resource_item(self, message, payload, resource_name, item_id, param1=None):
  # do something

gets called if a POST request is sent to url '/resource/foo/items/bar'.  The
'message' and 'payload' arguments are passed through from the RESTRequestHandler
handle_request method (see the aiohttp docs); 'foo' and 'bar' are passed to
fill the next two arguments.  Remaining arguments are filled by keyword from
the params dict parsed from the query string.

"""

class RESTError(HttpProcessingError):

    def __init__(self, code, message=None, **kwargs):
        super().__init__(code=code, message=message, **kwargs)


class RESTRequestHandler(aiohttp.server.ServerHttpProtocol):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('access_log', access_logger)
        super().__init__(*args, **kwargs)

    def handle_error(self, status=500, message=None,
                     payload=None, exc=None, headers=None, reason=None):
        """Handle errors.

        Returns HTTP response with specific status code. Logs additional
        information. It always closes current connection.

        The implementation below is based on the default from:
        http://aiohttp.readthedocs.io/en/1.3.3/_modules/aiohttp/server.html#ServerHttpProtocol.handle_error

        It was modified in order to truncate error responses for prodcution
        deployments and also to make sure they have appropriate json headers.
        """
        now = self._loop.time()
        try:
            if self.transport is None:
                # client has been disconnected during writing.
                return ()

            if status == 500:
                self.log_exception("Error handling request")

            try:
                if reason is None or reason == '':
                    reason, msg = RESPONSES[status]
                else:
                    msg = reason
            except KeyError:
                status = 500
                reason, msg = '???', ''

            if self.debug and exc is not None:
                data = {'result': 'error', 'data': msg}
                body = json.dumps(data).encode('utf-8')
            else:
                body = b''

            response = aiohttp.Response(self.writer, status, close=True)
            response.add_header(aiohttp.hdrs.CONTENT_TYPE,
                                'application/json; charset=utf-8')
            response.add_header(aiohttp.hdrs.CONTENT_LENGTH, str(len(body)))
            if headers is not None:
                for name, value in headers:
                    response.add_header(name, value)
            response.send_headers()

            response.write(body)
            # disable CORK, enable NODELAY if needed
            self.writer.set_tcp_nodelay(True)
            drain = response.write_eof()

            self.log_access(message, None, response, self._loop.time() - now)
            return drain
        finally:
            self.keep_alive(False)

    @asyncio.coroutine
    def handle_request(self, message, payload):
        now = time.time()
        log.debug("handling '%s %s'", message.method, message.path)
        url = urlparse(message.path)
        params = MultiDict(parse_qsl(url.query))
        handler, args = self.router.resolve(message.method, url.path)
        if handler is None:
            msg = "No handler found"
            log.debug(msg)
            raise RESTError(404, msg)
        handler = getattr(self, handler)
        sig = signature(handler)
        try:
            bound = sig.bind(message, payload, *args, **params)
        except TypeError as exc:
            raise RESTError(400, str(exc))
        data = yield from handler(*bound.args, **bound.kwargs)
        resp = aiohttp.Response(self.writer, 200, http_version=message.version)
        yield from self._send_data(resp, data)
        self.log_access(message, None, resp, time.time() - now)
        yield from resp.write_eof()

    @asyncio.coroutine
    def _send_data(self, resp, data):
        resp.add_header('Content-Type', 'application/json')
        body = json.dumps(data).encode('utf-8')
        resp.add_header('Content-Length', str(len(body)))
        resp.send_headers()
        resp.write(body)


"""
Server.

To create a server, subclass RESTRequestHandler and define REST handler method.
Then call create_server, passing the class and the address and port on which to
listen.  All other arguments will be passed through to the handler class
constructor.

"""

@asyncio.coroutine
def create_server(handler_class, addr, port, loop=None, ssl=None, *args, **kw):
    loop = asyncio.get_event_loop() if loop is None else loop
    return (yield from loop.create_server(
        lambda: handler_class(*args, loop=loop, **kw),
        addr, port, ssl=ssl))
