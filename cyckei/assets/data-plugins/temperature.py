import logging

logger = logging.getLogger('cyckei')


class DataPlugin(object):
    def __init__(self):
        self.name = "temperature"
        logger.info("Initializing Temperature Recorder plugin")

    def read(self):
        logger.debug("Reading temperature...")
        return 420

    def write(self):
        logger.debug("Logging temperature.")
