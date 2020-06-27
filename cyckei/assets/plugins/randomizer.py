import logging
from random import randint
from os.path import basename, join
import json

logger = logging.getLogger('cyckei')

DEFAULT_CONFIG = {
    "name":  basename(__file__)[:-3],
    "description": "Generates random numbers to demonstrate functionality.",
    "requirements": [],
    "sources": [
        {
            "readable": "Randomizer I",
            "port": "1",
            "range": [1, 10]
        },
        {
            "readable": "Randomizer II",
            "port": "2",
            "range": [11, 20]
        }
    ],
}


class DataController(object):
    def __init__(self, path):
        logger.info("Initializing Random Recorder plugin")

        self.name = DEFAULT_CONFIG["name"]
        with open(join(path, "plugins",
                       f"{self.name}.json")) as file:
            self.config = json.load(file)

    def match_source_attributes(self, source):
        for source_attribute in self.config["sources"]:
            if source_attribute["readable"] == source:
                return source_attribute
        logger.critical("Could not match plugin source.")

    def read(self, source):
        attr = self.match_source_attributes(source)
        logger.debug("Generating random integer...")
        return randint(attr["range"][0], attr["range"][1])
