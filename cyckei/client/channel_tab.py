"""
Widget that controls a single channnel.
Listed in the channel tab of the main window.
"""

import json
import logging
from pathlib import Path

from PySide2.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, \
     QScrollArea, QStyleOption, QStyle, QFileDialog
from PySide2.QtCore import QTimer, Qt
from PySide2.QtGui import QPainter, QPalette

from . import workers
from cyckei.functions import func, gui

UPDATE_INTERVAL = 1000  # milliseconds
logger = logging.getLogger('cyckei')


class ChannelTab(QWidget):
    def __init__(self, config, resource, parent):
        """Setup each channel widget and place in QVBoxlayout"""
        QWidget.__init__(self, parent)
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

    def alternate_colors(self):
        # TODO: Make dark mode compatible with windows
        base = self.palette().color(QPalette.Window)
        text = self.palette().color(QPalette.WindowText)
        for channel in self.channels:
            if (int(channel.attributes["channel"]) % 2 == 0):
                color = base.lighter(110)
            else:
                color = base.darker(110)
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

    def paintEvent(self, event):
        option = QStyleOption()
        option.initFrom(self)
        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, option, painter, self)
        self.alternate_colors()


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
            "script_path": None,
            "script_content": None
        }
        self.config = config

        self.threadpool = resource["threadpool"]
        # self.scripts = resource["scripts"]

        self.setMinimumSize(800, 150)

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
        self.divider.setStyleSheet("background-color: {}".format(gui.gray))
        middle.addWidget(self.divider)

        # Settings
        settings = QHBoxLayout()
        left.addLayout(settings)
        self.settings = self.get_settings()
        for element in self.settings:
            settings.addWidget(element)

        # Script
        self.script_label = gui.label("Script: None", "Current script loaded")
        left.addWidget(self.script_label)

        # Status
        args = ["Loading Status...", "Current Cell Status"]
        self.status = gui.label(*args)
        left.addWidget(self.status)

        # Controls
        controls = QHBoxLayout()
        right.addLayout(controls)
        for element in self.get_controls():
            controls.addWidget(element)

        # Feedback
        args = ["", "Server Response"]
        self.feedback = gui.label(*args)
        self.feedback.setAlignment(Qt.AlignCenter)
        right.addWidget(self.feedback)

        # Load default JSON
        self.json = json.load(open(
            func.asset_path("default_packet.json")))

    def get_settings(self):
        """Creates all UI elements and adds them to elements list"""
        elements = []

        # Cell channel label
        args = [
            "{}:".format(self.attributes["channel"]),
            "Channel {}".format(self.attributes["channel"]),
            "id_label"
        ]
        elements.append(gui.label(*args))
        elements[-1].setMinimumSize(25, 25)

        # Script File Dialog
        elements.append(gui.button("Script", "Open Script file",
                                   connect=self.set_script))

        # Line Edits
        editables = [
            ["Log file", "File to log to, placed in specified logs folder",
                "path"],
            ["Cell ID", "Cell identification", "cellid"],
            ["Comment", "Unparsed Comment", "comment"],
        ]
        for line in editables:
            elements.append(gui.line_edit(*line, self.set))

        return elements

    def set_script(self, button_text):
        filename = QFileDialog.getOpenFileName(
            self,
            "Open Script",
            self.config["record_dir"] + "/scripts")

        filepath = Path(filename[0]).resolve().absolute()
        self.attributes['script_path'] = str(filepath)
        try:
            self.attributes['script_content'] \
                = open(self.attributes['script_path'], "r").read()
            self.script_label.setText(f'Script: {filepath.name}')
        except (UnicodeDecodeError, PermissionError) as error:
            logger.error(f"cyckei.client.channel_tab.ChannelWidget.set_script: \
                Could not read file: {self.attributes['script_path']}")
            logger.exception(error)

    def get_controls(self):
        buttons = [
            ["Start", "Start Cycle", self.button],
            ["Stop", "Stop Cycle", self.button],
            ["Check", "Attempt to Read Cell", self.button, False],
            ["Pause", "Pause Cycle", self.button, False],
            ["Resume", "Resume Cycle", self.button, False]
        ]
        elements = []
        for but in buttons:
            elements.append(gui.button(*but))

        return elements

    def button(self, text):
        func.feedback("{} in progress...".format(text), self)
        if text == "Check":
            worker = workers.Read(self.config, self)
        else:
            worker = workers.Control(
                self.config, self, text.lower(), temp=False)
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
