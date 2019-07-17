import sys
import logging

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QAction, QMenu, QSystemTrayIcon, QMessageBox

from client import client
import functions as func


class Icon(QSystemTrayIcon):
    def __init__(self, config):
        """Create tray applet and self.controls"""
        super().__init__(QIcon(func.find_path("assets/bolt.png")))

        self.config = config
        self.menu = QMenu()
        self.controls = []
        self.windows = []

        self.controls.append(QAction("Cyckei {}".format(config["version"])))
        self.controls[-1].setDisabled(True)
        self.menu.addAction(self.controls[-1])

        self.menu.addSeparator()

        self.controls.append(QAction("Launch Client"))
        self.controls[-1].triggered.connect(self.launch)
        self.menu.addAction(self.controls[-1])

        self.controls.append(QAction("Quit Cyckei"))
        self.controls[-1].triggered.connect(self.stop)
        self.menu.addAction(self.controls[-1])

        # Add the self.menu to the tray
        self.setContextMenu(self.menu)

    def launch(self):
        self.windows.append(client.MainWindow(self.config))
        self.windows[-1].show()

    def stop(self):
        msg = ("Are you sure you want to quit Cyckei?\n\n"
               "This will stop any current cycles and "
               "release control of all channels.")
        confirmation = QMessageBox()
        confirmation.setText(msg)
        confirmation.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

        response = confirmation.exec_()

        if response == QMessageBox.Yes:
            logging.warning("applet.applet.Icon.stop: Shutting down\n")
            sys.exit()
