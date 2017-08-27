from bibleverses.models import TextType, TextVersion
from bibleverses.services import partial_data_available

from .analyzers.firstwordfrequencies import FirstWordFrequencyAnalyzer
from .analyzers.markov import Markov1Analyzer, Markov2Analyzer, Markov3Analyzer
from .analyzers.thesaurus import ThesaurusAnalyzer
from .analyzers.wordcounts import WordCountsAnalyzer
from .constants import BIBLE_BOOK_GROUPS
from .storage import AnalysisStorage
from .trainingtexts import BibleTrainingTexts, CatechismTrainingTexts

ANALYZERS = [
    FirstWordFrequencyAnalyzer,
    WordCountsAnalyzer,
    ThesaurusAnalyzer,
    Markov1Analyzer,
    Markov2Analyzer,
    Markov3Analyzer,
]


def analyze_all():
    texts = TextVersion.objects.all()
    storage = AnalysisStorage()
    for text in texts:
        if partial_data_available(text.slug):
            continue
        run_all_analyses_for_text(storage, text)


def run_all_analyses_for_text(storage, text):
    if text.text_type == TextType.BIBLE:
        for g in BIBLE_BOOK_GROUPS:
            training_texts = BibleTrainingTexts(text=text, books=g)
            run_analyzers(storage, training_texts, training_texts.keys())

    elif text.text_type == TextType.CATECHISM:
        training_texts = CatechismTrainingTexts(text=text)
        run_analyzers(storage, training_texts, training_texts.keys())


def run_analyzers(storage, training_texts, keys):
    for A in ANALYZERS:
        a = A(storage)
        a.run(training_texts, keys)
