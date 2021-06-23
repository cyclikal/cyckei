"""Abstract Classes for implementing plugins for Cyckei.
"""
import logging
import os.path


class BaseController(object):
    """Abstract Parent class of plugin controller objects.

    Creates default methods for interacting with plugin and handling sources.

    Attributes:
        description (str): The description given to the user in the info section.
        logger (logging.Logger): The logger for the plugin object. Stored in the Plugins folder, named after the name variable.
        name (str): The name of the plugin object.
    """

    def __init__(self, name, description):
        """Inits description, logger, and name. Sets up logging and sources for plugin.
        
        Args:
            name (str): The name of the plugin object.
            description (str): The description given to the user in the info section.
        """
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
        """Connects the plugin to main Cyckei loggers.

        Plugin initially tries to connect to to Cyckei's main logging handlers.
        If this fails, this method establishes a new console handler.
        Usually this should be as a result of running the plugin independantly.

        Args:
            name (str): The name of the plugin object.
            cyckei_plugin_path (str): The path to the Plugins folder in the Cyckei folder.

        Raises:
            FileNotFoundError: Raised when the path given by cyckei_plugin_path doesn't exist.

        Returns:
            logging.Logger: The logger for the plugin object. File stored in the Plugins folder, named after the name variable.
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

    def load_sources(self):
        """Abstract method. Searches for available sources, and establishes source objects.

        Raises:
            NotImplementedError: Error always raised as this is an abstract method.
        """
        raise NotImplementedError

    def read(self, source):
        """Reads data from every source object connected to this plugin controller. 

        Requires a collection of source objects to be stored in self.sources as a list or dictionary.

        Args:
            source (int or str): The index or key of the source object to be read from. Depends on whether the source
                objects are stored in a list or dict.

        Returns:
            Any: Any type can be returned as this function calls the read function from a source and does no further processing.
        """
        try:
            return self.sources[source].read()
        except (TypeError, KeyError) as error:
            # Occurs when there is no source at that address
            self.logger.error(f"Could not find plugin source: {error}")
        except Exception as error:
            self.logger.error("Exception occured while reading plugin:", error)

    def cleanup(self):
        """Abstract method.

        Raises:
            NotImplementedError: Error always raised as this is an abstract method.
        """
        raise NotImplementedError


class BaseSource(object):
    """Parent class of plugin source object. Controls communication with individual devices or channels.
    """

    def __init__(self):
        """Abstract constructor. No definition
        """
        pass

    def read(self):
        """Abstract method. Reads data from the source instrument.

        Raises:
            NotImplementedError: Error always raised as this is an abstract method.
        """
        raise NotImplementedError


def read_all(controller):
    """Performs the read function on every plugin source stored in the the plugin controller.

    Args:
        controller (BaseController): A BaseController holding plugin sources to be read from.

    Returns:
        dict: A dict with keys as the name of the plugin and values that could be any type.
        Any type could be returned from reading a plugin source, as there is no type control before this point.
    """
    values = {}
    for name in controller.sources:
        values[name] = controller.read(name)
    return values
