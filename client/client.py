"""Main window for the cyckei client."""

import logging
import sys

from PySide2.QtWidgets import QApplication, QMainWindow
from PySide2.QtCore import QThreadPool
from PySide2.QtGui import QIcon

from .channel_tab import ChannelTab
from . import workers
from functions import func, gui

logger = logging.getLogger('cyckei')


def main(config):
    """
    Begins execution of Cyckei.

    Args:
        record_dir: Optional path to recording directory.
    Returns:
        Result of app.exec_(), Qt's main event loop.

    """

    logger.info(f"cyckei.main: Initializing Cyckei Client {config['version']}")
    logger.debug("cyckei.main: Logging at debug level")

    # Create QApplication
    logger.debug("cyckei.main: Creating QApplication")
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(func.find_path("assets/cyckei.png")))
    app.setStyle("Fusion")

    # Create Client
    logger.debug("cyckei.main: Creating Initial Client")
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
                menu.addAction(gui.action(*item, parent=self))

    def ping_server(self):
        worker = workers.Ping(self.config)
        worker.signals.alert.connect(gui.message)
        self.threadpool.start(worker)
