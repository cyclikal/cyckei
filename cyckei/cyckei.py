"""This file is for execution as an installed package via 'cyckei'."""
import argparse
from os import makedirs, listdir
import os.path
import importlib
import sys
import traceback
import shutil
import logging
from logging.handlers import RotatingFileHandler
import json
import configparser
from datetime import datetime

from cyckei.functions import func

server_logger = logging.getLogger('cyckei_server')
client_logger = logging.getLogger('cyckei_client')

def main(args=None):
    """The entry point for the application that controls the execution of different program branches.

    Parses command-line arguments for component and directory.
    Checks for and, if necessary, creates file structure at given directory.
    Compiles configuration from config and variable files.
    Starts logging to both console and file based on argument input.
    Launches requested cyckei component (server, client, or explorer).
    
    |
    """
    try:
        if args is None:
            args = parse_args()
            args.dir = os.path.join(os.path.expanduser("~"), "Cyckei")
        if args.launch == "client":
            logger = client_logger
        else:
            logger = server_logger
        file_structure(args.dir, args.x)
        config = make_config(args, logger)
        start_logging(config, logger)
        print("Done!\n")

    except Exception as error:
        print("error occured before logging began")
        print(error)
        traceback.print_exc()
        sys.exit()

    logger.info(f"Launching {config['arguments']['component']} with record "
                f"directory '{config['arguments']['record_dir']}'")

    if args.launch == "server":
        from cyckei.server import server
        plugins, plugin_names = load_plugins(config)
        server.main(config, plugins, plugin_names)
    elif args.launch == "client":
        from cyckei.client import client
        client.main(config)
    elif args.launch == "explorer":
        from cyckei.explorer import explorer
        explorer.main(config)


def parse_args():
    """Creates and parses command line arguments

    Returns:
        ArgumentParser with filled arguments.
    |
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('launch', metavar="{server | client | explorer}",
                        choices=['server', 'client', 'explorer'],
                        type=str, help='Select which component to launch.')
    parser.add_argument('-v', action="store_true",
                        help='Toggle verbose console output.')
    parser.add_argument('-x', action="store_true",
                        help='Reset all configuration and plugins.')
    # The dir argument was removed since it would not pass values onto plugins
    # parser.add_argument('--dir', metavar="[dir]",
    #                     default=os.path.join(os.path.expanduser("~"),
    #                         "Cyckei"),
    #                     type=str, help='Recording directory.')
    parser.add_argument('--log_level', metavar="[log_level]",
                        default=20, type=int,
                        help='Set log file logging level.')

    return parser.parse_args()


def file_structure(path, overwrite):
    """Checks for existing folder structure and sets up if missing

    Args:
        config: Primary configuration dictionary
    |
    """
    print("Checking filestructure...", end="")

    makedirs(path, exist_ok=True)
    makedirs(os.path.join(path, "tests"), exist_ok=True)
    makedirs(os.path.join(path, "logs"), exist_ok=True)
    if not os.path.exists(os.path.join(path, "scripts")):
        makedirs(os.path.join(path, "scripts"), exist_ok=True)
        files = listdir(func.asset_path("scripts"))
        for script in files:
            script = os.path.join(func.asset_path("scripts"), script)
            if os.path.isfile(script):
                shutil.copy(script, os.path.join(path, "scripts"))
    if not os.path.exists(os.path.join(path, "plugins")) or overwrite:
        makedirs(os.path.join(path, "plugins"), exist_ok=True)


def make_config(args, logger):
    """Loads configuration and variables from respective files. Merges them and adds command line arguments for universal access.

    Args:
        args: All processed command line arguments.
        logger (Logger): The logger to log config creation to.

    Returns:
        dict: Completed 'config' dictionary.
    |
    """
    # Get packaged variables
    config = configparser.ConfigParser()
    config.read(func.asset_path("variables.ini"))

    # Check for configuration, read and create if necessary
    config_path = os.path.join(args.dir, "config.json")
    if not os.path.exists(config_path) or args.x:
        logger.warning(
            f"Creating configuration at {config_path}")
        try:
            shutil.copyfile(func.asset_path("config.json"), config_path)
        except IOError as error:
            logger.critical(
                f"Couldn't create required configuration at \
                    {config_path}")
            raise PermissionError(error)

    logger.info(f"Reading configuration from {config_path}")
    try:
        with open(config_path) as file:
            json_config = json.load(file)
    except OSError as error:
        logger.critical(f"Failed to access configuration at {config_path}")
        raise OSError(error)
    except json.decoder.JSONDecodeError as error:
        logger.critical(f"Failed to read configuration file: {error}")
        sys.exit()

    config = {**config, **json_config}
    config["arguments"] = {}
    config["arguments"]["record_dir"] = args.dir
    config["arguments"]["component"] = args.launch
    config["arguments"]["verbose"] = args.v
    config["arguments"]["log_level"] = args.log_level

    return config


def load_plugins(config):
    """Takes the plugins listed in the config dict and attempts to import and instantiate them.

    Args:
        config (dict): Primary configuration dictionary.

    Returns:
        (list, dict): The first value is a list of PluginControllers extending the BaseController object. The second value is a dict with a key of the plugin name and
            a value of the of the specific plugin instance's name.
    |
    """
    # create individual plugin configurations, if necessary
    server_logger.info("Loading plugins...")

    plugins = []
    plugin_names = {}
    # Load plugin modules
    for plugin in config["plugins"]:
        if plugin["enabled"]:
            try:
                server_logger.debug(f"Attempting to load {plugin['name']}")
                module = importlib.import_module(
                    f"{plugin['module']}.{plugin['module']}")
                plugins.append(module.PluginController(plugin["sources"]))
                plugin_names[plugins[-1].name] = (plugins[-1].names)
                print(plugins[-1].name)
                print(plugins[-1].names)
                server_logger.info(f"Loaded {plugin['module']} plugin for {plugin['name']}")
            except ModuleNotFoundError as error:
                server_logger.warning(
                    f"Could not load plugin {plugin['module']}: {error}")

    return plugins, plugin_names


def start_logging(config, logger):
    """Creates handlers and starts logging.

    Logs to both file (f_handler) and console (c_console).

    Args:
        config (dict): Primary configuration dictionary.
        logger (Logger): The logger to initialize.
    |
    """
    print("Starting logging: ", end="")

    # Base level must be lower than all handlers
    logger.setLevel(logging.DEBUG)
    sys.excepthook = handle_exception

    # Setting individual handlers and logging levels
    date_format = datetime.now().strftime('%m-%d_%H-%M-%S')
    c_handler = logging.StreamHandler()
    f_handler = RotatingFileHandler(
        os.path.join(config["arguments"]["record_dir"], "logs",
                     f"{logger.name}-{date_format}.log"),
        maxBytes=10000000,
        backupCount=10)

    if config["arguments"]["verbose"]:
        c_handler.setLevel(logging.DEBUG)
    else:
        c_handler.setLevel(logging.INFO)
    f_handler.setLevel(config["arguments"]["log_level"])

    print(f"C:{c_handler.level}, F:{f_handler.level}...", end="")

    # Format individual loggers
    formatter = ColorFormatter()
    c_handler.setFormatter(formatter)
    f_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)


def handle_exception(exc_type, exc_value, exc_traceback):
    """Exception Handler (referenced in start_logging)
    
    |
    """
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value,
                 exc_traceback))


class ColorFormatter(logging.Formatter):
    """Extends logging.Formatter. Formatter to add colors and count warning / errors. 
    
    Set as the formatter for loggers when they are initalized in start_logging().
    
    |
    """
    gray = "\x1b[38;21m"
    blue = "\x1b[34;21m"
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = ("%(asctime)s - %(levelname)s - %(filename)s.%(funcName)s:"
              "\t\t%(message)s")

    FORMATS = {
        logging.DEBUG: blue + format + reset,
        logging.INFO: gray + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        """Called by the logger this object is attached to to format records.

        Args:
            record (logging.LogRecord): The record to be formatted.

        Returns:
            str: The Formatter to be used by loggers.
        |
        """
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


if __name__ == "__main__":
    main()
