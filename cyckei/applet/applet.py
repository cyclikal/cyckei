import sys

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QAction, QMenu, QSystemTrayIcon, QMessageBox


class Applet(QSystemTrayIcon):
    def __init__(self, config):
        """Create tray applet and self.controls"""
        super().__init__(QIcon("resources/bolt.png"))

        self.menu = QMenu()
        self.controls = []

        self.controls.append(QAction("Cyckei {}".format(config["version"])))
        self.controls[-1].setDisabled(True)
        self.menu.addAction(self.controls[-1])

        self.menu.addSeparator()

        self.controls.append(QAction("Launch Client"))
        self.controls[-1].triggered.connect(self.client)
        self.menu.addAction(self.controls[-1])

        self.controls.append(QAction("Quit Cyckei"))
        self.controls[-1].triggered.connect(self.stop)
        self.menu.addAction(self.controls[-1])

        # Add the self.menu to the tray
        self.setContextMenu(self.menu)

    def client(self):
        pass

    def stop(self):
        msg = ("Are you sure you want to close Cyckei Server?\n\n"
               "This will stop any current cycles and "
               "release control of all channels.")
        confirmation = QMessageBox()
        confirmation.setText(msg)
        confirmation.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

        response = confirmation.exec_()

        if response == QMessageBox.Yes:
            sys.exit()
