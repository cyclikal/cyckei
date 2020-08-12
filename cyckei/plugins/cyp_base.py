import logging
import os.path


class BaseController(object):
    """
    Parent class of plugin controller objects.
    Creates default methods for interacting with plugin and handling sources.
    """

    def __init__(self, name, description):
        """Setup logging and sources for plugin."""
        # Check if "cyckei" logger found, and setup seperate handler if not.

        if type(name) is not str or type(description) is not str:
            raise TypeError("Name and description must be passed as string")
        self.name = name
        self.description = description

        cyckei_plugin_path = os.path.join(os.path.expanduser("~"),
                                          "Cyckei", "Plugins")
        if not os.path.exists(cyckei_plugin_path):
            raise FileNotFoundError(
                "could not find cyckei recording directory")

        self.logger = self.get_logger(self.name, cyckei_plugin_path)

    def get_logger(self, name, cyckei_plugin_path):
        """
        Plugin initially tries to connect to to Cyckei's main loggin handlers.
        If this fails, this method establishes a new console handler.
        Usually this should be as a result of running the plugin independantly.
        """
        cyckei_plugin_path = os.path.join(os.path.expanduser("~"),
                                          "Cyckei", "Plugins")
        if not os.path.exists(cyckei_plugin_path):
            raise FileNotFoundError(
                "Could not find Cyckei recording directory.")

        log_path = os.path.join(cyckei_plugin_path, f"{name}.log")

        # Create logger and set base level
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        # Setting individual handlers and logging levels
        c_handler = logging.StreamHandler()
        f_handler = logging.FileHandler(log_path)

        c_handler.setLevel(logging.DEBUG)
        f_handler.setLevel(logging.WARNING)

        # Add handlers to the logger
        logger.addHandler(c_handler)
        logger.addHandler(f_handler)

        return logger

    def get_sources(self):
        """
        Searches for available sources, and establishes source objects.

        Returns
        -------
        Dictionary of sources in format "name": SourceObject.
        """

        raise NotImplementedError

    def read(self, source):
        try:
            return self.sources[source].read()
        except (TypeError, KeyError) as error:
            # Occurs when there is no source at that address
            self.logger.error(f"Could not find plugin source: {error}")
        except Exception as error:
            self.logger.error("Exception occured while reading plugin:", error)

    def cleanup(self):
        raise NotImplementedError


class BaseSource(object):
    """
    Parent class of plugin source object.
    Controls communication with individual devices or channels.
    """
    def __init__(self):
        pass

    def read(self):
        raise NotImplementedError


def read_all(controller):
    values = {}
    for name in controller.sources:
        values[name] = controller.read(name)
    return values
