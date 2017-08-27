"""
Code for generating 'suggestions' for verses.
"""

# The 'on screen buttons' testing method works like this:

# For each word of the verse, a list of buttons is presented with different
# words, only one of which is correct, and the user must choose the right one.
#
# Simple enough! The complication is in selecting words to be shown at each point.
# Random words are not good suggestions - most would make no sense in context,
# semantically or grammatically.
#
# Instead we do a whole bunch of different strategies, some of which rely on
# intensive textual analysis of the relevant text (i.e. version of the Bible),
# such as Markov chains. Clearly this can't be done on the fly.
#
# As much as possible, we precompute:
#
# - do textual analysis up front
# - for each word in each verse, come up with suggestions
#   and save to the DB.
#
# Things are further complicated by the fact that for some Bible versions
# we are not given the whole text. So, we can't do textual analysis of the
# text, nor apply the suggestion generation routines to each verse ahead of
# time.

# An additional issue is that some of the textual analysis methods normally use
# up a lot of memory, and even just the final data from analysis (e.g. a Markov
# chain) uses a lot of memory. We don't want to load this into each Django
# process that serves requests.

# So, the solution so far implemented:
#
# * We do analysis up front - see `.analyze` and `.analyzers.*`

# * Where we don't have the full text, we choose a default English Bible
#   (NET) and hope that is sufficiently like other versions to be appropriate
#   as a textual analysis basis.

# * We serialize the results of analyses to disk - see `.storage`

# * We create wrappers classes to the analysis results,
#   that in some cases reduce the size of the data
#   we actually need in memory.  see `.tools`

# * We run a standalone socket server process, see `.server`. This loads
#   the serialized analysis data, and is able to very quickly
#   generate suggestions for a chunk of text.
#
#   This server avoids as many dependencies as possible, in order to be light.
#
# * For the main Django processes that need word suggestions,
#   we have an `.api' module that handles everything transparently:
#
#   * Loading from disk if available
#   * Talking to the socket server to get more suggestions if necessary
