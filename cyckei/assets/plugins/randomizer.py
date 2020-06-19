import logging
from random import randint

logger = logging.getLogger('cyckei')


class DataController(object):
    def __init__(self):
        self.name = "randomizer"
        logger.info("Initializing Random Recorder plugin")

    def read(self):
        logger.debug("Generating random integer...")
        return randint(1, 101)
