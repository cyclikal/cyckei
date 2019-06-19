from sys import exit

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QApplication, QAction,\
    QMenu, QSystemTrayIcon
from pkg_resources import resource_filename


def main():
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    app.setStyle("fusion")

    # Create the tray
    tray = QSystemTrayIcon()
    tray.setIcon(QIcon(resource_filename(
            "cyckei.server",
            "res/bolt.png")))
    tray.setVisible(True)

    # Create the menu
    menu = QMenu()
    controls = []

    controls.append(QAction("Status"))
    controls[-1].triggered.connect(status)

    controls.append(QAction("Log"))
    controls[-1].triggered.connect(log)

    controls.append(QAction("About"))
    controls[-1].triggered.connect(about)

    controls.append(QAction("Stop Server"))
    controls[-1].triggered.connect(stop)

    for action in controls:
        menu.addAction(action)

    # Add the menu to the tray
    tray.setContextMenu(menu)

    app.exec_()


def status():
    pass


def log():
    pass


def about():
    pass


def stop():
    exit()
