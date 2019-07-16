import logging

import zmq
import traceback
import sys

from threading import Thread
from json import load
from os.path import expanduser, exists
from os import makedirs
from shutil import copy

from PySide2.QtCore import QThread

from . import server
from . import applet


def main():
    """
        This is the main entrypoint and routine of Cyckei Vayu.
        Vayu aims to make cyckei more efficient in many aspects.
    """
    print("Sarting Server.")

    try:
        from AppKit import NSBundle
        info = NSBundle.mainBundle().infoDictionary()
        info["LSBackgroundOnly"] = "1"
    except ModuleNotFoundError:
        pass

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
    sys.excepthook = handler
    logging.info("--- Server started.")

    try:
        socket = initialize_socket(config["zmq"]["port"],
                                   config["zmq"]["server"]["address"])
    except zmq.error.ZMQError as error:
        logging.critical(
            "It appears the server is already running: ".format(error))
        return

    server_thread = Thread(target=server.main,
                           args=(config, socket), daemon=True)
    server_thread.start()

    return applet.main()


def handler(type, value, tb):
    logging.exception(traceback.format_exception(type, value, tb))


def initialize_socket(port, address):
    """Initialize zmq socket"""
    context = zmq.Context(1)
    socket = context.socket(zmq.REP)
    socket.bind("{}:{}".format(address, port))
    return socket


def file_structure(path):
    """Checks for existing folder structure and sets up if missing"""

    if not exists(path):
        makedirs(path)
    if not exists(path + "/tests"):
        makedirs(path + "/tests")
    if not exists(path + "/config.json"):
        copy("server/res/default.config.json",
             path + "/config.json")
    if not exists(path + "/batch.txt"):
        copy("server/res/batch.txt", path + "/batch.txt")
    if not exists(path + "/scripts"):
        makedirs(path + "/scripts")
        copy("server/res/example-script", path + "/scripts/example")
