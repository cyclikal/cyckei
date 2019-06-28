"""Main window for the cyckei client."""

import logging
import sys

from pkg_resources import require, DistributionNotFound
from PySide2.QtWidgets import QWidget, QMainWindow, QAction, QTabWidget,\
    QMessageBox, QMenuBar
from PySide2.QtCore import QThreadPool
from pkg_resources import resource_filename

from .channel_tab import ChannelTab
from .script_tab import ScriptEditor
from .log_tab import LogViewer
from . import workers
from .scripts import ScriptList


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

        # Set icon for windows
        try:
            import ctypes
            id = u"com.cyclikal.cyckei"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(id)
        except AttributeError:
            pass

        # Setup ThreadPool
        self.threadpool = QThreadPool()
        logging.info("Multithreading set with maximum {} threads".format(
            self.threadpool.maxThreadCount()
        ))

        # Load scripts
        scripts = ScriptList()
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
            ScriptEditor(self.channels, scripts, self.threadpool),
            "Scripts"
        )
        self.tab_widget.addTab(LogViewer(self.config, self.threadpool), "Logs")

        self.setStyleSheet(
            open(resource_filename(
                    "cyckei.client",
                    "res/style.css"), "r").read())

    def action(self, title, tip, connect):
        temp = QAction(title, self)
        temp.setStatusTip(tip)
        temp.triggered.connect(connect)
        return temp

    def create_menu(self):
        """Setup menu bar"""
        bar = QMenuBar()

        client = bar.addMenu("Client")
        client.addAction(self.action("&Info", "About Cyckei", about))
        client.addAction(self.action("&Help", "Help Using Cyckei", help))
        client.addAction(self.action("&Close", "Exit Client Application",
                                     sys.exit))

        server = bar.addMenu("Server")
        server.addAction(self.action("&Ping", "Test Connection to Server",
                                     self.ping_server))

        batch = bar.addMenu("Batch")
        batch.addAction(self.action("&Fill All",
                                    "Auto Fill All Log Files in Batch",
                                    self.fill_batch))
        batch.addAction(self.action("&Increment",
                                    "Increment Last Letter for Entire Batch",
                                    self.increment_batch))
        batch.addSeparator()
        batch.addAction(self.action("&Save", "Save Batch as File",
                                    self.save_batch))
        batch.addAction(self.action("&Load", "Load Batch from File",
                                    self.load_batch))

        return bar

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
