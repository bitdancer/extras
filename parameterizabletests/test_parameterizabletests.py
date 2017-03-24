import unittest

from parameterizabletests import parameterizable, parameters
# Legacy
from parameterizabletests import parameterize


class TestParaterizableTests(unittest.TestCase):

    def runTest(self, testcase, testname):
        res = testcase(methodName=testname).run()
        self.assertEqual(1, res.testsRun)
        self.assertEqual([], res.failures)
        self.assertEqual([], res.errors)
        self.assertTrue(res.wasSuccessful())

    def test_normal_tests_run(self):
        res = []
        @parameterizable
        class Test(unittest.TestCase):
            def test_normal_tests_run(self):
                res.append(1)
            @parameters()
            def test_foo(self):
                raise Exception("This should not be run in this test")
        self.runTest(Test, 'test_normal_tests_run')

    def test_single_arg_parameters(self):
        res = []
        @parameterizable
        class Test(unittest.TestCase):
            @parameters(1, 2)
            def test_foo(self, arg):
                res.append(arg)
        self.runTest(Test, 'test_foo_1')
        self.assertEqual([1], res)
        self.runTest(Test, 'test_foo_2')
        self.assertEqual([1, 2], res)
        with self.assertRaises(ValueError):
            Test(methodName='test_foo_3').run()

    def test_multiple_arg_parameters(self):
        res = []
        @parameterizable
        class Test(unittest.TestCase):
            @parameters((1, 7), (2, 3))
            def test_foo(self, *args):
                res.append(args)
        self.runTest(Test, 'test_foo_1_7')
        self.assertEqual([(1, 7)], res)
        self.runTest(Test, 'test_foo_2_3')
        self.assertEqual([(1, 7), (2, 3)], res)

    def test_list_of_multiple_arg_parameters_as_single_arg(self):
        res = []
        @parameterizable
        class Test(unittest.TestCase):
            @parameters(((1, 7), (2, 3)))
            def test_foo(self, *args):
                res.append(args)
        self.runTest(Test, 'test_foo_1_7')
        self.assertEqual([(1, 7)], res)
        self.runTest(Test, 'test_foo_2_3')
        self.assertEqual([(1, 7), (2, 3)], res)

    def test_dict_of_dict_parameters(self):
        res = []
        @parameterizable
        class Test(unittest.TestCase):
            @parameters(foo=dict(a=1, b=2), bar=dict(b=7))
            def test_foo(self, a=None, b=None):
                res.append((a, b))
        self.runTest(Test, 'test_foo_foo')
        self.assertEqual([(1, 2)], res)
        self.runTest(Test, 'test_foo_bar')
        self.assertEqual([(1, 2), (None, 7)], res)

    def test_dict_of_dict_parameters_as_single_arg(self):
        res = []
        @parameterizable
        class Test(unittest.TestCase):
            @parameters(dict(foo=dict(a=1, b=2), bar=dict(b=7)))
            def test_foo(self, a=None, b=None):
                res.append((a, b))
        self.runTest(Test, 'test_foo_foo')
        self.assertEqual([(1, 2)], res)
        self.runTest(Test, 'test_foo_bar')
        self.assertEqual([(1, 2), (None, 7)], res)

    def test_dict_of_single_arg_parameters(self):
        res = []
        @parameterize
        class Test(unittest.TestCase):
            @parameters(a=1, b=2)
            def test_bar(self, arg):
                res.append(arg)
        self.runTest(Test, 'test_bar_a')
        self.assertEqual([1], res)
        self.runTest(Test, 'test_bar_b')
        self.assertEqual([1, 2], res)

    def test_dict_of_multiple_arg_parameters(self):
        res = []
        @parameterize
        class Test(unittest.TestCase):
            @parameters(a=(1, 7), b=(2, 8))
            def test_bar(self, *args):
                res.append(args)
        self.runTest(Test, 'test_bar_a')
        self.assertEqual([(1, 7)], res)
        self.runTest(Test, 'test_bar_b')
        self.assertEqual([(1, 7), (2, 8)], res)

    def test__include_key(self):
        res = []
        @parameterize
        class Test(unittest.TestCase):
            @parameters(a=(1, 7), b=(2, 8), _include_key=True)
            def test_bar(self, *args):
                res.append(args)
        self.runTest(Test, 'test_bar_a')
        self.assertEqual([('a', 1, 7)], res)
        self.runTest(Test, 'test_bar_b')
        self.assertEqual([('a', 1, 7), ('b', 2, 8)], res)

    def test_mixed_lists_and_dicts(self):
        res = []
        @parameterize
        class Test(unittest.TestCase):
            @parameters(a=(1,), b=dict(z=1, k=3))
            def test_bar(self, z, k=None):
                res.append((z, k))
        self.runTest(Test, 'test_bar_a')
        self.assertEqual([(1, None)], res)
        self.runTest(Test, 'test_bar_b')
        self.assertEqual([(1, None), (1, 3)], res)

    def test_dict_parameters_invalid_if_not_named(self):
        with self.assertRaises(ValueError):
            @parameterizable
            class Test(unittest.TestCase):
                @parameters(dict(a=1, b=2), dict(b=7))
                def test_foo(self, a, b):
                    pass

    def test_invalid_setting_raises(self):
        with self.assertRaises(TypeError):
            @parameterize
            class Test(unittest.TestCase):
                @parameters(a=1, b=2, _nosuch_setting=True)
                def test_bar(self, *args):
                    pass


class TestLegacyAPI(unittest.TestCase):

    # Python2 compat
    if (not hasattr(unittest.TestCase, 'assertRaisesRegex')
            and  hasattr(unittest.TestCase, 'assertRaisesRegexp')):
        assertRaisesRegex = unittest.TestCase.assertRaisesRegexp

    def runTest(self, testcase, testname):
        res = testcase(methodName=testname).run()
        self.assertEqual(1, res.testsRun)
        self.assertEqual([], res.failures)
        self.assertEqual([], res.errors)
        self.assertTrue(res.wasSuccessful())

    def test_normal_tests_run(self):
        res = []
        @parameterize
        class Test(unittest.TestCase):
            def test_normal_tests_run(self):
                res.append(1)
            foo_params = [1, 2]
            def foo_as_bar(self, arg):
                raise Exception("This should not be run in this test")
        self.runTest(Test, 'test_normal_tests_run')
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
        self.runTest(Test, 'test_bar_1')
        self.assertEqual([1], res)
        self.runTest(Test, 'test_bar_2')
        self.assertEqual([1, 2], res)

    def test_names_generated_via_str(self):
        res = []
        @parameterize
        class Test(unittest.TestCase):
            foo_params = [0x30, 13.70]
            def foo_as_bar(self, arg):
                res.append(arg)
        self.runTest(Test, 'test_bar_48')
        self.assertEqual([48], res)
        self.runTest(Test, 'test_bar_13.7')
        self.assertEqual([48, 13.7], res)

    def test_multipart_test_names_generated_automatically(self):
        res = []
        @parameterize
        class Test(unittest.TestCase):
            foo_params = [(1, 7), (2, 8)]
            def foo_as_bar(self, arg1, arg2):
                res.append((arg1, arg2))
        self.runTest(Test, 'test_bar_1_7')
        self.assertEqual([(1, 7)], res)
        self.runTest(Test, 'test_bar_2_8')
        self.assertEqual([(1, 7), (2, 8)], res)

    def test_multiple_test_names_generated_from_dict_keys(self):
        res = []
        @parameterize
        class Test(unittest.TestCase):
            foo_params = dict(a=(1,), b=(2,))
            def foo_as_bar(self, arg):
                res.append(arg)
        self.runTest(Test, 'test_bar_a')
        self.assertEqual([1], res)
        self.runTest(Test, 'test_bar_b')
        self.assertEqual([1, 2], res)

if __name__=='__main__':
    unittest.main()
