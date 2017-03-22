"""Support for parameterizing test methods in a unittest TestCase.

This module provides two decorators: a class decorator named 'parameterizable',
and a method decorator named 'parameters'.  In order for the parameters
decorator to do anything useful, the test class must be decorated with the
parameterizable decorator.

parameterizable is a simple class decorator that takes no arguments.

parameterize takes 

"""
import collections
from functools import wraps


def parameters(parameters, **kw):
    def parameterize_decorator(func):
        @wraps(func)
        def parameterize_wrap_function(*args, **kw):
            return func(*args, **kw)
        parameterize_wrap_function._parameterized_ = True
        parameterize_wrap_function._parameters_ = parameters
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
    """A test method parameterization class decorator.

    Tests to be parameterized must be decorated using the 'parameters'
    decorator, which is passed the values for the parameters.  The va

    The value of the _params attribute may be either a dictionary or a list.
    The values in the dictionary and the elements of the list may either be
    single values, or a list.  If single values, they are turned into single
    element tuples.  However derived, the resulting sequence is passed via
    *args to the parameterized test function.

    In a _params dictioanry, the keys become part of the name of the generated
    tests.  In a _params list, the values in the list are converted into a
    string by joining the string values of the elements of the tuple by '_' and
    converting any blanks into '_'s, and this become part of the name.
    The  full name of a generated test is a 'test_' prefix, the portion of the
    test function name after the  '_as_' separator, plus an '_', plus the name
    derived as explained above.

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

    Note: if and only if the generated test name is a valid identifier can it
    be used to select the test individually from the unittest command line.

    """
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

