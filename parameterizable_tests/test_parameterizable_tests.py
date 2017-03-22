import unittest

from parameterizable_tests import parameterizable, parameters
# Legacy
from parameterizable_tests import parameterize


class TestParaterizableTests(unittest.TestCase):

    def test_normal_tests_run(self):
        res = []

        @parameterizable
        class Test(unittest.TestCase):
            def test_normal_tests_run(self):
                res.append(1)
            @parameters()
            def test_foo(self):
                raise Exception("This should not be run in this test")
        Test(methodName='test_normal_tests_run').run()
        self.assertEqual([1], res)

    def test_single_arg_parameters(self):
        res = []
        @parameterizable
        class Test(unittest.TestCase):
            @parameters(1, 2)
            def test_foo(self, arg):
                res.append(arg)
        Test(methodName='test_foo_1').run()
        self.assertEqual([1], res)
        Test(methodName='test_foo_2').run()
        self.assertEqual([1, 2], res)
        with self.assertRaises(ValueError):
            Test(methodName='test_foo_3').run()

    def test_multiple_arg_parameters(self):
        res = []
        @parameterizable
        class Test(unittest.TestCase):
            @parameters((1, 7), (2, 3))
            def test_foo(self, arg1, arg2):
                res.append((arg1, arg2))
        Test(methodName='test_foo_1_7').run()
        self.assertEqual([(1, 7)], res)
        Test(methodName='test_foo_2_3').run()
        self.assertEqual([(1, 7), (2, 3)], res)

    # XXX dicts as parameters don't work unless you are using a dict for the
    # sets of parameters...with just a list of dicts the method names clash
    # because it uses the dict keys in the method names.

    def test_dict_parameters(self):
        res = []
        @parameterizable
        class Test(unittest.TestCase):
            @parameters(foo=dict(a=1, b=2), bar=dict(b=7))
            def test_foo(self, a=None, b=None):
                res.append((a, b))
        Test(methodName='test_foo_foo').run()
        self.assertEqual([(1, 2)], res)
        Test(methodName='test_foo_bar').run()
        self.assertEqual([(1, 2), (None, 7)], res)

    def test_dict_of_parameters(self):
        res = []
        @parameterize
        class Test(unittest.TestCase):
            # XXX this fails if you say just a=1, b=2; that should be fixed.
            @parameters(a=(1,), b=(2,))
            def test_bar(self, arg):
                res.append(arg)
        Test(methodName='test_bar_a').run()
        self.assertEqual([1], res)
        Test(methodName='test_bar_b').run()
        self.assertEqual([1, 2], res)

    def test_mixed_lists_and_dicts(self):
        res = []
        @parameterize
        class Test(unittest.TestCase):
            @parameters(a=(1,), b=dict(z=1, k=3))
            def test_bar(self, z, k=None):
                res.append((z, k))
        Test(methodName='test_bar_a').run()
        self.assertEqual([(1, None)], res)
        Test(methodName='test_bar_b').run()
        self.assertEqual([(1, None), (1, 3)], res)


class TestLegacyAPI(unittest.TestCase):

    # Python2 compat
    if hasattr(unittest.TestCase, 'assertRaisesRegexp'):
        assertRaisesRegex = unittest.TestCase.assertRaisesRegexp

    def test_normal_tests_run(self):
        res = []
        @parameterize
        class Test(unittest.TestCase):
            def test_normal_tests_run(self):
                res.append(1)
            foo_params = [1, 2]
            def foo_as_bar(self, arg):
                raise Exception("This should not be run in this test")
        Test(methodName='test_normal_tests_run').run()
        self.assertEqual([1], res)

    def test_test_method_must_exist(self):
        with self.assertRaisesRegex(ValueError, "(?i)No test"):
            @parameterize
            class Test(unittest.TestCase):
                foo_params = [1, 2]
                def test_with_wrong_name(self, arg):
                    pass

    def test_test_data_must_exist(self):
        with self.assertRaisesRegex(ValueError, "(?i)No params"):
            @parameterize
            class Test(unittest.TestCase):
                bad_params_name = [1, 2]
                def foo_as_bar(self, arg):
                    pass

    def test_multiple_test_names_generated_automatically(self):
        res = []
        @parameterize
        class Test(unittest.TestCase):
            foo_params = [1, 2]
            def foo_as_bar(self, arg):
                res.append(arg)
        Test(methodName='test_bar_1').run()
        self.assertEqual([1], res)
        Test(methodName='test_bar_2').run()
        self.assertEqual([1, 2], res)

    def test_names_generated_via_str(self):
        res = []
        @parameterize
        class Test(unittest.TestCase):
            foo_params = [0x30, 13.70]
            def foo_as_bar(self, arg):
                res.append(arg)
        Test(methodName='test_bar_48').run()
        self.assertEqual([48], res)
        Test(methodName='test_bar_13.7').run()
        self.assertEqual([48, 13.7], res)

    def test_multipart_test_names_generated_automatically(self):
        res = []
        @parameterize
        class Test(unittest.TestCase):
            foo_params = [(1, 7), (2, 8)]
            def foo_as_bar(self, arg1, arg2):
                res.append((arg1, arg2))
        Test(methodName='test_bar_1_7').run()
        self.assertEqual([(1, 7)], res)
        Test(methodName='test_bar_2_8').run()
        self.assertEqual([(1, 7), (2, 8)], res)

    def test_multiple_test_names_generated_from_dict_keys(self):
        res = []
        @parameterize
        class Test(unittest.TestCase):
            foo_params = dict(a=(1,), b=(2,))
            def foo_as_bar(self, arg):
                res.append(arg)
        Test(methodName='test_bar_a').run()
        self.assertEqual([1], res)
        Test(methodName='test_bar_b').run()
        self.assertEqual([1, 2], res)

if __name__=='__main__':
    unittest.main()
