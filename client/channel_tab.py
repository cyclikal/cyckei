"""
Widget that controls a single channnel.
Listed in the channel tab of the main window.
"""

import json

from PySide2.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, \
     QScrollArea, QStyleOption, QStyle
from PySide2.QtCore import QTimer, Qt
from PySide2.QtGui import QPainter, QPalette

from . import workers
import functions as func


class ChannelTab(QWidget):
    def __init__(self, config, threadpool, scripts):
        """Setup each channel widget and place in QVBoxlayout"""
        QWidget.__init__(self)

        area = QScrollArea()
        contents = QWidget()
        rows = QVBoxLayout(contents)
        layout = QVBoxLayout(self)
        layout.addWidget(area)
        area.setWidget(contents)
        area.setWidgetResizable(True)
        layout.setContentsMargins(0, 0, 0, 0)
        rows.setContentsMargins(0, 0, 0, 0)
        rows.setSpacing(0)

        self.channels = []
        for channel in config["channels"]:
            self.channels.append(ChannelWidget(
                channel["channel"],
                config["record_dir"] + "/tests",
                threadpool,
                scripts
            ))
            rows.addWidget(self.channels[-1])

    def paintEvent(self, event):
        option = QStyleOption()
        option.initFrom(self)
        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, option, painter, self)
        self.alternate_colors()

    def alternate_colors(self):
        # TODO: Make compatible with windows
        base = self.palette().color(QPalette.Window)
        text = self.palette().color(QPalette.WindowText)
        for channel in self.channels:
            if (int(channel.attributes["channel"]) % 2 == 0):
                color = base.lighter(120)
            else:
                color = base.darker(120)
            channel.setStyleSheet(
                "QComboBox {{"
                "   color: {};"
                "}}"
                ".ChannelWidget {{"
                "   background: {};"
                "}}".format(text.name(), color.name())
            )


class ChannelWidget(QWidget):
    """Controls and stores information for a given channel"""

    def __init__(self, channel, record_folder, threadpool, scripts):
        super(ChannelWidget, self).__init__()
        # Default Values
        self.attributes = {
            "channel": channel,
            "record_folder": record_folder,
            "id": 0,
            "comment": "No Comment",
            "package": "Pouch",
            "type": "Full",
            "path": "default.pyb",
            "mass": 1,
            "requestor": "Unspecified",
            "protocol_name": None,
            "script_title": None,
        }

        self.threadpool = threadpool
        self.scripts = scripts

        self.setMinimumSize(1050, 110)

        # General UI
        sides = QHBoxLayout(self)
        left = QVBoxLayout()
        sides.addLayout(left)
        middle = QVBoxLayout()
        sides.addLayout(middle)
        right = QVBoxLayout()
        sides.addLayout(right)

        # TODO: make divider change color if running
        # Divider
        divider = QWidget()
        divider.setObjectName("off")
        divider.setMinimumWidth(2)
        divider.setMaximumWidth(2)
        middle.addWidget(divider)

        # Settings
        settings = QHBoxLayout()
        left.addLayout(settings)
        self.settings = self.get_settings()
        for element in self.settings:
            settings.addWidget(element)

        # Status
        args = [
            "Loading Status...",
            "Current Cell Status",
        ]
        self.status = func.label(*args)
        left.addWidget(self.status)

        # Controls
        controls = QHBoxLayout()
        right.addLayout(controls)
        for element in self.get_controls():
            controls.addWidget(element)

        # Feedback
        args = [
            "",
            "Server Response",
        ]
        self.feedback = func.label(*args)
        self.feedback.setAlignment(Qt.AlignCenter)
        right.addWidget(self.feedback)

        # Load default JSON
        self.json = json.load(open(func.find_path("assets/defaultJSON.json")))

        # Set initial status and set status timer
        self.update_status()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(5000)

    def get_settings(self):
        """Creates all UI elements and adds them to elements list"""
        elements = []

        # Cell channel label
        args = [
            "{}:".format(self.attributes["channel"]),
            "Channel {}".format(self.attributes["channel"]),
            "id_label"
        ]
        elements.append(func.label(*args))
        elements[-1].setMinimumSize(25, 25)

        # Script selection box
        available_scripts = []
        if self.scripts.script_list:
            self.attributes["script_title"] = self.scripts.script_list[0].title
            for script in self.scripts.script_list:
                available_scripts.append(script.title)
        elements.append(func.combo_box(available_scripts,
                                       "Select scripts to run",
                                       "script_title",
                                       self.set))

        # Line Edits
        editables = [
            ["Cell ID", "Cell identification", "id"],
            ["Log file", "File to log to, placed in specified logs folder",
                "path"],
            ["Mass", "Mass of Cell", "mass"],
            ["Comment", "Unparsed Comment", "comment"],
        ]
        for line in editables:
            elements.append(func.line_edit(*line, self.set))

        # Combo Boxes
        selectables = [
            [["Pouch", "Coin", "Cylindrical", "Unknown"],
                "Package Type", "package"],
            [["Full",  "Half", "AnodeHalf", "CathodeHalf", "LithiumLithium",
                "Symmetric", "Unknown"],
                "Package Type", "type"],
            [["Unspecified", "VC", "GE", "LK"],
                "Cell Type", "requestor"],
        ]
        for box in selectables:
            elements.append(func.combo_box(*box, self.set))

        return elements

    def get_controls(self):
        buttons = [
            ["Read Cell", "Read Voltage of Connected Cell"],
            ["Start", "Start Cycle"],
            ["Pause", "Pause Cycle"],
            ["Resume", "Resume Cycle"],
            ["Stop", "Stop Cycle"],
        ]
        elements = []
        for but in buttons:
            elements.append(func.button(*but, self.button))

        return elements

    def button(self, text):
        func.feedback("{} in progress...".format(text), self)
        if text == "Read Cell":
            worker = workers.Read(self)
        else:
            worker = workers.Control(self, text.lower(), self.scripts)
        worker.signals.status.connect(func.feedback)
        self.threadpool.start(worker)

    def set(self, key, text):
        """Sets object's script to one selected in dropdown"""
        self.attributes[key] = text

    def paintEvent(self, event):
        option = QStyleOption()
        option.initFrom(self)
        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, option, painter, self)

    def update_status(self):
        updater = workers.UpdateStatus(self)
        updater.signals.status.connect(func.status)
        self.threadpool.start(updater)
