"""Main window for the cyckei client."""

import logging
import sys
import json
import os
import shutil

from PySide2.QtWidgets import QApplication, QMainWindow
from PySide2.QtCore import QThreadPool
from PySide2.QtGui import QIcon

from channel_tab import ChannelTab
import workers
import functions as func

logger = logging.getLogger('cyckei')
logger.setLevel(logging.DEBUG)  # base level must be lower than all handlers


def handle_exception(exc_type, exc_value, exc_traceback):
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value,
                 exc_traceback))


sys.excepthook = handle_exception


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
        # Create handlers
        c_handler = logging.StreamHandler()
        f_handler = logging.FileHandler("{}/{}.log".format(record_dir,
                                                           logger.name))
        c_handler.setLevel(logging.INFO)
        f_handler.setLevel(config["verbosity"])

        # Create formatters and add it to handlers
        # c_format = logging.Formatter("%(name)s - %(levelname)s \
        #                               - %(message)s")
        f_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s \
                                      - %(threadName)s - %(message)s")
        c_handler.setFormatter(f_format)
        f_handler.setFormatter(f_format)

        # Add handlers to the logger
        logger.addHandler(c_handler)
        logger.addHandler(f_handler)

    except Exception as e:
        print("An error occured before logging began.")
        print(e)

    logger.info("cyckei.main: Initializing Cyckei version {}".format(
        config["version"]))
    logger.debug("cyckei.main: Logging at debug level")

    # Create QApplication
    logger.debug("cyckei.main: Creating QApplication")
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(func.find_path("assets/cyckei.png")))

    # Create Client
    logger.debug("cyckei.main: Creating Initial Client")
    main_window = MainWindow(config)
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


# def handler(exception_type, value, tb):
#     """Handler which writes exceptions to log and terminal"""
#     exception_list = traceback.format_exception(exception_type, value, tb)
#     text = "".join(str(l) for l in exception_list)
#     logger.exception(text)
#     print(text)


class MainWindow(QMainWindow):
    """Main Window class which is and sets up itself"""
    # Setup main windows
    def __init__(self, config):
        super(MainWindow, self).__init__()
        # Set basic window properties
        self.setWindowTitle("Cyckei Client")
        self.config = config
        self.resize(1100, 600)

        resource = {}
        # Setup ThreadPool
        resource["threadpool"] = QThreadPool()
        self.threadpool = resource["threadpool"]
        logger.info("Multithreading set with maximum {} threads".format(
            resource["threadpool"].maxThreadCount()
        ))

        # # Load scripts
        # resource["scripts"] = ScriptList(config)

        # Create menu and status bar
        self.create_menu()
        self.status_bar = self.statusBar()

        # Create ChannelTab
        self.channelView = ChannelTab(config, resource, self)
        self.channels = self.channelView.channels
        self.setCentralWidget(self.channelView)

    def create_menu(self):
        """Setup menu bar"""

        entries = {
            "Server": [
                ["&Ping", self.ping_server, "Test Connection to Server"]
            ],
        }

        for key, items in entries.items():
            menu = self.menuBar().addMenu(key)
            for item in items:
                menu.addAction(func.action(*item, parent=self))

    def ping_server(self):
        worker = workers.Ping(self.config)
        worker.signals.alert.connect(func.message)
        self.threadpool.start(worker)


if __name__ == "__main__":
    print("Starting Cyckei...")
    sys.exit(main())
