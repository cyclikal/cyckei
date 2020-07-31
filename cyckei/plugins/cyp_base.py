import logging

logger = logging.getLogger("cyckei")


class PluginController(object):
    """
    Parent class of plugin controller objects.
    Creates default methods for interacting with plugin and handling sources.
    """

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

    def read(self, source=None):
        try:
            return self.sources[source].read()
        except (TypeError, KeyError) as e:
            # Occurs when there is no source at that address
            logger.error(f"Could not find plugin source: {e}")

    def cleanup(self):
        raise NotImplementedError


class SourceObject(object):
    """
    Parent class of plugin source object.
    Controls communication with individual devices or channels.
    """
    def __init__(self):
        pass

    def read(self):
        raise NotImplementedError


def read_all(controller):
    values = []
    for source in controller.sources:
        values.append(f"{source}: {controller.read(source)}")
    return values
