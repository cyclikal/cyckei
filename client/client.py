"""Main window for the cyckei client."""

import logging
import sys
import functools

from PySide2.QtWidgets import QMainWindow, QTabWidget
from PySide2.QtCore import QThreadPool

from .channel_tab import ChannelTab
from .script_tab import ScriptEditor
from .log_tab import LogViewer
from . import workers
from .scripts import ScriptList
import functions as func


def help():
    """Direct to help"""
    msg = "For help refer to the HELP.md and README.md files located in" \
          "the cyckei install location, or online on our GitLab page." \
          "\n\ngitlab.com/cyclikal/cyckei"
    func.message(msg)


def about(version):
    """Display basic information about cyckei"""
    msg = "Cyckei version {}\n\n" \
          "Cyckei is developed by Gabriel Ewig and Vincent Chevrier " \
          "at Cyclikal, LLC.\n\n Updates and source code can be found " \
          "on GitLab at gitlab.com/cyclikal/cyckei. \n\nFor information" \
          "about Cyclikal, visit cyclikal.com.".format(version)
    func.message(msg)


class MainWindow(QMainWindow):
    """Main Window class which is and sets up itself"""
    # Setup main windows
    def __init__(self, config):
        super(MainWindow, self).__init__()
        # Set basic window properties
        self.setWindowTitle("Cyckei Client")
        self.config = config
        self.resize(1100, 600)

        self.setStyleSheet(
            open(func.find_path("assets/style.css"), "r").read())

        resource = {}
        # Setup ThreadPool
        resource["threadpool"] = QThreadPool()
        self.threadpool = resource["threadpool"]
        logging.info("Multithreading set with maximum {} threads".format(
            resource["threadpool"].maxThreadCount()
        ))

        # Load scripts
        resource["scripts"] = ScriptList(config)

        # Create menu and status bar
        self.create_menu()
        self.status_bar = self.statusBar()

        # Create Tabs
        resource["tabs"] = QTabWidget(self)
        self.setCentralWidget(resource["tabs"])

        resource["tabs"].addTab(ChannelTab(config, resource), "Channels")
        resource["tabs"].addTab(ScriptEditor(config, resource), "Scripts")
        resource["tabs"].addTab(LogViewer(config, resource), "Logs")

        self.threadpool = resource["threadpool"]
        self.channels = resource["tabs"].widget(0).channels

    def create_menu(self):
        """Setup menu bar"""

        entries = {
            "Client": [
                ["&Info", functools.partial(about, self.config["version"]),
                    "About Cyckei"],
                ["&Help", help, "Help Using Cyckei"],
                ["&Close", sys.exit, "Exit Client Application"]
            ],
            "Server": [
                ["&Ping", self.ping_server, "Test Connection to Server"]
            ],
            "Batch": [
                ["&Fill All", self.fill_batch,
                    "Auto Fill All Log Files in Batch"],
                ["&Increment", self.increment_batch,
                    "Increment Last Letter for Entire Batch"],
                ["&Save", self.save_batch, "Save Batch as File"],
                ["&Load", self.load_batch, "Load Batch from File"]
            ]
        }

        for key, items in entries.items():
            menu = self.menuBar().addMenu(key)
            for item in items:
                menu.addAction(func.action(*item, parent=self))

    def ping_server(self):
        worker = workers.Ping(self.config)
        worker.signals.alert.connect(func.message)
        self.threadpool.start(worker)

    def save_batch(self):
        """Saves id and log information to file"""
        msg = {
            "text": "Save batch?",
            "info": "Current saved batch will be deleted.",
            "confirm": True,
            "icon": func.Question
        }
        if func.message(**msg):
            batch = []
            for channel_widget in self.channels:
                channel = [channel_widget.attributes["cellid"],
                           channel_widget.attributes["path"]]
                batch.append(channel)

            with open(self.config["record_dir"] + "/batch.txt", "a") as file:
                file.truncate(0)
                for channel in batch:
                    for value in channel:
                        file.write(str(value) + ",")
                    file.write("\n")

    def load_batch(self):
        """Loads id and log information from file"""
        msg = {
            "text": "Load batch?",
            "info": "All current values will be overwritten.",
            "confirm": True,
            "icon": func.Question
        }
        if func.message(**msg):
            with open(self.config["record_dir"] + "/batch.txt", "r") as file:
                for index, line in enumerate(file):
                    channel = self.channels[index]
                    values = line.split(",")
                    if len(values) > 1:
                        channel.settings[2].setText(values[0])
                        channel.settings[3].setText(values[1])

    def fill_batch(self):
        """Executes autofill for each channel"""
        for channel in self.channels:
            self.threadpool.start(workers.AutoFill(channel))

    def increment_batch(self):
        """Increments last letter of batch by char number"""
        for channel in self.channels:
            working_list = list(channel.settings[3].text())
            if working_list:
                try:
                    current_letter = ord(working_list[-5])
                    next_letter = chr(current_letter + 1)
                    working_list[-5] = next_letter

                    channel.settings[3].setText("".join(working_list))
                except Exception as exception:
                    msg = {
                        "text": "Could not increment channel {}.\n".format(
                            channel["channel"]
                        ) + str(exception),
                        "icon": func.Warning
                    }
                    func.message(**msg)
