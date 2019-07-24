import sys
import json
import os
import shutil
import logging
import traceback
import threading

from PySide2.QtWidgets import QApplication
from PySide2.QtGui import QIcon

from server import server
from client import client
from applet import applet
import functions as func

VERSION = "0.2rc2"
ID = "com.cyclikal.cyckei"


def main(record_dir="/Cyckei"):
    """
    Begins execution of Cyckei.

    Args:
        record_dir: Optional path to recording directory.
    Returns:
        Result of app.exec_(), Qt's main event loop.

    """
    # Ensure Recording Directory is Setup
    record_dir = os.path.expanduser("~") + record_dir
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
    app.setWindowIcon(QIcon(func.find_path("assets/cyckei.png")))

    # Start Server
    logging.debug("cyckei.main: Starting Server")
    server_thread = threading.Thread(target=server.main,
                                     args=(config,),
                                     daemon=True)
    server_thread.start()

    # Create Applet
    logging.debug("cyckei.main: Creating Applet")
    applet_object = applet.Icon(config)
    applet_object.show()

    # Create Client
    logging.debug("cyckei.main: Creating Initial Client")
    main_window = client.MainWindow(config)
    main_window.show()

    return app.exec_()


def file_structure(path):
    """Checks for existing folder structure and sets up if missing"""
    os.makedirs(path, exist_ok=True)
    os.makedirs(path + "/tests", exist_ok=True)
    if not os.path.exists(path + "/config.json"):
        shutil.copy(func.find_path("assets/default_config.json"),
                    path + "/config.json")
    open(path + "/batch.txt", "a")
    if not os.path.exists(path + "/scripts"):
        os.makedirs(path + "/scripts")
        shutil.copy(func.find_path("assets/example-script"),
                    path + "/scripts/example")


def handler(type, value, tb):
    """Handler which writes exceptions to log and terminal"""
    list = traceback.format_exception(type, value, tb)
    text = "".join(str(l) for l in list)
    logging.exception(text)
    print(text)


if __name__ == "__main__":
    sys.exit(main())
