import logging

logger = logging.getLogger('cyckei')


class TemperatureRecorder(object):
    def __init__(self):
        logger.info("Initializing Temperature Recorder plugin")

    def read(self):
        logger.debug("Reading temperature.")

    def write(self):
        logger.debug("Logging temperature.")
