import logging

from threading import Thread
from pkg_resources import resource_filename
from json import load
from os.path import expanduser, exists
from os import makedirs
from shutil import copy

from . import server
from . import applet


def main():
    """
        This is the main entrypoint and routine of Cyckei Vayu.
        Vayu aims to make cyckei more efficient in many aspects.
    """
    print("Sarting Server.")

    # Setup recording direcory if unavailable
    record_dir = expanduser("~") + "/cyckei"
    file_structure(record_dir)

    # Load configuration
    config = load(open(record_dir + "/config.json", "r"))
    config["path"] = record_dir

    # Start logging
    log_file = "{}/server.log".format(record_dir)
    logging.basicConfig(filename=log_file, level=config["verbosity"],
                        format='%(asctime)s %(message)s')
    logging.info("--- Server started.")

    server_thread = Thread(target=server.main, args=(config,), daemon=True)
    server_thread.start()

    return applet.main()


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
