"""This file is for execution as an installed package via 'cyckei'."""
import argparse
from os import makedirs, listdir
import os.path
from importlib.util import spec_from_file_location, module_from_spec
import sys
import traceback
import shutil
import logging
from logging.handlers import RotatingFileHandler
import json
import configparser
from datetime import datetime

from cyckei.functions import func

logger = logging.getLogger('cyckei')


def main(args=None):
    """
    Parses command-line arguments for component and directory.
    Checks for and, if necessary, creates file structure at given directory.
    Compiles configuration from config and variable files.
    Starts logging to both console and file based on argument input.
    Launches requested cyckei component (server, client, or explorer).
    """
    try:
        if args is None:
            args = parse_args()
            args.dir = os.path.join(os.path.expanduser("~"), "Cyckei")
        file_structure(args.dir, args.x)
        config = make_config(args)
        # config, plugins = load_plugins(config, args.x, args.launch, args.dir)
        plugins = []
        start_logging(config)
        print("Done!\n")
        logger.debug(f"Using configuration: {config}")

    except Exception as error:
        print("error occured before logging began")
        print(error)
        traceback.print_exc()
        sys.exit()

    logger.info(f"Launching {config['Arguments']['component']} with record "
                f"directory '{config['Arguments']['record_dir']}'")

    if args.launch == "server":
        from cyckei.server import server
        server.main(config, [plugins])
    elif args.launch == "client":
        from cyckei.client import client
        client.main(config)
    elif args.launch == "explorer":
        from cyckei.explorer import explorer
        explorer.main(config)


def parse_args():
    """
    Creates and parses command line arguments

    Returns:
        ArgumentParser with filled arguments.
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
                        default=30, type=int,
                        help='Set log file logging level.')

    return parser.parse_args()


def file_structure(path, overwrite):
    """
    Checks for existing folder structure and sets up if missing

    Args:
        config: Primary configuration dictionary
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
        configs = []
        for file in listdir(os.path.join(path, "plugins")):
            if file.endswith(".json"):
                configs.append(file)
        files = listdir(func.asset_path("plugins"))
        for plugin in files:
            plugin = os.path.join(func.asset_path("plugins"), plugin)
            if os.path.isfile(plugin):
                shutil.copy(plugin, os.path.join(path, "plugins"))


def make_config(args):
    """
    Loads configuration and variables from respective files.
    Merges them and adds command line arguments for universal access.

    Args:
        args: All processed command line arguments.

    Returns:
        Completed 'config' dictionary.
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
    config["Arguments"] = {}
    config["Arguments"]["record_dir"] = args.dir
    config["Arguments"]["component"] = args.launch
    config["Arguments"]["verbose"] = args.v
    config["Arguments"]["log_level"] = args.log_level

    return config


def load_plugins(config, overwrite, launch, path):
    # create individual plugin configurations, if necessary
    print("Loading plugins:", end="")
    for plugin in config["plugins"]:
        print(f" {plugin},", end="")
    print("\b...", end="")

    plugins = []
    # Load plugin modules
    for plugin in config["plugins"]:
        plugin_file = os.path.join(config["Arguments"]["record_dir"],
                                   "plugins", f"{plugin}.py")
        if os.path.isfile(plugin_file):
            spec = spec_from_file_location(f"plugin.{plugin}", plugin_file)
            plugin_module = module_from_spec(spec)
            spec.loader.exec_module(plugin_module)
            plugins.append(plugin_module)

    # Rewrite individual configuration and load sources into config for client
    config["plugins"] = []
    for plugin in plugins:
        config_file = os.path.join(
            config["Arguments"]["record_dir"], "plugins",
            f"{plugin.DEFAULT_CONFIG['name']}.json")
        if not os.path.exists(config_file) or overwrite:
            with open(config_file, "w") as file:
                json.dump(plugin.DEFAULT_CONFIG, file)

        with open(config_file) as file:
            plugin_config = json.load(file)
        config["plugins"].append({
            "name": plugin_config["name"],
            "description": plugin_config["description"],
            "sources": []
        })
        for source in plugin_config["channels"]:
            config["plugins"][-1]["sources"].append(source["readable"])

    # Cycle each plugin module up into its own object
    if launch == "server":
        for i, module in enumerate(plugins):
            plugins[i] = module.DataController(path)

    return config, plugins


def start_logging(config):
    """
    Creates handlers and starts logging.
    Logs to both file (f_handler) and console (c_console).

    Args:
        config: Primary configuration dictionary
    """
    print("Starting logging: ", end="")

    # Base level must be lower than all handlers
    logger.setLevel(logging.DEBUG)
    sys.excepthook = handle_exception

    # Setting individual handlers and logging levels
    date_format = datetime.now().strftime('%m-%d_%H-%M-%S')
    c_handler = logging.StreamHandler()
    f_handler = RotatingFileHandler(
        os.path.join(config["Arguments"]["record_dir"], "logs",
                     f"{logger.name}-{date_format}.log"),
        maxBytes=100000000,
        backupCount=5)

    if config["Arguments"]["verbose"]:
        c_handler.setLevel(logging.DEBUG)
    else:
        c_handler.setLevel(logging.INFO)
    f_handler.setLevel(config["Arguments"]["log_level"])

    print(f"C:{c_handler.level}, F:{f_handler.level}...", end="")

    # Format individual loggers
    formatter = ColorFormatter()
    c_handler.setFormatter(formatter)
    f_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)


def handle_exception(exc_type, exc_value, exc_traceback):
    """Exception Handler (referenced in start_logging)"""
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value,
                 exc_traceback))


class ColorFormatter(logging.Formatter):
    """Logging Formatter to add colors and count warning / errors"""

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
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


if __name__ == "__main__":
    main()
