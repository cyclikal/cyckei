"""Controls log tab, which displays logs as they are being recorded"""

import webbrowser
from os import path, listdir
import logging

from PySide2.QtWidgets import QVBoxLayout, QHBoxLayout, \
    QListWidget, QListWidgetItem, QWidget, QPlainTextEdit

from functions import gui

logger = logging.getLogger('cyckei')


class LogViewer(QWidget):
    """Object of log tab"""
    def __init__(self, config, resource):
        QWidget.__init__(self)
        self.path = path.join(config["record_dir"], "tests")
        self.threadpool = resource["threadpool"]

        self.log_list = QListWidget()
        self.log_list.itemClicked.connect(self.log_clicked)
        self.folder_list = QListWidget()
        self.folder_list.itemClicked.connect(self.load_logs)

        # Create overall layout
        columns = QHBoxLayout(self)
        list_rows = QVBoxLayout()
        columns.addLayout(list_rows)
        edit_rows = QVBoxLayout()
        columns.addLayout(edit_rows)
        columns.setStretch(0, 1)
        columns.setStretch(1, 5)

        list_rows.addWidget(self.folder_list)
        list_rows.addWidget(self.log_list)
        list_rows.setStretch(0, 1)
        list_rows.setStretch(1, 3)

        # create edit_rows
        self.title_bar = gui.label("Select file on left to view log.")
        edit_rows.addWidget(self.title_bar)

        self.editor = QPlainTextEdit()
        edit_rows.addWidget(self.editor)

        controls = QHBoxLayout()
        edit_rows.addLayout(controls)

        # create control buttons
        buttons = [
            ["Reload", "Update Logs", self.reload],
            ["Open Folder", "Show Log Folder", self.open_explorer]
        ]

        for button in buttons:
            controls.addWidget(gui.button(*button))

        self.reload(None)

    def open_explorer(self, text=None):
        """Open logging folder in explorer"""
        webbrowser.open("file://{}".format(self.path))

    def log_clicked(self):
        """Display text of clicked file in text box"""
        try:
            self.title_bar.setText(self.log_list.currentItem().path)
            self.editor.setPlainText(self.log_list.currentItem().content)
        except AttributeError:
            logger.warning("Cannot load scripts, none found.")

    def load_logs(self):
        self.log_list.clear()
        self.editor.clear()
        logs = []

        files = listdir(self.folder_list.currentItem().path)
        for file in files:
            abspath = path.join(self.folder_list.currentItem().path, file)
            if not path.isdir(abspath):
                logs.append(Log(abspath, file))

        for log in logs:
            self.log_list.addItem(log)
        self.log_list.setCurrentItem(
            self.log_list.item(0))
        self.log_clicked()

    def reload(self, item):
        self.folder_list.clear()
        self.log_list.clear()
        self.editor.clear()
        folders = []

        files = listdir(self.path)
        for file in files:
            abspath = path.join(self.path, file)
            if path.isdir(abspath):
                folders.append(Folder(abspath, file))
        for folder in folders:
            self.folder_list.addItem(folder)
        self.folder_list.setCurrentItem(
            self.folder_list.item(0))
        self.load_logs()


class Log(QListWidgetItem):
    """Object of log, stores title and content of file for quick access"""
    def __init__(self, path, name):
        super(Log, self).__init__()
        self.path = path
        self.name = name
        self.setText(self.name)
        try:
            with open(self.path) as file:
                self.content = file.read()
        except UnicodeDecodeError as error:
            self.content = "Could not decode: {}".format(error)


class Folder(QListWidgetItem):
    """Object of log, stores title and content of file for quick access"""
    def __init__(self, path, name):
        super(Folder, self).__init__()
        self.path = path
        self.setText(name)
