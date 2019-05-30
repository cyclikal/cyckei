"""Controls log tab, which displays logs as they are being recorded"""

from os import listdir, path
import subprocess
from PySide2.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit,\
    QPushButton, QListWidget, QListWidgetItem, QWidget, QStyleOption, QStyle
from PySide2.QtGui import QPainter


class LogViewer(QWidget):
    """Object of log tab"""
    def __init__(self, config):
        QWidget.__init__(self)
        self.path = config["path"] + "/tests"

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
        """Reload list and contents of logs from specified logging folder"""
        self.file_list.clear()
        self.editor.clear()
        logs = []

        files = listdir(self.path)
        if files is not None:
            for file in files:
                if path.isdir(path.join(self.path, file)):
                    pass
                else:
                    logs.append(Log(file, self.path))

        for log in logs:
            self.file_list.addItem(log)

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
    def __init__(self, title, file_path):
        super().__init__()
        self.title = title
        self.setText(self.title)
        self.content = open(file_path + "/" + self.title, "r").read()
