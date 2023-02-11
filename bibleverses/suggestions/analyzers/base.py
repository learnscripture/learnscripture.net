import logging

from bibleverses.suggestions.storage import AnalysisStorage
from bibleverses.suggestions.trainingtexts import TrainingTexts

logger = logging.getLogger(__name__)


class Analyzer:
    name: str = NotImplemented

    def __init__(self, storage):
        self.storage: AnalysisStorage = storage

    def run(self, training_texts: TrainingTexts, keys):
        """
        Runs the analysis (using the texts defined by the the passed in keys and
        training text), and saves the result to disk.
        """
        saved_file = self.storage.saved_analysis_file(self, keys)
        if not saved_file.exists():
            logger.info("Running analysis %s for keys %s", self.__class__.__name__, keys)
            data = self.analyze(training_texts, keys)
            self.storage.save_analysis(data, self, keys)
        else:
            logger.info(
                "Skipping already created analysis %s for keys %s, path %s",
                self.__class__.__name__,
                keys,
                saved_file,
            )

    def analyze(self, training_texts: TrainingTexts, keys):
        """
        Perform analysis, and return an object suitable for saving to disk
        and for using by final strategies.
        """
        # This could be a simple as a dictionary
        raise NotImplementedError(f"{self.__class__} needs to implement 'analyze' method")
