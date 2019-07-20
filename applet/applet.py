import sys
import logging

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QMenu, QSystemTrayIcon

from client import client
import functions as func


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
            "icon": func.Icon().Warning,
            "confirm": True
        }

        if func.message(**msg):
            logging.warning("applet.applet.Icon.stop: Shutting down\n")
            sys.exit()
