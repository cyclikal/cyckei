"""Main window for the cyckei client."""

import ctypes

from PyQt5.QtWidgets import QWidget, QMainWindow, QAction, qApp, QTabWidget,\
    QMessageBox
from PyQt5.QtGui import QIcon

from client.channel_tab import ChannelTab
from client.script_tab import ScriptEditor
from client.log_tab import LogViewer


def help_page():
    """Converts markdown helpfile to html and loads in browser"""
    # # TODO: better help page


class MainWindow(QMainWindow):
    """Main Window class which is and sets up itself"""
    # Setup main windows
    def __init__(self, config, server):
        super().__init__()
        # Set basic window properties
        self.setWindowTitle("Cyckei")
        # Allows icon to show in Windows Taskbar
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "Cyckei"
        )
        self.setWindowIcon(QIcon(r"res\icon.png"))
        self.resize(1000, 562)

        # Create menu and status bar
        self.menu_bar = self.create_menu(server)
        self.status_bar = self.statusBar()

        self.tab_widget = QTabWidget(self)
        self.setCentralWidget(self.tab_widget)

        channel_tab = ChannelTab(config, server)
        self.channels = channel_tab.channels
        self.tab_widget.addTab(channel_tab, "Channels")
        self.tab_widget.addTab(ScriptEditor(self.channels, server), "Scripts")
        self.tab_widget.addTab(LogViewer(config), "Logs")

        self.setStyleSheet(open("res/style.css", "r").read())

    def create_menu(self, server):
        """Setup menu bar"""
        menu_options = []

        menu_options.append(QAction("&Help", self))
        menu_options[-1].setStatusTip("View Help in Web Browser")
        menu_options[-1].triggered.connect(help_page)

        menu_options.append(QAction("&Exit", self))
        menu_options[-1].setStatusTip("Exit Client Application")
        menu_options[-1].triggered.connect(qApp.quit)

        menu_options.append(QAction("&Ping", self))
        menu_options[-1].setStatusTip("Ping Server for Response")
        menu_options[-1].triggered.connect(server.ping_server)

        menu_options.append(QAction("&Time", self))
        menu_options[-1].setStatusTip("Get Current Server Time")
        menu_options[-1].triggered.connect(server.get_server_time)

        menu_options.append(QAction("&Start / Reconnect", self))
        menu_options[-1].setStatusTip("Start or Reconnect to Server")
        menu_options[-1].triggered.connect(server.start_server_app)

        menu_options.append(QAction("&Kill", self))
        menu_options[-1].setStatusTip("Kill Server")
        menu_options[-1].triggered.connect(server.kill_server)

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

        server = menu_bar.addMenu("&Server")
        server.addAction(menu_options[2])
        server.addAction(menu_options[3])
        server.addAction(menu_options[4])
        server.addAction(menu_options[5])

        batch = menu_bar.addMenu("&Batch")
        batch.addAction(menu_options[6])
        batch.addAction(menu_options[7])
        batch.addAction(menu_options[8])
        batch.addAction(menu_options[9])

        return menu_bar

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

            with open("res/batch.txt", "a") as file:
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
            with open("res/batch.txt", "r") as file:
                for index, line in enumerate(file):
                    channel = self.channels[index]
                    values = line.split(",")
                    channel.elements[2].setText(values[0])
                    channel.elements[3].setText(values[1])

    def fill_batch(self):
        """Executes autofill for each channel"""
        for channel in self.channels:
            channel.auto_fill()

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
