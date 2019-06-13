import logging

from pkg_resources import require, DistributionNotFound, resource_filename
from json import load
from os.path import expanduser, exists
from os import makedirs
from shutil import copy

from cyckei.server import server


def main():
    """
        This is the main entrypoint and routine of Cyckei Vayu.
        Vayu aims to make cyckei more efficient in many aspects.
    """
    print("\n")

    try:
        version = require("cyckei")[0].version
    except DistributionNotFound:
        version = "(unpackaged)"

    print("Welcome to Cyckei Server version {}.".format(version))

    # Setup recording direcory if unavailable
    print("Checking for recording directory...")
    record_dir = expanduser("~") + "/cyckei"
    file_structure(record_dir)

    # Load configuration
    print("Loading configuration...")
    config = load(open(record_dir + "/config.json", "r"))
    config["path"] = record_dir

    # Start logging
    log_file = "{}/server.log".format(record_dir)
    print("Starting log...")
    logging.basicConfig(filename=log_file, level=config["verbosity"],
                        format='%(asctime)s %(message)s')
    logging.info("--- Server started.")

    # Start server
    server.main(config)


def file_structure(path):
    """Checks for existing folder structure and sets up if missing"""

    if not exists(path):
        makedirs(path)
    if not exists(path + "/tests"):
        makedirs(path + "/tests")
    if not exists(path + "/config.json"):
        copy(resource_filename("cyckei.server", "res/default.config.json"),
             path + "/config.json")
    if not exists(path + "/batch.txt"):
        copy(resource_filename("cyckei.server", "res/batch.txt"),
             path + "/batch.txt")
    if not exists(path + "/scripts"):
        makedirs(path + "/scripts")
        copy(resource_filename("cyckei.server", "res/example-script"),
             path + "/scripts/example")


if __name__ == "__main__":
    main()