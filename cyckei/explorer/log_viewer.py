"""Controls log tab, which displays logs as they are being recorded"""

import webbrowser
from os import path, listdir
import logging
import json

from PySide2.QtWidgets import QVBoxLayout, QHBoxLayout, \
    QListWidget, QListWidgetItem, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.pyplot import FuncFormatter

from cyckei.functions import gui

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

        self.editor = LogDisplay()
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
            self.editor.update(self.log_list.currentItem().content)
        except AttributeError:
            logger.warning("Cannot load scripts, none found.")

    def load_logs(self):
        self.log_list.clear()
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


class LogDisplay(QWidget):
    def __init__(self):
        super(LogDisplay, self).__init__()
        layout = QVBoxLayout(self)
        info = QHBoxLayout()
        layout.addLayout(info)

        self.info_elements = {
            "cellid": gui.label("Cell ID", "Cell ID"),
            "date_start_timestr": gui.label("Start Time", "Start Time"),
            "comment": gui.label("Comment", "Test Comment"),
        }
        for key, value in self.info_elements.items():
            info.addWidget(value)

        self.protocol_viewer = gui.text_edit("Protocol", readonly=True)
        layout.addWidget(self.protocol_viewer)

        data = QHBoxLayout()
        layout.addLayout(data)

        self.data_viewer = gui.text_edit("Test Data", readonly=True)
        data.addWidget(self.data_viewer)
        layout.setStretch(1, 1)
        layout.setStretch(2, 3)

        self.graph = GraphCanvas()
        data.addWidget(self.graph)
        data.setStretch(0, 3)
        data.setStretch(1, 2)

    def update(self, content):
        # Load data
        attr = ""
        data = ""
        for line in content.split("\n"):
            if line.startswith("#"):
                attr += line[1:] + "\n"
            else:
                data += line + "\n"
        try:
            attr = json.loads(attr)
        except json.decoder.JSONDecodeError:
            logger.warning("Could not read script file.")

        # Setting info Elements
        for common_key in attr.keys() & self.info_elements.keys():
            self.info_elements[common_key].setText(attr[common_key])
        self.protocol_viewer.setPlainText(attr["protocol"])
        self.data_viewer.setPlainText(data.replace(",", "\t"))

        # Setup graph
        points_t = []
        points_v = []
        for line in data.split("\n"):
            if "{\"" in line:
                points_t.append([])
                points_v.append([])
            else:
                info = line.strip().split(",")
                try:
                    points_t[-1].append(float(info[0]))
                    points_v[-1].append(float(info[2]))
                except (IndexError, ValueError):
                    pass
        self.graph.plot(points_t, points_v)


class GraphCanvas(FigureCanvasQTAgg):
    """Graphing Canvas using matplotlib"""

    def __init__(self):
        fig = Figure()
        self.axes = fig.add_subplot()
        FigureCanvasQTAgg.__init__(self, fig)

    def plot(self, x_data, y_data):
        self.axes.cla()
        col = ["b", "g", "r", "c", "m", "k"]
        i = 0
        for x, y in zip(x_data, y_data):
            try:
                self.axes.plot(x, y, col[i % len(col)])
            except ValueError:
                pass
            i += 1
        self.draw()


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
