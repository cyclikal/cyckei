"""Main window for the cyckei client."""

import logging
import sys

from pkg_resources import require, DistributionNotFound
from PySide2.QtWidgets import QWidget, QMainWindow, QAction, QTabWidget,\
    QMessageBox
from PySide2.QtGui import QIcon
from PySide2.QtCore import QThreadPool

from cyckei.client.channel_tab import ChannelTab
from cyckei.client.script_tab import ScriptEditor
from cyckei.client.log_tab import LogViewer
import workers
from scripts import Scripts


def help():
    """Direct to help"""
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Information)
    msg.setText(
        """For help refer to the HELP.md and README.md files located in
the cyckei install location, or online on our GitLab page.
\n\ngitlab.com/cyclikal/cyckei"""
    )
    msg.setWindowTitle("Help")
    msg.exec_()


def about():
    """Display basic information about cyckei"""
    try:
        version = require("cyckei")[0].version
    except DistributionNotFound:
        version = "(unpackaged)"

    print("Welcome to Cyckei Vayu version {}.".format(version))
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Information)
    msg.setText(
        """Cyckei version {}\n\n
Cyckei is developed by Gabriel Ewig and Vincent Chevrier at Cyclikal, LLC.\n\n
Updates and source code can be found on GitLab at gitlab.com/cyclikal/cyckei.
\n\nFor information about Cyclikal, visit cyclikal.com.""".format(version)
    )
    msg.setWindowTitle("About")
    msg.exec_()


class MainWindow(QMainWindow):
    """Main Window class which is and sets up itself"""
    # Setup main windows
    def __init__(self, config):
        super().__init__()
        # Set basic window properties
        self.setWindowTitle("Cyckei")
        self.config = config
        self.resize(1100, 600)

        # Setup ThreadPool
        self.threadpool = QThreadPool()
        logging.info("Multithreading set with maximum {} threads".format(
            self.threadpool.maxThreadCount()
        ))

        # Load scripts
        scripts = Scripts()
        scripts.load_default_scripts(config["path"] + "/scripts")

        # Create menu and status bar
        self.menu_bar = self.create_menu()
        self.status_bar = self.statusBar()

        self.tab_widget = QTabWidget(self)
        self.setCentralWidget(self.tab_widget)

        self.tab_widget.addTab(
            ChannelTab(self.config, self.threadpool, scripts),
            "Channels"
        )
        self.channels = self.tab_widget.widget(0).channels
        self.tab_widget.addTab(
            ScriptEditor(self.channels, scripts),
            "Scripts"
        )
        self.tab_widget.addTab(LogViewer(self.config), "Logs")

        self.setStyleSheet(open("resources/style.css", "r").read())

    def create_menu(self):
        """Setup menu bar"""
        menu_options = []

        menu_options.append(QAction("&About", self))
        menu_options[-1].setStatusTip("About Cyckei")
        menu_options[-1].triggered.connect(about)

        menu_options.append(QAction("&Help", self))
        menu_options[-1].setStatusTip("View Help File")
        menu_options[-1].triggered.connect(help)

        menu_options.append(QAction("&Exit", self))
        menu_options[-1].setStatusTip("Exit Client Application")
        menu_options[-1].triggered.connect(self.exit_client)

        menu_options.append(QAction("&Ping", self))
        menu_options[-1].setStatusTip("Ping Server for Response")
        menu_options[-1].triggered.connect(self.ping_server)

        menu_options.append(QAction("&Save", self))
        menu_options[-1].setStatusTip("Save Batch of IDs and Log Files")
        menu_options[-1].triggered.connect(self.save_batch)

        menu_options.append(QAction("&Load", self))
        menu_options[-1].setStatusTip("Load Batch of IDs and Log Files")
        menu_options[-1].triggered.connect(self.load_batch)

        menu_options.append(QAction("&Fill All", self))
        menu_options[-1].setStatusTip("Auto Fill All Log Files in Batch")
        menu_options[-1].triggered.connect(self.fill_batch)

        menu_options.append(QAction("&Increment", self))
        menu_options[-1].setStatusTip("Increment Batch")
        menu_options[-1].triggered.connect(self.increment_batch)

        menu_bar = self.menuBar()
        menu_bar.setNativeMenuBar(False)

        menu = menu_bar.addMenu("&Menu")
        menu.addAction(menu_options[0])
        menu.addAction(menu_options[1])
        menu.addAction(menu_options[2])

        server = menu_bar.addMenu("&Server")
        server.addAction(menu_options[3])

        batch = menu_bar.addMenu("&Batch")
        batch.addAction(menu_options[4])
        batch.addAction(menu_options[5])
        batch.addAction(menu_options[6])
        batch.addAction(menu_options[7])

        return menu_bar

    def exit_client(self):
        sys.exit()

    def ping_server(self):
        worker = workers.Ping()
        worker.signals.alert.connect(self.post_message)
        self.threadpool.start(worker)

    def post_message(self, status):
        msg = QMessageBox()
        msg.setText(status)
        msg.exec_()

    def save_batch(self):
        """Saves id and log information to file"""
        reply = QMessageBox.question(
            QWidget(),
            "Batch",
            "Save batch?\nCurrent saved batch will be deleted.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            batch = []
            for channel_widget in self.channels:
                channel = [channel_widget.attributes["id"],
                           channel_widget.attributes["path"]]
                batch.append(channel)

            with open(self.config["path"] + "/batch.txt", "a") as file:
                file.truncate(0)
                for channel in batch:
                    for value in channel:
                        file.write(str(value) + ",")
                    file.write("\n")

    def load_batch(self):
        """Loads id and log information from file"""
        reply = QMessageBox.question(
            QWidget(),
            "Batch",
            "Load batch?\nAll current values will be overwritten.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            with open(self.config["path"] + "/batch.txt", "r") as file:
                for index, line in enumerate(file):
                    channel = self.channels[index]
                    values = line.split(",")
                    if len(values) > 1:
                        channel.elements[2].setText(values[0])
                        channel.elements[3].setText(values[1])

    def fill_batch(self):
        """Executes autofill for each channel"""
        for channel in self.channels:
            channel.button_auto_fill()

    def increment_batch(self):
        """Increments last letter of batch by char number"""
        for channel in self.channels:
            working_list = list(channel.elements[3].text())
            if working_list:
                try:
                    current_letter = ord(working_list[-5])
                    next_letter = chr(current_letter + 1)
                    working_list[-5] = next_letter

                    channel.elements[3].setText("".join(working_list))
                except Exception as exception:
                    msg = QMessageBox()
                    msg.setText(
                        "Could not increment channel {}.\n".format(
                            channel.channel
                        )
                        + str(exception)
                    )
                    msg.setIcon(QMessageBox.Warning)
                    msg.setWindowTitle("Increment")
                    msg.exec_()
