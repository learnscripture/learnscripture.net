from __future__ import absolute_import

from django.utils import unittest

from accounts.memorymodel import strength_estimate

class StrengthEstimate(unittest.TestCase):

    def test_strength_estimate_repeat(self):
        # If we test N times after interval I at a certain score, it should return the same
        # as if we test at the end of a single N*I interval


        def repeat(func, init, times):
            val = init
            for i in range(0, times):
                val = func(val)
            return val

        score = 0.8
        init = 0.5
        one_day = 24 * 3600
        after_one_week = strength_estimate(init, score, 7 * one_day)

        after_seven_daily_tests = repeat(lambda val: strength_estimate(val, score, one_day),
                                         init, 7)

        self.assertTrue(abs(after_seven_daily_tests - after_one_week) < 0.00001)


    def test_strength_estimate_null_previous(self):
        self.assertEqual(strength_estimate(None, 1.0, None), 0.5)
