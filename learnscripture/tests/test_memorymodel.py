from __future__ import absolute_import

import unittest2

from accounts.memorymodel import strength_estimate


class StrengthEstimate(unittest2.TestCase):

    def test_strength_estimate_repeat(self):
        # If we test N times after interval I at a certain score, it should
        # return better than if we test at the end of a single N*I interval

        def repeat(func, init, times):
            val = init
            for i in range(0, times):
                val = func(val)
            return val

        score = 1.0
        init = 0.5
        two_days = 24 * 3600 * 2
        after_one_test = strength_estimate(init, score, 7 * two_days)

        after_seven_tests = repeat(lambda val: strength_estimate(val, score, two_days),
                                   init, 7)

        self.assertTrue((after_seven_tests - after_one_test) > 0.0001)

    def test_strength_estimate_null_previous(self):
        self.assertEqual(strength_estimate(None, 1.0, None), 0.1)
