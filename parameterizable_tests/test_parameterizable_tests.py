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


class TestLegacyAPI(unittest.TestCase):

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
