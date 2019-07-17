# from subprocess import Popen, DEVNULL
import sys
import json
import os
import shutil
import logging
import traceback
import threading

from PySide2.QtWidgets import QApplication
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QSystemTrayIcon

from server import server
from client import client
from applet.applet import Applet

VERSION = "0.2.dev2"


def main():
    # Ensure Recording Directory is Setup
    record_dir = os.path.expanduser("~") + "/cyckei"
    file_structure(record_dir)

    # Setup Configuration
    config = json.load(open(record_dir + "/config.json", "r"))
    config["version"] = VERSION
    config["record_dir"] = record_dir

    # Setup Logging
    logging.basicConfig(filename="{}/cyckei.log".format(record_dir),
                        level=config["verbosity"],
                        format="%(asctime)s \t %(message)s")
    sys.excepthook = handler
    logging.info("cyckei.main: Initializing Cyckei version {}".format(
        config["version"]))
    logging.debug("cyckei.main: Logging at debug level")

    # Create QApplication
    logging.debug("cyckei.main: Creating QApplication")
    app = QApplication(sys.argv)
    app.setStyle("fusion")
    app.setQuitOnLastWindowClosed(False)
    app.setWindowIcon(QIcon("resources/cyckei.png"))

    # Start Server
    logging.debug("cyckei.main: Starting Server")
    server_thread = threading.Thread(target=server.main, args=(config))
    server_thread.start()

    # Create Applet
    logging.debug("cyckei.main: Creating Applet")
    applet_object = Applet(config)
    applet_object.show()


    # Create Client
    logging.debug("cyckei.main: Creating Initial Client")

    sys.exit(app.exec_())


def file_structure(path):
    """Checks for existing folder structure and sets up if missing"""

    if not os.path.exists(path):
        os.makedirs(path)
    if not os.path.exists(path + "/tests"):
        os.makedirs(path + "/tests")
    if not os.path.exists(path + "/config.json"):
        shutil.copy("resources/default.config.json", path + "/config.json")
    if not os.path.exists(path + "/batch.txt"):
        shutil.copy("resources/batch.txt", path + "/batch.txt")
    if not os.path.exists(path + "/scripts"):
        os.makedirs(path + "/scripts")
        shutil.copy("resources/example-script", path + "/scripts/example")


def handler(type, value, tb):
    """Handler which writes exceptions to log and terminal"""
    text = traceback.format_exception(type, value, tb)
    logging.exception(text)
    print(text)


if __name__ == "__main__":
    main()
