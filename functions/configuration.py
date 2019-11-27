import json
import logging
import os
import shutil
import sys

from . import find_path


def read_config(record_dir):
    # Ensure Recording Directory is Setup
    record_dir = os.path.join(os.path.expanduser("~"), record_dir)
    file_structure(record_dir)

    # Setup Configuration
    with open(record_dir + "/config.json") as file:
        config = json.load(file)
    with open(find_path("assets/variables.json")) as file:
        var = json.load(file)
    config["version"] = var["version"]
    config["record_dir"] = record_dir
    return config, record_dir


def file_structure(path):
    """Checks for existing folder structure and sets up if missing"""
    os.makedirs(path, exist_ok=True)
    os.makedirs(path + "/tests", exist_ok=True)
    if not os.path.exists(path + "/config.json"):
        shutil.copy(find_path("assets/default_config.json"),
                    path + "/config.json")
    open(path + "/batch.txt", "a")
    if not os.path.exists(path + "/scripts"):
        os.makedirs(path + "/scripts")
        shutil.copy(find_path("assets/example-script"),
                    path + "/scripts/example")


def setup_logging(logger_name, record_dir, config):
    # Setup Logging
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG) # base level must be lower than all handlers

    # Create handlers
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler("{}/{}.log".format(record_dir, logger.name))
    c_handler.setLevel(logging.INFO)
    f_handler.setLevel(config["verbosity"])

    # Create formatters and add it to handlers
    # c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(threadName)s - %(message)s')
    c_handler.setFormatter(f_format)
    f_handler.setFormatter(f_format)

    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)

    def handle_exception(exc_type, exc_value, exc_traceback):
        logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    sys.excepthook = handle_exception

    return logger
