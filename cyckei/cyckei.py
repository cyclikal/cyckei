"""This file is for execution as an installed package via 'cyckei'."""
import argparse
from os import makedirs, listdir, remove
from os.path import expanduser, join, exists, isfile
from importlib.util import spec_from_file_location, module_from_spec
import sys
import shutil
import logging
import json

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
        file_structure(args.dir, args.x)
        config = make_config(args)
        config, plugins = load_plugins(config, args.x)
        start_logging(config)
        print("Done!\n")
        logger.debug(f"Using configuration: {config}")

    except Exception:
        print("Error occured before logging began.")
        raise Exception

    logger.info(f"Launching {config['component']} with record "
                f"directory '{config['record_dir']}'")

    if args.launch == "server":
        from cyckei.server import server
        server.main(config, plugins)
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
        Arguments.
    """
    default_path = join(expanduser("~"), "Cyckei")

    parser = argparse.ArgumentParser()
    parser.add_argument('launch', metavar="{server | client | explorer}",
                        choices=['server', 'client', 'explorer'],
                        type=str, help='Select which component to launch.')
    parser.add_argument('-v', action="store_true",
                        help='Toggle verbose console output.')
    parser.add_argument('-x', action="store_true",
                        help='Reset all configuration and plugins.')
    parser.add_argument('--dir', metavar="[dir]", default=default_path,
                        type=str, help='Recording directory.')
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
    makedirs(join(path, "tests"), exist_ok=True)
    if not exists(join(path, "config.json")) or overwrite:
        shutil.copy(func.asset_path("default_config.json"),
                    join(path, "config.json"))
    if not exists(join(path, "scripts")):
        makedirs(join(path, "scripts"), exist_ok=True)
        files = listdir(func.asset_path("scripts"))
        for script in files:
            script = join(func.asset_path("scripts"), script)
            if isfile(script):
                shutil.copy(script, join(path, "scripts"))
    if not exists(join(path, "plugins")) or overwrite:
        makedirs(join(path, "plugins"), exist_ok=True)
        configs = []
        for file in listdir(join(path, "plugins")):
            if file.endswith(".json"):
                configs.append(file)
        files = listdir(func.asset_path("plugins"))
        for plugin in files:
            plugin = join(func.asset_path("plugins"), plugin)
            if isfile(plugin):
                shutil.copy(plugin, join(path, "plugins"))


def make_config(args):
    """
    Loads configuration and variables from respective files.
    Merges them and adds command line arguments for universal access.

    Args:
        args: All processed command line arguments.

    Returns:
        Completed 'config' dictionary.
    """

    with open(join(args.dir, "config.json")) as file:
        configuration = json.load(file)
    with open(func.asset_path("variables.json")) as file:
        variables = json.load(file)

    config = {**configuration, **variables}
    config["record_dir"] = args.dir
    config["component"] = args.launch
    config["verbose"] = args.v
    config["log_level"] = args.log_level

    return config

def load_plugins(config, overwrite):
    # create individual plugin configurations, if necessary
    print("Loading plugins:", end="")
    for plugin in config["data-plugins"]:
        print(f" {plugin},", end="")
    print("\b...", end="")

    plugins = []
    # Load plugin modules
    for plugin in config["data-plugins"]:
        plugin_file = join(config["record_dir"], "plugins", f"{plugin}.py")
        if isfile(plugin_file):
            spec = spec_from_file_location(f"plugin.{plugin}", plugin_file)
            plugin_module = module_from_spec(spec)
            spec.loader.exec_module(plugin_module)
            plugins.append(plugin_module)

    # Rewrite individual configuration and load sources into config for client
    config["plugin_sources"] = []
    for plugin in plugins:
        config_file = join(config["record_dir"], "plugins",
                           f"{plugin.DEFAULT_CONFIG['name']}.json")
        if not exists(config_file) or overwrite:
            with open(config_file, "w") as file:
                json.dump(plugin.DEFAULT_CONFIG, file)

        with open(config_file) as file:
            plugin_config = json.load(file)
        config["plugin_sources"].append({
            "name": plugin_config["name"],
            "description": plugin_config["description"],
            "sources": []
        })
        for source in plugin_config["sources"]:
            config["plugin_sources"][-1]["sources"].append(source["readable"])

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
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler(
        join(config["record_dir"], f"{logger.name}.log"))

    if config["verbose"]:
        c_handler.setLevel(logging.DEBUG)
    else:
        c_handler.setLevel(logging.INFO)
    f_handler.setLevel(min(config["log_level"], config["verbosity"]))

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
