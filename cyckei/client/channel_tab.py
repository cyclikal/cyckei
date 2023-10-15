"""Widget that controls a single channnel.
Listed in the channel tab of the main window.
"""

import json
import logging
import os
from pathlib import Path

from PySide2.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, \
     QScrollArea, QStyleOption, QStyle, QFileDialog
from PySide2.QtCore import QTimer, Qt, QRegExp
from PySide2.QtGui import QPainter, QPalette, QRegExpValidator

from . import workers
from cyckei.functions import func, gui

logger = logging.getLogger('cyckei_client')


class ChannelTab(QWidget):
    """Object that creates a window to interact with cycler channels from the server.

    Attributes:
        config (dict): Holds Cyckei launch settings.
        resource (dict): A dict holding the Threadpool object for threads to be pulled from.
        channels (list): A list of ChannelWidget objects.
        timer (QTimer): A timer for the status of cells.
    |
    """

    def __init__(self, config, resource, parent, plugin_info, channel_info):
        """Inits ChannelTab with channels, config, resource, and timer. Creates each channel widget and place in QVBoxlayout.

        Args:
            config (dict): Holds Cyckei launch settings.
            resource (dict): A dict holding the Threadpool object for threads to be pulled from.
            parent (MainWindow): The MainWindow object that created this ChannelTab.
            plugin_info (list): A list of dicts holding info about installed plugins.
            channel_info (dict): A dict of nested dicts holding info about each connected channel.
            |
        """
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
            try:
                self.channels.append(ChannelWidget(
                    channel["channel"],
                    config,
                    resource,
                    plugin_info,
                    channel_info[str(channel["channel"])]
                ))
                rows.addWidget(self.channels[-1])
            except KeyError:
                pass
        self.alternate_colors()

        # Set initial status and set status timer
        self.update_status()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(
            int(self.config["behavior"]["update-interval"]) * 1000)

    def alternate_colors(self):
        """Sets the channels to alternate between light and dark.
        
        |
        """
        # TODO: Make dark mode compatible with windows
        base = self.palette().color(QPalette.Window)
        text = self.palette().color(QPalette.WindowText)
        for channel in self.channels:
            if (int(channel.attributes["channel"]) % 2 == 0):
                color = base.lighter(110)
            else:
                color = base.darker(110)
            channel.default_color = color.name()
            channel.setStyleSheet(
                "QComboBox {{"
                "   color: {};"
                "}}"
                ".ChannelWidget {{"
                "   background: {};"
                "}}".format(text.name(), color.name())
            )

    def update_status(self):
        """Updates the status section of a channel.

        |
        """
        updater = workers.UpdateStatus(self.channels, self.config)
        self.resource["threadpool"].start(updater)

    def paintEvent(self, event):
        """Redraws the window with the current visual settings. Overrides the defaul QT paintEvent.
        
        |
        """
        option = QStyleOption()
        option.initFrom(self)
        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, option, painter, self)


class ChannelWidget(QWidget):
    """Object that controls and stores information for a given channel.

    Attributes:
        attributes (dict): Holds info about the ChannelWidget: Channel info, cell info, script info, etc.
        config (dict): Holds Cyckei launch settings.
        default_color (str): The default background color of the channel.
        divider (QWidget): Divides the channel widget vertically between info and controls.
        feedback (QLabel): A label under the controls that gives info when a control is pressed.
        json (dict): Holds the default attribtues of a ChannelWidget. Taken from an outside file.
        script_label (QLabel): A gui label that indicates if there is a selected script.
        settings (list): A list of gui elements to be added to the window, set in the set_settings function.
        state (str): The step in the protocol performed on a cell.
        state_changed (bool): Indicates whether the channel state has changed.
        status (QLabel): A gui label that indicates a cell's status.
        threadpool (dict):  Holds the Threadpool object from resource for threads to be pulled from.
    
    |
    """

    def __init__(self, channel, config, resource, plugin_info, cur_channel_info):
        """Inits ChannelWidget with attributes, config, divider, feedback, json, script_label, status, and threadpool.

        Args:
            channel (int): Id number for the channel corresponding with this Widget.
            config (dict): Holds Cyckei launch settings.
            resource (dict): A dict holding the Threadpool object for threads to be pulled from.
            plugin_info (list): A list of dicts holding info about installed plugins.
            cur_channel_info (dict): A dict holding info about the corresponding channel for this Widget.
        |
        """
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
            "record_folder": os.path.join(config["arguments"]["record_dir"], "tests"),
            "mass": None,
            "protocol_name": None,
            "script_path": None,
            "script_content": None
        }
        self.config = config
        # State and state_changed currently only used for changing the color 
        # of the channel background. If state_changed wants to be used for anything
        # else you should add a new bool like "change_color", since state_changed is
        # changed to false after changing color to mitigate startup lag.
        self.state = None
        self.state_changed = False
        self.default_color = None
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
            self.set_script("",os.path.join(self.config["arguments"]["record_dir"], "scripts", cur_channel_info["protocol_name"]))
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
        """Creates all UI settings and adds them to settings list.

        Args:
            cur_channel_info (dict): A dict holding info about the corresponding channel for this Widget.
            plugin_info (list): A list of dicts holding info about installed plugins.

        Returns:
            list: a list of gui elements to be added to the window.
        |
        """
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
        # Look up regex rules for clarification
        file_rgx = QRegExp("^[^:\"*?/<>\n|\\\\]+$")
        validator = QRegExpValidator(file_rgx)
        for line in editables:
            self.settings.append(gui.line_edit(*line, self.set))
            # Allowing only filename safe characters in editables
            if line[0] == 'Filename':
                self.settings[-1].setValidator(validator)
        # Check each spot and update if the client was closed while the
        # server was still running protocols
        
        # Parses the filepath for a script, removes the extension,
        # and sets the filename slot
        if cur_channel_info['path'] != None:
            split_path = cur_channel_info['path'].split('\\')
            split_path = split_path[-1].split('.')[:-1]
            filename = ""
            for i in split_path:
                filename = filename + i + "."
            self.settings[2].setText(filename[:-1])

        # Fills in cellid slot
        if cur_channel_info['cellid'] != None:
             self.settings[3].setText(cur_channel_info['cellid'])

        # Fills in comment slot
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

    def set_state(self, state=None):
        """Changes the state of the channel and marks if the state has been changed or not.
        
        Args:
            state (str, optional): The step the channel protocol is on. Defaults to None.
        |
        """
        if self.state != state:
            self.state = state
            self.state_changed = True
        else:
            self.state_changed = False

    def set_bg_color(self):
        """Checks whether the background needs to be changed and acts accordingly
        
        |
        """
        if self.state_changed:
            if self.state == "charge":
                self.setStyleSheet(
                    f"background-color: {gui.green}")
                self.state_changed = False
            elif self.state == "discharge":
                self.setStyleSheet(
                    f"background-color: {gui.red}")
                self.state_changed = False
            elif self.state == "sleep":
                self.setStyleSheet(
                    f"background-color: {gui.yellow}")
                self.state_changed = False
            elif self.state == "no control":
                self.setStyleSheet(
                    f"background-color: {gui.light_blue}")
                self.state_changed = False
            else:
                self.setStyleSheet(
                    f"background-color: {self.default_color}")
                self.state_changed = False

    def unlock_settings(self):
        """Sets the status of each QObject in settings to be interactable
        
        |
        """
        for setting in self.settings:
            setting.setEnabled(True)

    def lock_settings(self):
        """Sets the status of each QObject in settings to be uninteractable
        
        |
        """
        for setting in self.settings:
            setting.setDisabled(True)
            
    def set_script(self, button_text, filename=None):
        """Sets the protocol for a channel to run
        
        By default opens a finder window to select a file
        If a filepath is already provided then the finder window is skipped.

        Args:
            button_text (str): The text of the button being pressed.
            filename (str, optional): The name of the script file at the end of the stored script path. Defaults to None.
        |
        """
        if filename == None:
            filename = QFileDialog.getOpenFileName(
                self,
                "Open Script",
                os.path.join(self.config["arguments"]["record_dir"], "scripts"))
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
        """Creates a set of buttons in an element that control the cycler.
        
        Returns:
            list: A list of gui buttons that control the cycler.
        |
        """
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
        """Controls what happens when a button on the control panel is pressed.

        Creates workers and uses the threadpool to run cycler functions.
        
        Args:
            text (str): Button text that determines which function to do.
        |
        """
        gui.feedback("{} in progress...".format(text), self)
        if text == "Check":
            worker = workers.Read(self.config, self)
        else:
            worker = workers.Control(
                self.config, self, text.lower(), temp=False)
        worker.signals.status.connect(gui.feedback)
        self.threadpool.start(worker)

    def set(self, key, text):
        """Sets the attributes dict using the corresponding key and text.
        
        Used to set ChannelWidget's script to the one selected in dropdown.
        
        Args:
            key (str): The key in the attributes dict in the ChannelWidget to have its value changed.
            text (str): The new value for the corresponding key in the attributes dict.
        |
        """
        self.attributes[key] = text

    def set_plugin(self, key, text):
        """Sets object's plugin to one selected in dropdown

        Args:
            key (str): The key in the "plugins" section of the attributes dict in the ChannelWidget to have its value changed.
            text (str): The new value for the corresponding key in the "plugins" section of the attributes dict.
        |
        """
        self.attributes["plugins"][key] = text

    def paintEvent(self, event):
        """Redraws the window with the current visual settings. Overrides the defaul QT paintEvent.
        
        |
        """
        option = QStyleOption()
        option.initFrom(self)
        painter = QPainter(self)
        self.set_bg_color()
        self.style().drawPrimitive(QStyle.PE_Widget, option, painter, self)
