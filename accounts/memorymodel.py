# -*- coding: utf-8 -*-
import math

### Memory model ###

# We try to fit the progress of a memory to a idealised exponential curve:
#
#
# s = 1 - exp(-alpha × t)

def s(t):
    return 1 - math.exp(-ALPHA * t)

# where 's' is the strength of the memory and t is the time elapsed,
# and alpha is a constant. We will also need the inverse:

def t(s):
    return - math.log(1 - s) / ALPHA

# A strength of 1 is perfect, but we assume that a person never reaches this.
# We attempt to move a memory along this curve by testing at ever increasing
# intervals. This idea is taken from the Charlotte Mason Scripture Memory system.
#
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
# At every point, we assume that the memory is following the curve above, so for
# calculating intervals in 't', we don't look at the actual 't' since they first
# began. Instead we only look at time intervals between the current time and the
# last test. This keeps us robust against the case where they started learning
# and then had a long gap, or forgot it completely.
#
# If the user does much worse than 100%, all that happens is that they progress
# along the 't' curve much more slowly than the model suggests, and they will
# be tested more frequently as a result, which is the behaviour we want.
#
# For every memory, we attempt to test it after an ideal interval delta_t_ideal
#
# delta_t_ideal corresponds to an interval delta_s_ideal from the current
# strength.  We aim to fit delta_s_ideal to a constant that will produce a fixed
# number of tests to move the memory from strength zero to 'one'. In the Charlotte
# Mason system, a verse is tested about 15 - 20 times, so we use this:

MAX_TESTS = 20

# For the initial test, we don't have a previous strength recorded. We
# arbitrarily set the initial strength to be 0.1 test strength

INITIAL_STRENGTH_FACTOR = 0.1

# Assuming the user scores 100% initially, we then want to fit in MAX_TESTS
# between this initial strength and the final of one. Each test should therefore
# come after:

DELTA_S_IDEAL = (1 - INITIAL_STRENGTH_FACTOR) / MAX_TESTS

# We now need a fixed point to calculate alpha

# In the Charlotte Mason system, the user is tested every day for a week.
# If we aim to get 7 tests in first week, the initial ones will be crammed
# together, and the user will miss them. Also, experimentally, we want
# a value of alpha that will still test the user after about a year.
# So we go for 7 tests in 14 days.

TP = 7 * 24 * 60 * 60
N = 7

# We have s_initial = INITIAL_STRENGTH_FACTOR:
s_initial = INITIAL_STRENGTH_FACTOR

# We need to fit: (s_later - s_initial) corresponds to N tests
# s_later - s_initial ==  N * DELTA_S_IDEAL

s_later = s_initial + N * DELTA_S_IDEAL

# Re-arranging s:
# ln(1 - s) = - alpha * t

# - alpha * t_initial  = ln (1 - s_initial)      [1]
# - alpha * t_later    = ln (1 - s_later)        [2]
#           t_later    = t_initial +  TP         [3]
#
# Eliminating t_later from [2] using [3]:
# - alpha * (t_initial + TP) = ln(1 - s_later)
#
# Rearrange [1] and eliminating t_initial:
#
#  - alpha( -1/alpha * ln(1 - s_initial) + TP) = ln(1 - s_later)
#  alpha = - ln(1 - s_later) / (-1/alpha * ln(1 - s1) + TP)
#
# giving an iterative method for finding alpha, which happens to converge fairly
# quickly:

def refine_alpha(alpha):
    return - math.log(1.0 - s_later) / (-1.0/alpha * math.log(1.0 - s_initial) + TP)

def repeat(func, init, times):
    val = init
    for i in range(0, times):
        val = func(val)
    return val

ALPHA = repeat(refine_alpha, 1, 50) # approx 7e-7

# (Feeding this value back into the formulae confirms it is correct).

# If we have a strength of 1 it will stop the memory from ever being tested, and
# break our maths below.
BEST_STRENGTH = 0.999999999999999

# Given an old strength, a new test score, and the number of seconds elapsed,
# we need to calculate the new strength estimate.

def strength_estimate(old_strength, test_strength, time_elapsed):
    if old_strength is None or time_elapsed is None:
        return INITIAL_STRENGTH_FACTOR * test_strength

    # If they have gone down from recorded strength, that is very strong
    # evidence of their new test_strength, so we simply return that value.
    if test_strength < old_strength:
        return test_strength

    if old_strength == 1.0:
        return BEST_STRENGTH


    # Otherwise, we do not allow the strength to increase more than
    # our formula allows. Another way of interpreting the following
    # calculation is that a test after a long gap is better evidence
    # of it having gone into memory than a test after a short gap.

    s1 = old_strength
    delta_t = time_elapsed

    # We assume old strength was accoding to our formula
    t1 = t(s1)

    t2 = t1 + time_elapsed

    # If they got 100% in test, we would have this value of s:
    s2 = s(t2)

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
    #   delta_s_actual == 1 for test_strength == 1.

    delta_s_actual = delta_s_max * (test_strength - old_strength) / (1.0 - old_strength)
    new_strength = old_strength + delta_s_actual

    return min(BEST_STRENGTH, new_strength)


def needs_testing(strength, time_elapsed):
    if time_elapsed is None or strength is None:
        return True
    # For the initial stages, DELTA_S_IDEAL works well.  For later stages,
    # however, the exponential behaviour works against us, and the memory falls
    # off a cliff and is dropped a bit too quickly.

    TOP_PHASE = 0.05
    if strength > (1.0 - TOP_PHASE):
        # Keep adjusting it so we don't hit the ceiling
        delta_s_ideal = DELTA_S_IDEAL * (1.0 - strength)/TOP_PHASE
    else:
        delta_s_ideal = DELTA_S_IDEAL

    t_0 = t(strength)
    t_1 = t(min(strength + delta_s_ideal, BEST_STRENGTH))
    if time_elapsed > t_1 - t_0:
        return True



def test_run():
    interval = 0
    x = None
    day = 24*3600
    test = 0
    for i in range(0, 200):
        interval += 1
        if needs_testing(x, day * interval):
            x = strength_estimate(x, 1.0, interval * day)
            test += 1
            print "Day %d, test %d, interval %d, strength %s" % (i, test, interval, x)
            interval = 0

