"""Support for parameterizing test methods in a unittest TestCase.

This module provides two decorators: a class decorator named 'parameterizable',
and a method decorator named 'parameters'.  In order for the parameters
decorator to do anything useful, the test class must be decorated with the
parameterizable decorator.

parameterizable is a simple class decorator that takes no arguments.

parameters takes a single argument, which is either a dict or a list.
containing the parameters for a test.  If a dict, the keys of the dict
are used to complete the test name.  If a list, the elements of the
list are stringified and joined by '_' characters to complete the
test name.  Thus, given:

    @parameters(1, 2)
    def test_foo(self, arg):
        pass

there will be two tests, 'test_foo_1', and 'test_foo_2', the first of
which will be passed 1 for arg, and the second of which will be passed
2 for arg.  On the other hand,

    @parameters(a=(1, 2), b=(3, 4))
    def test_foo(self, arg1, arg2):
        pass

will produce tests named 'test_foo_a' and 'test_foo_b', that will be
each passed two arguments.

The individual parameter lists may be single arguments, lists of
positional arguments, or dictionaries of keyword arguments.  For example:

    @parameters(a=(1, 2), b=dict(z=7, k=3))
    def test_foo(self, z, y=50, k=100):
        print(z, y, k)

would result in:

    1 2 100
    7 50 3

This allows you to have optional arguments in your test methods, at the cost of
having to specify all the arguments by name when you want to specify any of
them by name.

Note: if test names are generated, than if and only if the generated test name
is a valid identifier can it be used to select the test individually from the
unittest command line.

"""
import collections
from functools import wraps


# TODO: add setting to include the key from a dict of parameter lists in
#       the arguments that are passed to the test function.
# TODO: add a setting that can be used to provide a function to generate
#       the test name.


def parameters(*args, **kw):
    settings = {}
    for name in list(kw):
        if name.startswith('_'):
            settings[name] = kw.pop(name)
    if args and kw:
        raise TypeError("positional and keyword parameter list"
                        " specifications may not be mixed")
    def parameterize_decorator(func):
        @wraps(func)
        def parameterize_wrap_function(*args, **kw):
            return func(*args, **kw)
        parameterize_wrap_function._parameterized_ = True
        parameterize_wrap_function._parameters_ = args if args else kw
        parameterize_wrap_function._settings_ = kw
        return parameterize_wrap_function
    return parameterize_decorator


def generate_tests(base_name, parameters, _test_name=None):
    test_funcs = {}
    # _test_name is for legacy API support.
    name = base_name if _test_name is None else _test_name
    for paramname, params in parameters.items():
        if hasattr(params, 'keys'):
            test = (lambda self, name=name, params=params:
                            getattr(self, name)(**params))
        else:
            test = (lambda self, name=name, params=params:
                            getattr(self, name)(*params))
        testname = base_name + '_' + paramname
        test.__name__ = testname
        test_funcs[testname] = test
    return test_funcs


def parameterizable(cls):
    testfuncs = {}
    paramdicts = {}
    testers = collections.defaultdict(list)
    for name, attr in cls.__dict__.items():
        if (name.endswith('_params') and not hasattr(attr, '__code__')
                or hasattr(attr, '_parameterized_')):
            new_style = hasattr(attr, '_parameterized_')
            if new_style:
                parameters = attr._parameters_
            else:
                parameters = attr
            if not hasattr(parameters, 'keys'):
                d = {}
                for x in parameters:
                    if not hasattr(x, '__iter__'):
                        x = (x,)
                    n = '_'.join(str(v) for v in x).replace(' ', '_')
                    d[n] = x
                parameters = d
            if new_style:
                testfuncs.update(generate_tests(name, parameters))
            else:
                paramdicts[name[:-7] + '_as_'] = parameters
        elif '_as_' in name:
            testers[name.split('_as_')[0] + '_as_'].append(name)
    for name in paramdicts:
        if name not in testers:
            raise ValueError("No tester found for {}".format(name))
    for name in testers:
        if name not in paramdicts:
            raise ValueError("No params found for {}".format(name))
    for name, attr in cls.__dict__.items():
        for paramsname, paramsdict in paramdicts.items():
            if name.startswith(paramsname):
                testnameroot = 'test_' + name[len(paramsname):]
                testfuncs.update(
                    generate_tests(testnameroot, paramsdict, name))
    for key, value in testfuncs.items():
        setattr(cls, key, value)
    return cls


# Backward compatibility.
parameterize = parameterizable

"""
The legacy method of specifying test parameters and tests is that
parameters are specified as the value of a class attribute that ends with
the string '_params'.  Call the portion before '_params' the prefix.  Then
a method to be parameterized must have the same prefix, the string
'_as_', and an arbitrary suffix.

For example, if we have:

    count_params = range(2)

    def count_as_foo_arg(self, foo):
        self.assertEqual(foo+1, myfunc(foo))

we will get parameterized test methods named:
    test_foo_arg_0
    test_foo_arg_1
    test_foo_arg_2

Or we could have:

    example_params = {'foo': ('bar', 1), 'bing': ('bang', 2)}

    def example_as_myfunc_input(self, name, count):
        self.assertEqual(name+str(count), myfunc(name, count))

and get:
    test_myfunc_input_foo
    test_myfunc_input_bing
"""

