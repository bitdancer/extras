import asyncio
import json
import unittest
import threading
from urllib.request import urlopen, URLError
from urllib.parse import urljoin
import logging

from aio_rest_server import (
    create_server, RESTRequestHandler, Router, GET, PUT, POST)
from parameterizabletests import parameterizable, parameters


@parameterizable
class TestRouter(unittest.TestCase):

    paths = {
        'root':          (GET, '/', '/', []),
        'one_var':       (GET, '/xxx/$', '/xxx/bar', ['bar']),
        'two_parm':      (GET, '/abc/$/$', '/abc/bar/bar2', ['bar', 'bar2']),
        'two_parm_post': (POST, '/abc/$/$', '/abc/foo1/foo2', ['foo1', 'foo2']),
        'two_parm_mid':  (GET, '/a/$/f/$', '/a/bar/f/bar2', ['bar', 'bar2']),
        'two_parm_mid_wo_last_var': (GET, '/a/$/f', '/a/foo/f', ['foo']),
        'one_parm_mid':  (GET, '/nnn/$/xyz', '/nnn/ping/xyz', ['ping']),
        'parm_in_mid':   (PUT, '/foo/bar/$/sid', '/foo/bar/yeah/sid', ['yeah']),
        'end_slash_nop': (GET, '/yes/$', '/yes/me/', ['me']),
        'end_slash_nop2': (GET, '/no/$/', '/no/me', ['me']),
        }

    @parameters(paths)
    def test_resolve(self, method, path, test_path, expected_args):
        with self.subTest(path=(path, test_path)):
            routes = Router()
            routes.set_handler_for_path(method, path, 'foo')
            handler, actual_args = routes.resolve(method, test_path)
            self.assertEqual(handler, 'foo')
            self.assertEqual(actual_args, expected_args)

    @parameters(paths)
    def test_full_set_resolve(self, method, path, test_path, expected_args):
        routes = Router()
        for meth, pth, _, _ in self.paths.values():
            routes.set_handler_for_path(meth, pth, 'foo')
        handler, actual_args = routes.resolve(method, test_path)
        self.assertEqual((handler, actual_args), ('foo', expected_args))

    @parameters(paths)
    def test_duplicate(self, method, path, *args):
        routes = Router()
        routes.set_handler_for_path(GET, path, 'foo')
        with self.assertRaises(ValueError):
            routes.set_handler_for_path(GET, path, 'foo')


class RESTServerTestMixin:

    handler = None  # Set this in subclass

    def _create_server_co_ro(self):
        return create_server(self.handler, '127.0.0.1', 0, loop=self.server_loop)

    def _run_server(self):
        started = threading.Event()
        self._stopped_event = threading.Event()
        self.srv_thread = threading.Thread(target=self._server, args=(started,))
        self.srv_thread.start()
        if not started.wait(timeout=3):
            self.fail("server did not start")

    def _server(self, started):
        loop = self.server_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.server = loop.run_until_complete(self._create_server_co_ro())
        self.port = self.server.sockets[0].getsockname()[1]
        self.addCleanup(self._close_loop)
        # the event loop is not running yet, but the socket is listening.
        started.set()
        # Now run the event loop to handle the test request(s).
        loop.run_forever()

    def _stop_hook(self):
        asyncio.ensure_future(self._stop_server(), loop=self.server_loop)

    @asyncio.coroutine
    def _stop_server(self):
        self.server.close()
        yield from self.server.wait_closed()
        yield from self._close_other()
        self.server_loop.stop()
        self._stopped_event.set()

    @asyncio.coroutine
    def _close_other(self):
        pass

    def _close_loop(self):
        self.server_loop.call_soon_threadsafe(self._stop_hook)
        self._stopped_event.wait()
        self.srv_thread.join()
        self.server_loop.close()

    def _make_url(self, path):
        return urljoin('http://127.0.0.1:{}'.format(self.port), path)

    def assert_empty_json_response(self, resp):
        self.assertEqual(resp.headers.get_content_type(), 'application/json')
        self.assertEqual(resp.read(), b'')


class TestServer(RESTServerTestMixin, unittest.TestCase):

    def test_bad_url(self):
        class MyServer(RESTRequestHandler):
            router = Router()
        self.handler = MyServer
        self._run_server()
        with self.assertRaises(URLError) as cm:
            with urlopen(self._make_url('/no_such_url')):
                pass
        self.assertEqual(cm.exception.code, 404)
        self.assert_empty_json_response(cm.exception)

    def test_simple_get(self):
        json_payload = {'foo': 'bar'}
        class MyServer(RESTRequestHandler):
            router = Router()
            @asyncio.coroutine
            @router.handles_path(GET, '/foo')
            def foo(self, message, payload, params={}):
                return json_payload
        self.handler = MyServer
        self._run_server()
        with urlopen(self._make_url('/foo')) as request:
            res = request.read().decode()
        self.assertEqual(json.loads(res), json_payload)

    def test_params_passed_to_paramless_handler(self):
        class MyServer(RESTRequestHandler):
            router = Router()
            @asyncio.coroutine
            @router.handles_path(GET, '/foo')
            def foo(self, message, payload):
                raise Exception("This should not happen")
        self.handler = MyServer
        self._run_server()
        with self.assertRaises(URLError) as cm1:
            urlopen(self._make_url('/foo?test=testing'))
        self.assertEqual(cm1.exception.code, 400)
        self.assert_empty_json_response(cm1.exception)

    def test_params(self):
        class MyServer(RESTRequestHandler):
            router = Router()
            @asyncio.coroutine
            @router.handles_path(GET, '/foo')
            def foo(self, message, payload, param1=10, param2=20):
                return dict(param1=param1, param2=param2)

            @asyncio.coroutine
            @router.handles_path(GET, '/bar')
            def bar(self, message, payload, *, required):
                return dict(required=required)
        self.handler = MyServer
        self._run_server()
        with urlopen(self._make_url('/foo?param1=1')) as request:
            res = request.read().decode()
        self.assertEqual(json.loads(res), {'param1': '1', 'param2': 20})
        with urlopen(self._make_url('/foo?param1=2&param2=3')) as request:
            res = request.read().decode()
        self.assertEqual(json.loads(res), {'param1': '2', 'param2': '3'})
        with self.assertRaises(URLError) as cm1:
            urlopen(self._make_url('/foo?param1=1&test=testing'))
        self.assertEqual(cm1.exception.code, 400)
        self.assert_empty_json_response(cm1.exception)
        with urlopen(self._make_url('/bar?required=test')) as request:
            res = request.read().decode()
        self.assertEqual('{"required": "test"}', res)
        with self.assertRaises(URLError) as cm:
            urlopen(self._make_url('/bar'))
        self.assertEqual(cm.exception.code, 400)
        self.assert_empty_json_response(cm.exception)

    def test_typeerror_inside_route_handler_function(self):
        class MyServer(RESTRequestHandler):
            router = Router()
            @asyncio.coroutine
            @router.handles_path(GET, '/foo')
            def foo(self, message, payload):
                # MyServer is just something convenient to call incorrectly.
                MyServer(badparam='bar')
        self.handler = MyServer
        self._run_server()
        with self.assertLogs('aiohttp.server', logging.ERROR):
            with self.assertRaises(URLError) as cm:
                urlopen(self._make_url('/foo'))
            self.assertEqual(cm.exception.code, 500)
            self.assert_empty_json_response(cm.exception)


if __name__ == '__main__':
    unittest.main()
