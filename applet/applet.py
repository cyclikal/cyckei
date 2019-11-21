import logging
import sys

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QMenu, QSystemTrayIcon

import functions.gui as func
from client import client

logger = logging.getLogger('cyckei')

def handle_exception(exc_type, exc_value, exc_traceback):
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
sys.excepthook = handle_exception

class Icon(QSystemTrayIcon):
    def __init__(self, config):
        """Create tray applet and self.controls"""
        # TODO: Make icon visible on all backgrounds
        super(Icon, self).__init__(QIcon(func.find_path("assets/bolt.png")))

        self.config = config
        self.menu = QMenu()
        self.controls = []
        self.windows = []

        actions = [
            {"text": "Cyckei {}".format(config["version"]), "disabled": True},
            {"separator": True},
            {"text": "Launch Client", "connect": self.launch},
            {"text": "Quit Cyckei", "connect": self.stop},
        ]

        for action in actions:
            self.controls.append(func.action(**action))
            self.menu.addAction(self.controls[-1])

        # Add the self.menu to the tray
        self.setContextMenu(self.menu)

    def launch(self):
        self.windows.append(client.MainWindow(self.config))
        self.windows[-1].show()

    def stop(self):
        msg = {
            "text": "Are you sure you want to quit Cyckei?",
            "info": "This will stop any current cycles and "
                    "release control of all channels.",
            "icon": func.Warning,
            "confirm": True
        }

        if func.message(**msg):
            logger.warning("applet.applet.Icon.stop: Shutting down\n")
            sys.exit()
