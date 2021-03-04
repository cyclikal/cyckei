"""Main window for the cyckei client."""

import logging
import sys

from PySide2.QtWidgets import QApplication, QMainWindow
from PySide2.QtCore import QThreadPool
from .channel_tab import ChannelTab
from . import workers
from cyckei.functions import gui
from .socket import Socket

logger = logging.getLogger('cyckei_client')


def main(config):
    """
    Begins execution of Cyckei.

    Args:
        record_dir: Optional path to recording directory.
    Returns:
        Result of app.exec_(), Qt's main event loop.

    """

    logger.info(f"Starting Cyckei Client {config['versioning']['version']}")

    # Create QApplication
    logger.debug("Creating QApplication")
    app = QApplication(sys.argv)
    gui.style(app, "icon-client.png", gui.orange)

    # Create Client
    logger.debug("Creating initial xlient window")
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

        # Obtain channel information
        logger.info("Connecting to server for channel information")
        self.channel_info = Socket(config).info_all_channels()
        if type(self.channel_info) is not dict:
            logger.error("Could not get any plugin info from server.")
            raise Exception("Incorrect server response")

        # Obtain plugin information
        logger.info("Connecting to server for plugin information")
        self.plugin_info = Socket(config).info_plugins()
        if type(self.plugin_info) is not list:
            logger.error("Could not get any plugin info from server.")
            raise Exception("Incorrect server response")

        # Create menu and status bar
        self.create_menu()
        self.status_bar = self.statusBar()

        # Create ChannelTab
        self.channelView = ChannelTab(config, resource, self, self.plugin_info, self.channel_info)
        self.channels = self.channelView.channels
        self.setCentralWidget(self.channelView)

    def create_menu(self):
        """Setup menu bar"""

        entries = {
            "Info": [
                ["&Server", self.ping_server, "Test Connection to Server"],
                ["&Plugins", self.plugin_dialog, "Check Loaded Plugins"]
            ]
        }

        for key, items in entries.items():
            menu = self.menuBar().addMenu(key)
            for item in items:
                menu.addAction(gui.action(*item, parent=self))

    def ping_server(self):
        worker = workers.Ping(self.config)
        worker.signals.alert.connect(gui.message)
        self.threadpool.start(worker)

    def plugin_dialog(self):
        if self.config["plugins"]:
            text = "<h2>Plugins:</h2>"
        else:
            text = "<h2>No Loaded Plugins</h2>"
        info = ""
        for plugin in self.plugin_info:
            info += f"<p><h3>{plugin['name']}</h3>"
            info += f"<i>{plugin['description']}</i><br>"
            info += f"Sources: {plugin['sources']}</p>"
        msg = {
            "text": text,
            "info": info,
        }
        gui.message(**msg)
