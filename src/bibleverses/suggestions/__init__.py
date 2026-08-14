"""
Code for generating 'suggestions' for verses.
"""

# The 'on screen buttons' testing method works like this:

# For each word of the verse, a list of buttons is presented with different
# words, only one of which is correct, and the user must choose the right one.
#
# The problem is this method is generally too easy. We're showing the user the
# correct word, and in addition, many of the other words we might put there
# might not make sense in context, semantically or grammatically, and so would
# be obviously wrong.
#
# So, we need a method of selecting words that will be far more likely to fool
# the user. To do this, we currently use a bunch of different strategies, some
# of which rely on textual analysis of the relevant text (i.e. version of the
# Bible), such as Markov chains. Since this code was written there have been a
# lot of advances in NLP, and there are newer methods we could move to if we
# have the time and there would be clear benefits, see
# https://github.com/learnscripture/learnscripture.net/issues/200
#
# For performance reasons, including keeping memory usage low, we pre-compute
# as much as possible:
#
# 1. do textual analysis up front
# 2. for each word in each verse, come up with suggestions and save to the DB.

# Additionally, we anticipate the possibility that we may get access to some
# Bible versions only via an API, where we don't have the whole text. In this
# case, we can't do step 2 above, and we may want to have a service, perhaps
# implemented as a separate server process, that generates word suggestions on
# the fly. This is not implemented yet, but some of the structure of the code
# has that need in mind.

# So, the solution so far implemented:
#
# * We do analysis up front - see `.analyze` and `.analyzers.*`

# * Where we don't have the full text, we choose a default English Bible
#   (NET) and hope that is sufficiently like other versions to be appropriate
#   as a textual analysis basis.

# * We serialize the results of analyses to disk - see `.storage`

# * We create wrappers classes to the analysis results, that in some cases
#   reduce the size of the data we actually need in memory. see `.tools`

# * We have a `.generators` module that loads that completed analysis and
#   generates suggestions.
#
#   This module has as few dependencies as possible e.g. it doesn't
#   load Django at all.
#   This makes it easier to test for memory consumption.
#   In the future it may be possible to run this code as a standalone
#   server, e.g. a socket server, using PyPy for performance,
#   or rewrite to be faster and more lightweight using Cython etc.
#
# * For the main Django processes that need word suggestions,
#   we have a `.modelapi' module that handles everything transparently.
#
#   If necessary, it will handle talking to the socket server


# The solution above doesn't work well for all languages we support. In
# particular, for Turkish, Markov chains are far from adequate. Turkish is also
# hard since it tends to have fewer words per verse, making the word suggestion
# testing method even worse as an effective test. So for some languages we
# disable this testing method altogether.
