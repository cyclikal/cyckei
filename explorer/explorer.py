"""Main window for the cyckei client."""

import logging
import sys
import json
import os

from PySide2.QtWidgets import QApplication, QMainWindow
from PySide2.QtCore import QThreadPool
from PySide2.QtGui import QIcon

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
        func.file_structure(record_dir)

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

    logger.info("explorer.main: Initializing Explorer version {}".format(
        config["version"]))
    logger.debug("explorer.main: Logging at debug level")

    # Create QApplication
    logger.debug("explorer.main: Creating QApplication")
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(func.find_path("assets/explorer.png")))

    # Create Client
    logger.debug("explorer.main: Creating Window")
    main_window = MainWindow(config)
    main_window.show()

    return app.exec_()


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

    def create_menu(self):
        """Setup menu bar"""

        entries = {
            "File": [
                ["&About", self.about, "About Cyckei Explorer"]
            ],
        }

        for key, items in entries.items():
            menu = self.menuBar().addMenu(key)
            for item in items:
                menu.addAction(func.action(*item, parent=self))

    def about(self):
        func.message(f"About Cyckei Explorer v. {self.config['version']}")


if __name__ == "__main__":
    print("Starting Cyckei...")
    sys.exit(main())
