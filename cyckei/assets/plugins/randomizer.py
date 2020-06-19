import logging
from random import randint
from os.path import basename

logger = logging.getLogger('cyckei')

DEFAULT_CONFIG = {
    "name":  basename(__file__)[:-3],
    "description": "Default Cyckei plugin to demonstrate functionality. Generates random numbers.",
    "requirements": {},
    "sources": [
        {
            "readable": "Randomizer I",
            "port": "1",
            "range": [1, 10],
        },
        {
            "readable": "Randomizer II",
            "port": "2",
            "range": [11, 20],
        },
    ],
}

class DataController(object):
    def __init__(self):
        self.name = CONFIG["name"]
        logger.info("Initializing Random Recorder plugin")

    def read(self):
        logger.debug("Generating random integer...")
        return randint(1, 100)
