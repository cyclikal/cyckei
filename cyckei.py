import sys
import json
import os
import shutil
import logging
import traceback
import threading

import zmq
from PySide2.QtWidgets import QApplication
from PySide2.QtGui import QIcon

from server import server
from client import client
from applet import applet
import functions as func


def main(record_dir="Cyckei"):
    """
    Begins execution of Cyckei.

    Args:
        record_dir: Optional path to recording directory.
    Returns:
        Result of app.exec_(), Qt's main event loop.

    """
    try:
        # Ensure Recording Directory is Setup
        record_dir = os.path.join(os.path.expanduser("~"), record_dir)
        file_structure(record_dir)

        # Setup Configuration
        with open(record_dir + "/config.json") as file:
            config = json.load(file)
        with open(func.find_path("assets/variables.json")) as file:
            var = json.load(file)
        config["version"] = var["version"]
        config["record_dir"] = record_dir

        # Setup Logging
        logging.basicConfig(filename="{}/cyckei.log".format(record_dir),
                            level=config["verbosity"],
                            format="%(asctime)s \t %(message)s")
        sys.excepthook = handler
    except Exception as e:
        print("An error occured before logging began.")
        print(e)

    logging.info("cyckei.main: Initializing Cyckei version {}".format(
        config["version"]))
    logging.debug("cyckei.main: Logging at debug level")

    # Create QApplication
    logging.debug("cyckei.main: Creating QApplication")
    app = QApplication(sys.argv)
    app.setStyle("fusion")
    app.setQuitOnLastWindowClosed(False)
    app.setWindowIcon(QIcon(func.find_path("assets/cyckei.png")))

    # Create Server's ZMQ Socket
    logging.debug("cyckei.server.server.main: Binding socket")
    try:
        context = zmq.Context(1)
        socket = context.socket(zmq.REP)
        socket.bind("{}:{}".format(config["zmq"]["server-address"],
                                   config["zmq"]["port"]))
    except zmq.error.ZMQError as error:
        logging.critical(
            "It appears the server is already running: ".format(error))
        msg = [
            "Cyckei Instance Already Running!",
            "To show client, open taskbar widget and click \"Launch Client\"",
            func.Critical,
            "Failed to initialize socket. "
            "This indicates an existing server insance. "
            "Error: {}".format(error)
        ]
        func.message(*msg)
        return
    logging.debug("cyckei.server.server.main: Socket bound successfully")

    # Start Server
    logging.debug("cyckei.main: Starting Server")
    server_thread = threading.Thread(target=server.main,
                                     args=(config, socket,),
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
    print("Starting Cyckei...")
    sys.exit(main())
