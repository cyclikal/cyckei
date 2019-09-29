"""Main window for the cyckei client."""

import logging
import functools

from PySide2.QtWidgets import QMainWindow, QTabWidget, QHBoxLayout
from PySide2.QtCore import QThreadPool

from .channel_tab import ChannelTab
from . import workers
from .scripts import ScriptList
import functions as func

logger = logging.getLogger('cyckei')

def handle_exception(exc_type, exc_value, exc_traceback):
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
sys.excepthook = handle_exception
def help():
    """Direct to help"""
    msg = "For help refer to the HELP.md and README.md files located in" \
          "the cyckei install location, or online on our GitLab page." \
          "\n\ngitlab.com/cyclikal/cyckei"
    func.message(msg)


def about(version):
    """Display basic information about cyckei"""
    msg = "Cyckei version {}\n\n" \
          "Cyckei is developed by Gabriel Ewig and Vincent Chevrier " \
          "at Cyclikal, LLC.\n\n Updates and source code can be found " \
          "on GitLab at gitlab.com/cyclikal/cyckei. \n\nFor information" \
          "about Cyclikal, visit cyclikal.com.".format(version)
    func.message(msg)


class MainWindow(QMainWindow):
    """Main Window class which is and sets up itself"""
    # Setup main windows
    def __init__(self, config):
        super(MainWindow, self).__init__()
        # Set basic window properties
        self.setWindowTitle("Cyckei Client")
        self.config = config
        self.resize(1100, 600)

        self.setStyleSheet(
            open(func.find_path("assets/style.css"), "r").read())

        resource = {}
        # Setup ThreadPool
        resource["threadpool"] = QThreadPool()
        self.threadpool = resource["threadpool"]
        logger.info("Multithreading set with maximum {} threads".format(
            resource["threadpool"].maxThreadCount()
        ))

        # Load scripts
        resource["scripts"] = ScriptList(config)

        # Create menu and status bar
        self.create_menu()
        self.status_bar = self.statusBar()

        # Create Tabs
        layout = QHBoxLayout()
        self.setLayout(layout)
        self.channelView = ChannelTab(config, resource, self)
        layout.addWidget(self.channelView)
        self.threadpool = resource["threadpool"]
        self.channels = self.channelView.channels

    def create_menu(self):
        """Setup menu bar"""

        entries = {
            "Client": [
                ["&Info", functools.partial(about, self.config["version"]),
                    "About Cyckei"],
                ["&Help", help, "Help Using Cyckei"]
            ],
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
