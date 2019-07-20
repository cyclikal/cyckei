import sys

from subprocess import Popen, DEVNULL

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QApplication, QAction, QMenu, QSystemTrayIcon,\
    QMessageBox
from pkg_resources import require, DistributionNotFound, resource_filename


def main():
    app = QApplication(sys.argv)
    app.setStyle("fusion")
    app.setQuitOnLastWindowClosed(False)

    # Create the tray
    tray = QSystemTrayIcon(QIcon(resource_filename("cyckei.server",
                                                   "res/bolt.png")))
    menu = QMenu()
    controls = []

    try:
        version = require("cyckei")[0].version
    except DistributionNotFound:
        version = "(unpackaged)"

    controls.append(QAction("Cyckei Server {}".format(version)))
    controls[-1].setDisabled(True)
    menu.addAction(controls[-1])

    menu.addSeparator()

    controls.append(QAction("Launch Client"))
    controls[-1].triggered.connect(client)
    menu.addAction(controls[-1])

    controls.append(QAction("Stop Server"))
    controls[-1].triggered.connect(stop)
    menu.addAction(controls[-1])

    # Add the menu to the tray
    tray.setContextMenu(menu)
    tray.show()

    app.exec_()


def post_message(text):
    msg = QMessageBox()
    msg.setText(text)
    msg.exec_()


def client():
    Popen(["cyckei-client"], stdout=DEVNULL)


def stop():
    msg = ("Are you sure you want to close Cyckei Server?\n\n"
           "This will stop any current cycles and "
           "release control of all channels.")
    confirmation = QMessageBox()
    confirmation.setText(msg)
    confirmation.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

    response = confirmation.exec_()

    if response == QMessageBox.Yes:
        sys.exit()
