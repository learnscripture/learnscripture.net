from bibleverses.models import TextType, TextVersion
from bibleverses.services import partial_data_available
from bibleverses.suggestions.analyzers.base import Analyzer

from .analyzers.firstwordfrequencies import FirstWordFrequencyAnalyzer
from .analyzers.markov import Markov1Analyzer, Markov2Analyzer, Markov3Analyzer
from .analyzers.thesaurus import ThesaurusAnalyzer
from .analyzers.wordcounts import WordCountsAnalyzer
from .constants import get_bible_book_groups
from .storage import AnalysisStorage
from .trainingtexts import BibleTrainingTexts, CatechismTrainingTexts, TrainingTexts

ANALYZERS: list[type[Analyzer]] = [
    FirstWordFrequencyAnalyzer,
    WordCountsAnalyzer,
    ThesaurusAnalyzer,
    Markov1Analyzer,
    Markov2Analyzer,
    Markov3Analyzer,
]


def analyze_all(version_slugs=None, disallow_text_loading=False):
    if version_slugs == []:
        version_slugs = None
    texts = TextVersion.objects.all()
    if version_slugs is not None and len(version_slugs) > 0:
        texts = texts.filter(slug__in=version_slugs)
    storage = AnalysisStorage()
    for text in texts:
        if version_slugs is None and partial_data_available(text.slug):
            continue
        run_all_analyses_for_text(storage, text, disallow_text_loading=disallow_text_loading)


def run_all_analyses_for_text(storage: AnalysisStorage, text: TextVersion, disallow_text_loading=False):
    training_texts: TrainingTexts
    if text.text_type == TextType.BIBLE:
        for g in get_bible_book_groups(text.language_code):
            training_texts = BibleTrainingTexts(text_version=text, books=g, disallow_loading=disallow_text_loading)
            run_analyzers(storage, training_texts, training_texts.keys())

    elif text.text_type == TextType.CATECHISM:
        training_texts = CatechismTrainingTexts(text_version=text, disallow_loading=disallow_text_loading)
        run_analyzers(storage, training_texts, training_texts.keys())


def run_analyzers(storage: AnalysisStorage, training_texts: TrainingTexts, keys):
    for A in ANALYZERS:
        a = A(storage)
        a.run(training_texts, keys)
