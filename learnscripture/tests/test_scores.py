from bibleverses.languages import LANGUAGES
from scores.models import Scores


def test_scores_set_for_languages():
    for lang in LANGUAGES:
        assert lang.code in Scores._LANGUAGE_POINTS_PER_WORD, f"{lang.code} needs _LANGUAGE_POINTS_PER_WORD defining"
