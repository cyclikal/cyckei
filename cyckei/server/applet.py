import sys

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QApplication, QAction, QMenu, QSystemTrayIcon,\
    QMessageBox
from pkg_resources import require, DistributionNotFound, resource_filename


def main():
    app = QApplication(sys.argv)
    app.setStyle("fusion")

    # Create the tray
    tray = QSystemTrayIcon(QIcon(resource_filename("cyckei.server",
                                                   "res/bolt.png")))
    menu = QMenu()
    controls = []

    controls.append(QAction("Cyckei Server"))
    controls[-1].triggered.connect(about)
    menu.addAction(controls[-1])

    controls.append(QAction("Check Status"))
    controls[-1].triggered.connect(status)
    menu.addAction(controls[-1])

    menu.addSeparator()

    controls.append(QAction("Launch client"))
    controls[-1].triggered.connect(client)
    menu.addAction(controls[-1])

    controls.append(QAction("Stop Server"))
    controls[-1].triggered.connect(stop)
    menu.addAction(controls[-1])

    # Add the menu to the tray
    tray.setContextMenu(menu)
    tray.show()

    app.exec_()


def post_message(status):
    msg = QMessageBox()
    msg.setText(status)
    msg.exec_()


def about():
    try:
        version = require("cyckei")[0].version
    except DistributionNotFound:
        version = "(unpackaged)"

    text = ("Cyckei Server version {}\n\n"
            "Updates and source code can be found on "
            "GitLab at gitlab.com/cyclikal/cyckei."
            ).format(version)

    post_message(text)


def status():
    pass


def client():
    pass


def stop():
    sys.exit()
