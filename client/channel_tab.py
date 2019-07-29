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

UPDATE_INTERVAL = 12000


class ChannelTab(QWidget):
    def __init__(self, config, resource):
        """Setup each channel widget and place in QVBoxlayout"""
        QWidget.__init__(self)
        self.config = config
        self.resource = resource

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
                config,
                resource
            ))
            rows.addWidget(self.channels[-1])

        # Set initial status and set status timer
        self.update_status()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(UPDATE_INTERVAL)

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

    def update_status(self):
        updater = workers.UpdateStatus(self.channels, self.config)
        self.resource["threadpool"].start(updater)


class ChannelWidget(QWidget):
    """Controls and stores information for a given channel"""

    def __init__(self, channel, config, resource):
        super(ChannelWidget, self).__init__()
        # Default Values
        self.attributes = {
            "channel": channel,
            "record_folder": config["record_dir"] + "/tests",
            "cellid": 0,
            "comment": "No Comment",
            "package": "Pouch",
            "celltype": "Full",
            "path": "default.pyb",
            "mass": 1,
            "requester": "Unspecified",
            "protocol_name": None,
        }
        self.config = config

        self.threadpool = resource["threadpool"]
        self.scripts = resource["scripts"]

        self.setMinimumSize(1050, 110)

        # General UI
        sides = QHBoxLayout(self)
        left = QVBoxLayout()
        sides.addLayout(left)
        middle = QVBoxLayout()
        sides.addLayout(middle)
        right = QVBoxLayout()
        sides.addLayout(right)

        # Divider
        self.divider = QWidget(self)
        self.divider.setMinimumWidth(2)
        self.divider.setMaximumWidth(2)
        middle.addWidget(self.divider)

        # Settings
        settings = QHBoxLayout()
        left.addLayout(settings)
        self.settings = self.get_settings()
        for element in self.settings:
            settings.addWidget(element)

        # Status
        args = ["Loading Status...", "Current Cell Status"]
        self.status = func.label(*args)
        left.addWidget(self.status)

        # Controls
        controls = QHBoxLayout()
        right.addLayout(controls)
        for element in self.get_controls():
            controls.addWidget(element)

        # Feedback
        args = ["", "Server Response"]
        self.feedback = func.label(*args)
        self.feedback.setAlignment(Qt.AlignCenter)
        right.addWidget(self.feedback)

        # Load default JSON
        self.json = json.load(open(
            func.find_path("assets/default_packet.json")))

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
            self.attributes["protocol_name"] \
                = self.scripts.script_list[0].title
            for script in self.scripts.script_list:
                available_scripts.append(script.title)
        elements.append(func.combo_box(available_scripts,
                                       "Select scripts to run",
                                       "protocol_name",
                                       self.set))

        # Line Edits
        editables = [
            ["Cell ID", "Cell identification", "cellid"],
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
                "Package Type", "celltype"],
            [["Unspecified", "VC", "GE", "LK"],
                "Cell Type", "requester"],
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
            worker = workers.Read(self.config, self)
        else:
            worker = workers.Control(
                self.config, self, text.lower(), self.scripts)
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
