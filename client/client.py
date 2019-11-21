"""Main window for the cyckei client."""

import logging
import functools
import sys

from PySide2.QtWidgets import QMainWindow, QTabWidget, QHBoxLayout, QVBoxLayout
from PySide2.QtCore import QThreadPool

from .channel_tab import ChannelTab
from . import workers
# from .scripts import ScriptList
import functions.gui as func

logger = logging.getLogger('cyckei')

def handle_exception(exc_type, exc_value, exc_traceback):
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
sys.excepthook = handle_exception

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
