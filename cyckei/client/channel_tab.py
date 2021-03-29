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

logger = logging.getLogger('cyckei_client')


class ChannelTab(QWidget):
    """Object that creates a window to interact with cycler channels from the server.

    Attributes:
        config (dict): Holds Cyckei launch settings.
        resource (dict): 
        channels (list):
        timer (QTimer): A timer for the status of cells
    """
    def __init__(self, config, resource, parent, plugin_info, channel_info):
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
                resource,
                plugin_info,
                channel_info[str(channel["channel"])]
            ))
            rows.addWidget(self.channels[-1])
        self.alternate_colors()

        # Set initial status and set status timer
        self.update_status()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(
            int(self.config["behavior"]["update-interval"]) * 1000)

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


class ChannelWidget(QWidget):
    """Controls and stores information for a given channel"""

    def __init__(self, channel, config, resource, plugin_info, cur_channel_info):
        super(ChannelWidget, self).__init__()
        # Default Values
        self.attributes = {
            "channel": channel,
            "path": "",
            "cellid": None,
            "comment": "",
            "package": None,
            "celltype": None,
            "requester": None,
            "plugins": {},
            "record_folder": config["arguments"]["record_dir"] + "/tests",
            "mass": None,
            "protocol_name": None,
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
        self.divider.setStyleSheet(f"background-color: {gui.gray}")
        middle.addWidget(self.divider)

        # Settings
        setting_box = QHBoxLayout()
        left.addLayout(setting_box)
        setting_elements = self.get_settings(cur_channel_info, plugin_info)
        for element in setting_elements:
            setting_box.addLayout(element)

        # Script
        if cur_channel_info["protocol_name"] == None:
            self.script_label = gui.label("Script: None", "Current script")
        else:
            self.script_label = gui.label("Script: "+cur_channel_info["protocol_name"], "Current script")
            # If a script was running when the client was closed this line keeps that script as the active one
            self.set_script("",self.config["arguments"]["record_dir"] + "/scripts/"+ cur_channel_info["protocol_name"])
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

    def get_settings(self, cur_channel_info, plugin_info):
        """Creates all UI settings and adds them to settings list"""
        labels = []
        self.settings = []

        # Cell channel label
        labels.append("")
        args = [
            "{}:".format(self.attributes["channel"]),
            "Channel {}".format(self.attributes["channel"]),
            "id_label"
        ]
        self.settings.append(gui.label(*args))
        self.settings[-1].setMinimumSize(25, 25)

        # Script File Dialog
        labels.append("Script:")
        self.settings.append(gui.button("Open File", "Open Script file",
                                        connect=self.set_script))

        # Line Edits
        labels.append("Log File:")
        labels.append("Cell ID:")
        labels.append("Comment:")
        editables = [
            ["Filename", "File to log to, placed in specified logs folder",
                "path"],
            ["ID", "Cell identification", "cellid"],
            ["Comment", "Unparsed Comment", "comment"],
        ]
        for line in editables:
            self.settings.append(gui.line_edit(*line, self.set))

        # Check each spot and update if the client was closed while the
        # server was still running protocols
        if cur_channel_info['path'] != None:
            split_path = cur_channel_info['path'].split('\\')
            self.settings[2].setText(split_path[-1])

        if cur_channel_info['cellid'] != None:
             self.settings[3].setText(cur_channel_info['cellid'])

        if cur_channel_info['comment'] != None:
             self.settings[4].setText(cur_channel_info['comment'])

        # Plugin Assignments
        plugin_sources = []
        for plugin in plugin_info:
            labels.append(f"{plugin['name']} Source:")
            plugin_sources.append([])
            plugin_sources[-1].append(["None"] + plugin["sources"])
            plugin_sources[-1].append(
                f"Set Measurement Source for '{plugin['name']}' Plugin.")
            plugin_sources[-1].append(plugin["name"])

        for source in plugin_sources:
            self.settings.append(gui.combo_box(*source, self.set_plugin))

        # Zip Settings and layers together into elements
        elements = []
        for label, setting in zip(labels, self.settings):
            elements.append(QVBoxLayout())
            elements[-1].addWidget(gui.label(f"<i><small>{label}</small></i>"))
            elements[-1].addWidget(setting)

        return elements

    # 
    def set_script(self, button_text, filename=None):
        """Sets the protocol for a channel to run
        
        By default opens a finder window to select a file
        If a filepath is already provided then the finder window is skipped.
        """
        if filename == None:
            filename = QFileDialog.getOpenFileName(
                self,
                "Open Script",
                self.config["arguments"]["record_dir"] + "/scripts")
            filename = filename[0]

        self.attributes["protocol_name"] = filename.split("/")[-1]
        if filename:
            filepath = Path(filename).resolve().absolute()
            if filepath.is_dir() is False:
                self.attributes['script_path'] = str(filepath)
                try:
                    self.attributes['script_content'] \
                        = open(self.attributes['script_path'], "r").read()
                    self.script_label.setText(f'Script: {filepath.name}')
                except (UnicodeDecodeError, PermissionError, FileNotFoundError) as error:
                    logger.error(
                        f"Could not read file: {self.attributes['script_path']}")
                    logger.exception(error)

    def get_controls(self):
        buttons = [
            ["Start", "Start Cycle", self.button],
            ["Stop", "Stop Cycle", self.button],
            ["Check", "Attempt to Read Cell", self.button],
            ["Pause", "Pause Cycle", self.button],
            ["Resume", "Resume Cycle", self.button]
        ]
        elements = []
        for but in buttons:
            elements.append(gui.button(*but))

        return elements

    def button(self, text):
        gui.feedback("{} in progress...".format(text), self)
        if text == "Check":
            worker = workers.Read(self.config, self)
        else:
            worker = workers.Control(
                self.config, self, text.lower(), temp=False)
        worker.signals.status.connect(gui.feedback)
        self.threadpool.start(worker)

    def set(self, key, text):
        """Sets object's script to one selected in dropdown"""
        self.attributes[key] = text

    def set_plugin(self, key, text):
        """Sets object's script to one selected in dropdown"""
        self.attributes["plugins"][key] = text

    def paintEvent(self, event):
        option = QStyleOption()
        option.initFrom(self)
        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, option, painter, self)
