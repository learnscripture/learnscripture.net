import logging

logger = logging.getLogger(__name__)


class Analyzer(object):
    name = NotImplemented

    def __init__(self, storage):
        self.storage = storage

    def run(self, training_texts, keys):
        """
        Runs the analysis (using the texts defined by the the passed in keys and
        training text), and saves the result to disk.
        """
        if not self.storage.saved_analysis_exists(self, keys):
            logger.info("Running analysis %s for keys %s",
                        self.__class__.__name__,
                        keys)
            data = self.analyze(training_texts, keys)
            self.storage.save_analysis(data, self, keys)
        else:
            logger.info("Skipping already created analysis %s for keys %s",
                        self.__class__.__name__,
                        keys)

    def analyze(self, training_texts, keys):
        """
        Perform analysis, and return an object suitable for saving to disk
        and for using by final strategies.
        """
        # This could be a simple as a dictionary
        raise NotImplementedError("{0} needs to implement 'analyze' method".format(self.__class__))
