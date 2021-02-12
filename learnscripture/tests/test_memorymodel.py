import json
import os.path
import unittest

from accounts.memorymodel import MM, strength_estimate


class StrengthEstimate(unittest.TestCase):

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
        self.assertEqual(strength_estimate(0, 1.0, None), MM.INITIAL_STRENGTH_FACTOR)

    def test_outputs(self):
        # Here we test against known good values. The main purpose here is to be
        # able to sync the Python version of the code with the Elm version -
        # both are checked against the same JSON file.
        data = json.load(open(os.path.join(os.path.dirname(__file__), "memorymodel_test_data.json")))['strengthEstimateTestData']
        for vals in data:
            with self.subTest(vals=vals):
                self.assertEqual(vals[3], strength_estimate(vals[0], vals[1], vals[2]))
