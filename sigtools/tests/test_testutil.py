import unittest

from sigtools.support import s
from sigtools.tests import util as tutil


class UtilTests(unittest.TestCase):
    def test_conv_first_posarg(self):
        self.assertEqual(s(''), tutil.conv_first_posarg(s('')))
        self.assertEqual(
            s('one, /, two, *three, four, **five'),
            tutil.conv_first_posarg(s('one, two, *three, four, **five')))

    def test_sigtester_success(self):
        @tutil.sigtester
        def tester(self):
            pass
        @tester
        class Tests(object):
            attr = ()
        Tests('test_attr').test_attr()

    def test_sigtester_failure(self):
        @tutil.sigtester
        def tester(self):
            self.fail()
        @tester
        class Tests(object):
            attr = ()
        self.assertRaises(AssertionError, Tests('test_attr').test_attr)

    def test_keep_attributes(self):
        @tutil.sigtester
        def tester(self):
            pass
        obj1 = object()
        obj2 = object()
        @tester
        class Tests(object):
            _underscore = obj1
            test_prefix = obj2
        self.assertTrue(Tests._underscore, obj1)
        self.assertTrue(Tests.test_prefix, obj2)

    def test_args(self):
        @tutil.sigtester
        def tester(self, a, b):
            self.assertEqual(a, b)
        @tester
        class Tests(object):
            success = 1, 1
            failure = 0, 1
        t = Tests('test_success')
        t.test_success()
        self.assertRaises(AssertionError, t.test_failure)

    def test_sigs_equal(self):
        @tutil.sigtester
        def tester(self, a, b):
            self.assertSigsEqual(a, b)
        @tester
        class Tests(object):
            success_1 = s('one'), s('one')
            success_2 = s('*, one'), s('*, one')
            failure_1 = s('one'), s('two')
            failure_2 = s('one'), s('*, one')
        t = Tests('test_success_1')
        t.test_success_1()
        t.test_success_2()
        self.assertRaises(AssertionError, t.test_failure_1)
        self.assertRaises(AssertionError, t.test_failure_2)

    def test_sigs_equal_conv_first(self):
        @tutil.sigtester
        def tester(self, a, b):
            self.assertSigsEqual(a, b, conv_first_posarg=True)
        @tester
        class Tests(object):
            success_1 = s('self, /, one'), s('self, one')
            success_2 = s('self, /, *, one'), s('self, *, one')
            failure_1 = s('self, /, one'), s('self, two')
            failure_2 = s('self, /, one'), s('self, *, one')
        t = Tests('test_success_1')
        t.test_success_1()
        t.test_success_2()
        self.assertRaises(AssertionError, t.test_failure_1)
        self.assertRaises(AssertionError, t.test_failure_2)

    def test_assertIs(self):
        @tutil.sigtester
        def tester(self, a, b):
            self.assertIs(a, b)
        @tester
        class Tests(object):
            success = ([],) * 2
            failure = [], []
        t = Tests('test_success')
        t.test_success()
        self.assertRaises(AssertionError, t.test_failure)
