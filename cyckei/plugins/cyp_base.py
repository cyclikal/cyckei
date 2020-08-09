import logging
import os.path
import configparser


class PluginController(object):
    """
    Parent class of plugin controller objects.
    Creates default methods for interacting with plugin and handling sources.
    """

    def __init__(self, name, base_path):
        """Setup logging and sources for plugin."""
        # Check if "cyckei" logger found, and setup seperate handler if not.

        if type(name) is not str:
            raise TypeError("plugin name must be passed as string")

        cyckei_plugin_path = os.path.join(os.path.expanduser("~"),
                                          "Cyckei", "Plugins")
        if not os.path.exists(cyckei_plugin_path):
            raise FileNotFoundError(
                "could not find cyckei recording directory")

        self.logger = self.get_logger(name, cyckei_plugin_path)
        self.config = self.get_config(name, cyckei_plugin_path, base_path)

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

        c_handler.setLevel(logging.INFO)
        f_handler.setLevel(logging.WARNING)

        # Add handlers to the logger
        logger.addHandler(c_handler)
        logger.addHandler(f_handler)

        return logger

    def get_config(self, name, cyckei_plugin_path, plugin_base_path):
        config = configparser.ConfigParser()

        # Read default configuration from package
        default_config_path = os.path.join(plugin_base_path, "config.ini")
        if os.path.exists(default_config_path):
            config.read(os.path.join(plugin_base_path, "config.ini"))
        else:
            raise FileNotFoundError(
                "no default configuration included in plugin")
        self.logger.debug(f"read default config from {default_config_path}")

        # Read additional custom configuration from folder, if available
        custom_config_path = os.path.join(cyckei_plugin_path, f"{name}.ini")
        config.read(custom_config_path)
        self.logger.debug(f"read custom config from {custom_config_path}")

        # Write combined configuration back to folder
        with open(custom_config_path, 'w') as file:
            config.write(file, space_around_delimiters=True)
        self.logger.debug(f"wrote finalized config to {custom_config_path}")

        return config

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
        except (TypeError, KeyError) as e:
            # Occurs when there is no source at that address
            self.logger.error(f"Could not find plugin source: {e}")

    def cleanup(self):
        raise NotImplementedError


class SourceHandler(object):
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
