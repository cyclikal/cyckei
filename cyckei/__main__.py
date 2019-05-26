import sys
import pkg_resources

from json import load
from os.path import expanduser, exists
from os import makedirs
from shutil import copy


def main(args=None):
    """
        This is the main entrypoint and routine of Cyckei Vayu.
        Vayu aims to make cyckei more efficient in many aspects.
    """
    if args is None:
        args = sys.argv[1:]

    version = pkg_resources.require("cyckei")[0].version

    print("Welcome to Cyckei Vayu version {}".format(version))

    # Do argument parsing here (eg. with argparse) and anything else.

    # Setup recording direcory if unavailable
    record_dir = expanduser("~") + "/cyckei"
    file_structure(record_dir)

    # load configuration
    config = load(open(record_dir + "/config.json", "r"))
    config["path"] = record_dir


def file_structure(path):
    """Checks for existing folder structure and sets up if missing"""
    print("Checking for or creating files at \"{}\"...".format(path), end="")

    if not exists(path):
        makedirs(path)
    if not exists(path + "/logs"):
        makedirs(path + "/logs")
    if not exists(path + "/tests"):
        makedirs(path + "/tests")
    if not exists(path + "/config.json"):
        copy("resources/default.config.json", path + "/config.json")
    if not exists(path + "/batch.txt"):
        copy("resources/batch.txt", path + "/batch.txt")
    if not exists(path + "/scripts"):
        makedirs(path + "/scripts")
        copy("resources/example-script", path + "/scripts/example")

    print("Done!")


if __name__ == "__main__":
    main()
