import logging
from random import randint

logger = logging.getLogger('cyckei')


class DataController(object):
    def __init__(self):
        self.name = "temperature"
        logger.info("Initializing Temperature Recorder plugin")

    def read(self):
        logger.debug("Reading temperature...")
        return randint(1, 101)

    def write(self):
        logger.debug("Logging temperature.")
