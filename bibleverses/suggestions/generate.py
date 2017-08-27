from .constants import MIN_SUGGESTIONS, MAX_SUGGESTIONS
from .utils.text import split_into_sentences, split_into_words_for_suggestions
from .utils.numbers import scale_suggestions, merge_suggestions


def generate_suggestions_for_text(text, strategies):
    item_suggestions = []

    # We are actually treating beginning of verse as beginning of sentence,
    # which is not ideal, but hard to fix, and usually it's not too bad,
    # because verse breaks are usually 'close' to being sentence breaks.

    sentences = split_into_sentences(text)
    for sentence in sentences:
        words = split_into_words_for_suggestions(sentence)
        for i, word in enumerate(words):
            relevance = 1.0
            word_suggestions = []
            for strategy in strategies:
                if strategy.use_for_word(i):
                    need = MIN_SUGGESTIONS - len(word_suggestions)  # Only random strategies really uses this
                    new_suggestions = [(w, f) for (w, f) in
                                       strategy.get_suggestions(words, i, need, word_suggestions)
                                       if w != word]
                    new_suggestions = scale_suggestions(new_suggestions, relevance)
                    if len(new_suggestions) > 0:
                        word_suggestions = merge_suggestions(word_suggestions, new_suggestions)
                        relevance = relevance / 2.0  # scale down worse methods for finding suggestions

                # Sort after each one:
                word_suggestions.sort(key=lambda w_f: -w_f[1])

            item_suggestions.append([w for w, f in word_suggestions[0:MAX_SUGGESTIONS]])
    return item_suggestions
