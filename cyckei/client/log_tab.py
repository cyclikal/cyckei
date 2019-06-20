"""Controls log tab, which displays logs as they are being recorded"""

from os import path
from glob import glob
import subprocess
from PySide2.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QStyleOption,\
    QPushButton, QListWidget, QListWidgetItem, QWidget, QPlainTextEdit, QStyle
from PySide2.QtGui import QPainter
from PySide2.QtCore import Slot, QRunnable


class LogViewer(QWidget):
    """Object of log tab"""
    def __init__(self, config, threadpool):
        QWidget.__init__(self)
        self.path = config["path"] + "/tests"
        self.threadpool = threadpool

        self.file_list = QListWidget()
        self.file_list.itemClicked.connect(self.list_clicked)

        # Create overall layout
        columns = QHBoxLayout(self)
        columns.addWidget(self.file_list)
        edit_rows = QVBoxLayout()
        columns.addLayout(edit_rows)
        columns.setStretch(0, 1)
        columns.setStretch(1, 5)

        # create edit_rows
        self.title_bar = QLabel()
        self.title_bar.setText("Select file on left to view log.")
        edit_rows.addWidget(self.title_bar)

        self.editor = QPlainTextEdit()
        edit_rows.addWidget(self.editor)

        controls = QHBoxLayout()
        edit_rows.addLayout(controls)

        # create control buttons
        reload = QPushButton()
        reload.setText("Reload")
        reload.clicked.connect(self.reload)
        controls.addWidget(reload)

        open_folder = QPushButton()
        open_folder.setText("Open Folder")
        open_folder.clicked.connect(self.open_explorer)
        controls.addWidget(open_folder)

        self.reload()

    def reload(self):
        worker = Reload(self)
        self.threadpool.start(worker)

    def open_explorer(self):
        """Open logging folder in explorer"""
        subprocess.Popen(r'explorer /select,"{}"'.format(self.path))

    def list_clicked(self, item):
        """Display text of clicked file in text box"""
        self.editor.setPlainText(item.content)

    def paintEvent(self, event):
        style_option = QStyleOption()
        style_option.initFrom(self)
        painter = QPainter(self)
        style = self.style()
        style.drawPrimitive(QStyle.PE_Widget, style_option, painter, self)


class Log(QListWidgetItem):
    """Object of log, stores title and content of file for quick access"""
    def __init__(self, file):
        super().__init__()
        self.file = file
        self.setText(self.file)
        with open(file) as file:
            self.content = file.read()


class Reload(QRunnable):
    def __init__(self, widget):
        super(Reload, self).__init__()
        self.widget = widget

    @Slot()
    def run(self):
        self.widget.file_list.clear()
        self.widget.editor.clear()
        logs = []
        files = glob("{}/*".format(self.widget.path))
        for file in files:
            if path.isdir(file):
                pass
            else:
                logs.append(Log(file))

        for log in logs:
            self.widget.file_list.addItem(log)
