Parameterizing Tests Using the stdlib unittest
==============================================


Test parameterization is an often-requested feature.  Support for it has been
added to Nose via plugin, and py.test supports it.  But if for some reason you
need to stick with the standard library unittest framework, it has no built in
way to do this.  This module is essentially a proposal for how to add this
feature to the stdlib.

This package consists of a single module, parameterizable_tests, containing two
decorators: parameterizable and parameters.  The former is a class decorator,
and makes it possible to parameterize any test in the decorated class.  The
second is a method decorator, and provides a way to specify the parameters to
be used with a specific test.

You can install the package by hand by just copying the module to an
appropriate location, or you can install it using pip.


Usage
-----

parameterizable is a simple class decorator that takes no arguments.

parameters takes a single argument, which is either a dict or a list containing
the parameters for a test.  If a dict, the keys of the dict are used to
complete the test name.  If a list, the elements of the list are stringified
and joined by '_' characters to complete the test name.  Thus, given:

    @parameters(1, 2)
    def test_foo(self, arg):
        pass

there will be two tests, 'test_foo_1', and 'test_foo_2', the first of which
will be passed 1 for arg, and the second of which will be passed 2 for arg.  On
the other hand,

    @parameters(a=(1, 2), b=(3, 4))
    def test_foo(self, arg1, arg2):
        pass

will produce tests named 'test_foo_a' and 'test_foo_b' which will each be
passed two arguments.  You can also specify the special keyword argument
_include_key, in which case the key that names the parameter list is
passed as the first non-self argument to the test:

    @parameters(a=(1, 2), b=(3, 4), _include_key=True)
    def test_foo(self, key, arg1, arg2):
        pass

key here will be 'a' when arg1 and arg2 are (1, 2), and 'b' when they
are (3, 4).

The individual parameter lists may be single arguments, lists of positional
arguments, or dictionaries of keyword arguments.  For example:

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
