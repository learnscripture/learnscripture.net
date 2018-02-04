# -*- coding: utf-8 -*-
import json
import math
import os.path
from datetime import timedelta


# The whole of this model is also reproduced in Elm code, to allow client side code
# to estimate when something is next due without a server round trip. All changes
# must be synced with that code


class MemoryModel(object):
    # == Memory model ==

    # We try to fit the progress of a memory to a idealised exponential curve:
    #
    # s = 1 - exp(-alpha × t^exponent)
    #
    # where 's' is the strength of the memory and 't' is the time elapsed in
    # seconds since first learning.

    # A strength of 1 is perfect, but we assume that a person never reaches this.
    # We attempt to move a memory along this curve by testing at ever increasing
    # intervals. This idea is taken from the Charlotte Mason Scripture Memory system.

    # We fix alpha and exponent by trial and error to give us:

    # 1) the right initial testing sequence (lots of times initially, preferably
    #    about a week where they are tested every day.
    # 2) a tail that remains for over a year, so it doesn't drop the memory too
    #    quickly.

    # We need s:

    def s(self, t):
        return 1 - math.exp(-self.ALPHA * t ** self.EXPONENT)

    # We will also need the inverse:

    def t(self, s):
        return (- math.log(1 - s) / self.ALPHA) ** (1.0 / self.EXPONENT)

    # These increasing intervals on the time axis can correspond to even size
    # intervals on the strength axis since we have an exponential as above.
    #
    # When a memory is tested, the score is evidence of the current strength of the
    # memory. However, the new recorded strength is not simply set to the test
    # score. If someone has recently been prompted, the information may simply be in
    # short term memory, and we are only interested in long term memory.  So we use
    # the test information to adjust the current recorded strength, not replace it.
    # A user is not allowed to beat the above curve.
    #
    # The idealised curve above represents the behaviour if the user scores 100% on
    # all tests. In this way, the memory will never stop being a candidate for
    # testing, even if the user aces the tests.
    #
    # At every point, we assume that the memory is following the curve above, so
    # for calculating intervals in 't', we don't look at the actual 't' since
    # they first began. Instead we only look at time intervals between the
    # current time and the last test, and assume the current time corresponds to
    # the current strength as per the curve. This keeps us robust against the
    # case where they started learning and then had a long gap, or forgot it
    # completely.
    #
    # If the user does much worse than 100%, all that happens is that they progress
    # along the 't' curve much more slowly than the model suggests, and they will
    # be tested more frequently as a result, which is the behaviour we want.
    #
    # For every memory, we attempt to test it after an ideal interval delta_t_ideal
    #
    # delta_t_ideal corresponds to an interval delta_s_ideal from the current
    # strength.  We aim to fit delta_s_ideal to a constant that will produce a fixed
    # number of tests to move the memory from strength zero to 'learnt'. In the
    # Charlotte Mason system, a verse is tested about 15 - 20 times before being
    # retired, so we aim for that (with a bit of tuning)

    VERSE_TESTS = 18

    # We want to avoid the number of verses needing testing increasing forever,
    # and so put a hard limit, after which a verse is considered 'learnt'.

    # We need a value that is attainable using reasonable test accuracy. Test
    # accuracy of 95 - 100% is achievable for most people, but scaling (see
    # below) means 95% accuracy goes to a strength of 0.9025, and we need to go
    # under that.
    #
    # With a value of 0.8, it is possible to move a verse fully learnt with
    # a test score of 90%, which should be achievable by all.
    #
    # Also, with a strength of just less than this, a verse will be due for
    # review in less than a year.
    LEARNT = 0.80

    # We want to reach this stage after 1 year on our idealised curve.

    # This will mean that if we learn X new verses every day,
    # there will be X*VERSE_TESTS verses to review each day.

    # Some maths below needs a limit to stop us getting logs of
    # negative numbers:
    BEST_STRENGTH = 0.999

    # For the initial test, we don't have a previous strength recorded. We
    # arbitrarily set the initial strength to be 0.1 test strength

    INITIAL_STRENGTH_FACTOR = 0.1  # This is also used in learn.js

    def __init__(self, EXPONENT):
        # We allow one of the two parameters to be tuned - pick EXPONENT
        self.EXPONENT = EXPONENT

        # ALPHA can be set using the above constants:

        # s  = 1 - exp(-alpha * t^n)
        # LEARNT = 1 - exp(-alpha * ONE_YEAR^n)
        ONE_YEAR = 365 * 24 * 3600 * 1.0

        # Rearranging:
        # ALPHA = - ln(1 - LEARNT) / (ONE_YEAR^n)
        self.ALPHA = - math.log(1.0 - self.LEARNT) / (ONE_YEAR ** EXPONENT)

        self.DELTA_S_IDEAL = (self.LEARNT - self.INITIAL_STRENGTH_FACTOR) / self.VERSE_TESTS

    # Given an old strength, a new test score, and the number of seconds elapsed,
    # we need to calculate the new strength estimate.

    def strength_estimate(self, old_strength, test_accuracy, time_elapsed):
        # We first have to convert between 'test accuracy' and some notion of
        # 'test strength'. It was found that achieving 100% is actually pretty
        # easy, and a score as high as 60% shows pretty low knowledge in reality
        # - contextual clues given on a word-by-word basis give a lot of help
        # and it is easy to guess. So we invent a somewhat arbitrary scale here
        # that has fixed points at zero and one, and reduces the score for
        # everything in between.

        test_strength = test_accuracy ** 2

        if time_elapsed is None:
            return self.INITIAL_STRENGTH_FACTOR * test_strength

        # If they have gone down from recorded strength, that is very strong
        # evidence of their new test_strength, so we simply return that value.
        if test_strength < old_strength:
            return test_strength

        if old_strength == 1.0:
            return self.BEST_STRENGTH

        # Otherwise, we do not allow the strength to increase more than
        # our formula allows.

        s1 = old_strength

        # We assume old strength was according to our formula
        t1 = self.t(s1)

        t2 = t1 + time_elapsed

        # If they got 100% in test, we would have this value of s:
        s2 = self.s(t2)

        # Giving:
        delta_s_max = s2 - s1

        # However, we have to adjust for the fact that test_strength may be < 1
        #
        # Long term, if test_strength hits a ceiling, then s should tend to
        # test_strength, and not to 1. This implies:
        #
        #   delta_s_actual == 0 for test_strength == old_strength
        #
        # We also need to fit:
        #
        #   delta_s_actual == delta_s_max for test_strength == 1.
        #
        # Linear interpolation between these two constraints gives:

        delta_s_actual = delta_s_max * (test_strength - old_strength) / (1.0 - old_strength)

        # Limit jumps to approx DELTA_S_IDEAL to avoid people progressing
        # too quickly if they are not doing tests.
        delta_s_actual = min(self.DELTA_S_IDEAL * 1.1, delta_s_actual)

        new_strength = old_strength + delta_s_actual

        return min(self.BEST_STRENGTH, new_strength)

    MIN_TIME_BETWEEN_TESTS = 3600

    # needs_testing and next_test_due contain almost equivalent information.
    # next_test_due is stored in UserVerseStatus.next_test_due, allowing easier
    # queries

    def needs_testing(self, strength, time_elapsed):
        if time_elapsed is None:
            return True
        if time_elapsed < self.MIN_TIME_BETWEEN_TESTS:
            # It is confusing to have a verse up for revision within an hour of
            # it being first learnt, so we special case that here.
            return False
        if strength > self.LEARNT:
            return False
        t_0 = self.t(strength)
        # clip at BEST_STRENGTH here to stop log of a negative
        t_1 = self.t(min(strength + self.DELTA_S_IDEAL, self.BEST_STRENGTH))
        return time_elapsed > t_1 - t_0

    def next_test_due_after(self, strength):
        """
        Returns the number of seconds to wait for the next test, for a given
        strength
        """
        t_0 = self.t(strength)
        t_1 = self.t(min(strength + self.DELTA_S_IDEAL, self.BEST_STRENGTH))
        return max(t_1 - t_0, self.MIN_TIME_BETWEEN_TESTS)


# test_run and test_run_using_next_test_due should be essentially identical.


def test_run(exponent, accuracy, interval_gap=1):
    m = MemoryModel(exponent)
    interval = 0
    x = 0
    day = 24 * 3600
    test = 0
    days_total = 0
    while days_total < 10 * 365:
        interval += interval_gap
        days_total += interval_gap
        time_elapsed = None if x == 0 else day * interval
        if m.needs_testing(x, time_elapsed):
            x = m.strength_estimate(x, accuracy, time_elapsed)
            test += 1
            print("Day %d, test %d, interval %d, strength %s" % (math.floor(days_total), test, interval, x))
            interval = 0


def test_run_using_next_test_due_after(exponent, accuracy, interval_gap=1):
    from datetime import datetime
    m = MemoryModel(exponent)
    interval = 0
    s = 0
    start = datetime.now()
    last_test = None
    next_test = None
    test = 0
    days_total = 0
    while days_total < 10 * 365:
        current_time = start + timedelta(days=days_total)
        interval += interval_gap
        days_total += interval_gap
        if next_test is None or (current_time > next_test and s < m.LEARNT):
            if last_test is None:
                time_elapsed = None
            else:
                time_elapsed = (current_time - last_test).total_seconds()
            s = m.strength_estimate(s, accuracy, time_elapsed)
            last_test = current_time
            next_test = last_test + timedelta(seconds=m.next_test_due_after(s))
            test += 1
            print("Day %d, test %d, interval %d, strength %s" % (days_total, test, interval, s))
            interval = 0


def test_run_passage(passage_length, days):
    # Test function for experimenting with methods of getting testing of verses
    # in a passage to converge to tests on the same day, instead of diverging in
    # testing schedule

    import random
    # We learn 1 verse a day in passage.
    learnt = {}
    verses_learnt = 0
    day = 24 * 3600
    accuracy = 0.95
    tests_for_verse = {}
    for i in range(0, days):
        if verses_learnt < passage_length:
            # Learn new:
            learnt[verses_learnt] = (i * day, MM.strength_estimate(0, accuracy, None))
            verses_learnt += 1

        need_testing = 0
        for j in range(0, verses_learnt):
            t, s = learnt[j]
            time_elapsed = i * day - t
            if MM.needs_testing(s, time_elapsed):
                need_testing += 1

        number_tested = 0
        if need_testing > 0 and verses_learnt == passage_length:
            # STRENGTH_FOR_GROUP_TESTING:
            # We want to do testing together.  The simplest way is just to do
            # testing if any verse requires testing. This doesn't actually result in
            # much more testing - it just means that some verses are tested before
            # their ideal time.

            # However, we don't want to do this immediately - only after 'a while'
            # of treating the verses more individually.

            # From user testing, a sensible period seems to be when 3 days after all
            # the verses have been learnt. This corresponds to a strength of 0.5.
            test_all = False
            min_strength = min(s for t, s in learnt.values())
            if min_strength > STRENGTH_FOR_GROUP_TESTING:
                test_all = True

            for j in range(0, verses_learnt):
                t, s = learnt[j]
                time_elapsed = i * day - t

                if test_all:
                    needs_testing = True
                else:
                    needs_testing = MM.needs_testing(s, time_elapsed)

                print("%02d: %6f %s" % (j + 1, s,
                                        "Test" if needs_testing else "No test"))

                if needs_testing:
                    acc = 0.95 + (random.random() / 20.0)
                    acc = min(acc, 1)
                    tests_for_verse[j] = tests_for_verse.setdefault(j, 0) + 1

                    # if min_strength is not None:
                    #     s = min_strength
                    # if min_time_elapsed is not None:
                    #     time_elapsed = min_time_elapsed

                    new_strength = MM.strength_estimate(s, acc, time_elapsed)
                    new_time_tested = i * day
                    learnt[j] = new_time_tested, new_strength
                    number_tested += 1
        if number_tested > 0:
            print()
            print("Day %d" % i)
            print("%02d/%02d" % (number_tested, passage_length))
    return sorted(tests_for_verse.items())


def generate_test_file():
    old_strengths = [x / 10.0 for x in range(0, 11)]
    test_accuracies = [x / 10.0 for x in range(0, 11)]
    time_elapsed = [None, 0, 100, 3600, 3600 * 10, 3600 * 24 * 10, 3600 * 24 * 100]

    output = []
    for s in old_strengths:
        for a in test_accuracies:
            for t in time_elapsed:
                output.append([s, a, t, strength_estimate(s, a, t)])

    with open(os.path.join(os.path.dirname(__file__),
                           "../learnscripture/tests/memorymodel_test_data.json"), "w") as fp:
        json.dump({'strengthEstimateTestData': output}, fp,
                  indent=4)


# Trial and error with test_run, with the aim of getting
# a verse tested at least 3 or 4 times in the first week
# after learning, and then a sensible sequence of intervals,
# prdocuces EXPONENT = 0.25.
# This was tried for accuracy = 1.0 and accuracy = 0.95, both
# giving sensible results

EXPONENT = 0.25
MM = MemoryModel(EXPONENT)
needs_testing = MM.needs_testing
strength_estimate = MM.strength_estimate
next_test_due_after = MM.next_test_due_after
LEARNT = MM.LEARNT
STRENGTH_FOR_GROUP_TESTING = 0.5
