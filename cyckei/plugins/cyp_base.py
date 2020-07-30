import logging

logger = logging.getLogger("cyckei")


class PluginController(object):
    def __init__(self):
        """Setup logging and sources for plugin."""

        # Check if "cyckei" logger found, and setup seperate handler if not.
        self.check_logger()
        self.sources = self.get_sources()

    def check_logger(self):
        """
        Plugin initially tries to connect to to Cyckei's main loggin handlers.
        If this fails, this method establishes a new console handler.
        Usually this should be as a result of running the plugin independantly.
        """

        if not logger.hasHandlers():
            c_handler = logging.StreamHandler()
            c_handler.setLevel(logging.DEBUG)
            logger.addHandler(c_handler)

    def get_sources(self):
        """
        Searches for available sources, and establishes source objects.

        Returns
        -------
        Dictionary of sources in format "name": SourceObject.
        """

        raise NotImplementedError

    def read(self, source):
        return self.sources[source]


class SourceObject(object):
    def __init__(self, port):
        pass

    def connect(self):
        raise NotImplementedError

    def ping(self):
        raise NotImplementedError

    def read(self):
        raise NotImplementedError


if __name__ == "__main__":
    controller = PluginController()
