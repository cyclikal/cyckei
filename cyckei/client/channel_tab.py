"""
Widget that controls a single channnel.
Listed in the channel tab of the main window.
"""

import json
import logging


from PySide2.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, \
    QLineEdit, QPushButton, QLabel, QScrollArea, QStyleOption, \
    QStyle, QMessageBox
from PySide2.QtCore import QMetaObject
from PySide2.QtGui import QPainter
from pkg_resources import resource_filename

from cyckei.client import workers


def not_none(value):
    """Sets a None value to "None" string"""
    return "None" if value is None else str(value)


def new_button_element(text, status, connect):
    """Creates a button with given information"""
    button = QPushButton()
    button.setText(text)
    button.setStatusTip(status)
    button.clicked.connect(connect)
    return button


def new_combo_element(items, status, connect):
    """Creates a combo box with given information"""
    box = QComboBox()
    box.addItems(items)
    box.setStatusTip(status)
    box.activated[str].connect(connect)
    return box


def new_text_element(label, status, connect):
    """Creates text edit field with given information"""
    text = QLineEdit()
    text.setMinimumSize(60, 20)
    text.setPlaceholderText(label)
    text.setStatusTip(status)
    text.textChanged.connect(connect)
    return text


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
                config["path"] + "/tests",
                threadpool,
                scripts
            ))
            rows.addWidget(self.channels[-1])

    def paintEvent(self, event):
        style_option = QStyleOption()
        style_option.initFrom(self)
        painter = QPainter(self)
        style = self.style()
        style.drawPrimitive(QStyle.PE_Widget, style_option, painter, self)


class ChannelWidget(QWidget):
    """Controls and stores information for a given channel"""

    def __init__(self, channel, record_folder, threadpool, scripts):
        super().__init__()
        # Default Values
        self.attributes = {}
        self.attributes["channel"] = channel
        self.attributes["record_folder"] = record_folder
        self.attributes["id"] = 0
        self.attributes["comment"] = "No Comment"
        self.attributes["package"] = "Pouch"
        self.attributes["type"] = "Full"
        self.attributes["path"] = "default.pyb"
        self.attributes["mass"] = 1
        self.attributes["requestor"] = "Unspecified"
        self.attributes["protocol_name"] = None
        self.attributes["script_title"] = None

        self.threadpool = threadpool
        self.scripts = scripts

        self.setMinimumSize(1050, 110)

        # Setup UI
        rows = QVBoxLayout(self)
        settings = QHBoxLayout()
        rows.addLayout(settings)
        self.setup_ui()

        for element in self.elements:
            settings.addWidget(element)
        rows.addWidget(self.elements[-1])
        if (int(self.attributes["channel"]) % 2 == 0):
            self.setObjectName("even")
        else:
            self.setObjectName("odd")

        # Load default JSON
        self.json = json.load(open(
            resource_filename("cyckei.client", "res/defaultJSON.json")))

        # Update status
        worker = workers.UpdateStatus(self)
        worker.signals.status.connect(self.post_status)
        self.threadpool.start(worker)

    def setup_ui(self):
        """Creates all UI elements and adds them to self.elements list"""
        self.elements = []

        # 0 - Cell channel label
        self.elements.append(QLabel())
        self.elements[-1].setStatusTip(
            "Channel {}".format(self.attributes["channel"])
        )
        self.elements[-1].setText(
            "{}:".format(self.attributes["channel"])
        )
        self.elements[-1].setObjectName("id_label")
        self.elements[-1].setMinimumSize(25, 25)

        # 1 - Script selection box
        available_scripts = []
        if self.scripts.script_list:
            self.attributes["script_title"] = self.scripts.script_list[0].title
            for script in self.scripts.script_list:
                available_scripts.append(script.title)
        self.elements.append(new_combo_element(available_scripts,
                                               "Select scripts to run",
                                               self.script_box_activated))

        # 2 - Cell identification number
        self.elements.append(new_text_element("Cell ID",
                                              "Cell identification",
                                              self.set_id))

        # 3 - Path to log file
        self.elements.append(new_text_element(
            "Log file",
            "File to log to, placed in specified logs folder",
            self.set_path
        ))

        # 4 - auto_fill Button
        self.elements.append(new_button_element(
            "AutoFill",
            "Fill log file from cell identification, defaults to [id]A.log",
            self.button_auto_fill
        ))

        # 5 - Mass
        self.elements.append(new_text_element("Mass",
                                              "Mass of Cell",
                                              self.set_mass))

        # 6 - Comment
        self.elements.append(new_text_element("Comment",
                                              "Unparsed Comment",
                                              self.set_comment))

        # 7 - Package
        package_types = ["Pouch",
                         "Coin",
                         "Cylindrical",
                         "Unknown"]
        self.elements.append(new_combo_element(package_types,
                                               "Package Type",
                                               self.package_box_activated))

        # 8 - Cell type
        cell_types = ["Full",
                      "Half",
                      "AnodeHalf",
                      "CathodeHalf",
                      "LithiumLithium",
                      "Symmetric",
                      "Unknown"]
        self.elements.append(new_combo_element(cell_types,
                                               "Cell Type",
                                               self.cell_box_activated))

        # 9 - Requester selection box
        requestor_options = ["Unspecified",
                             "VC",
                             "GE",
                             "LK"]
        self.elements.append(new_combo_element(requestor_options,
                                               "Person starting cycle",
                                               self.requestor_box_activated))

        # 10 - Read button
        self.elements.append(new_button_element(
            "Read Cell",
            "Read Voltage of Connected Cell",
            self.button_read
        ))

        # 11 - Start button
        self.elements.append(new_button_element(
            "Start",
            "Start Cycle",
            self.button_start
        ))

        # 12 - Pause button
        self.elements.append(new_button_element(
            "Pause",
            "Pause Cycle",
            self.button_pause
        ))

        # 13 - Resume button
        self.elements.append(new_button_element(
            "Resume",
            "Resume Cycle",
            self.button_resume
        ))

        # 14 - Stop button
        self.elements.append(new_button_element(
            "Stop",
            "Stop Cycle",
            self.button_stop
        ))

        # 15 Cell Status
        self.elements.append(QLabel())
        self.elements[-1].setStatusTip("Cell status")

        QMetaObject.connectSlotsByName(self)

    # Begin Button Press Definitions
    def button_auto_fill(self):
        self.threadpool.start(workers.AutoFill(self))
        logging.debug("AutoFill Pressed")

    def button_read(self):
        logging.debug("Read Pressed")
        worker = workers.Read(self)
        worker.signals.alert.connect(self.post_message)
        self.threadpool.start(worker)

    def button_start(self):
        logging.debug("Start Pressed")
        worker = workers.Control(self, "start", self.scripts)
        worker.signals.status.connect(self.post_feedback)
        self.threadpool.start(worker)

    def button_pause(self):
        logging.debug("Pause Pressed")
        worker = workers.Control(self, "pause", self.scripts)
        worker.signals.status.connect(self.post_feedback)
        self.threadpool.start(worker)

    def button_resume(self):
        logging.debug("Resume Pressed")
        worker = workers.Control(self, "resume", self.scripts)
        worker.signals.status.connect(self.post_feedback)
        self.threadpool.start(worker)

    def button_stop(self):
        logging.debug("Stop Pressed")
        worker = workers.Control(self, "stop", self.scripts)
        worker.signals.status.connect(self.post_feedback)
        self.threadpool.start(worker)

    # Begin Signal Response Definitions

    def post_message(self, status):
        msg = QMessageBox()
        msg.setText(status)
        msg.exec_()

    def post_status(self, status, channel):
        channel.elements[-1].setText(status)

    def post_feedback(self, status, channel):
        channel.elements[-1].setText(status)

    # Begin Attribute Assignment Definitions

    def script_box_activated(self, text):
        """Sets object's script to one selected in dropdown"""
        self.attributes["script_title"] = text

    def package_box_activated(self, text):
        """Sets object's package type to one selected in dropdown"""
        self.attributes["package"] = text

    def cell_box_activated(self, text):
        """Sets object's cell type to one selected in dropdown"""
        self.attributes["type"] = text

    def requestor_box_activated(self, text):
        """Sets object's requestor to one selected in dropdown"""
        self.attributes["requestor"] = text

    def set_id(self, text):
        """Set object identification from text box"""
        self.attributes["id"] = text

    def set_comment(self, text):
        """Set object comment from text box"""
        self.attributes["comment"] = text

    def set_path(self, text):
        """Set object path from text box"""
        self.attributes["path"] = text

    def set_mass(self, text):
        """Set object mass from text box"""
        self.attributes["mass"] = text

    def set_protocol(self, text):
        """Set object protocol from text box"""
        self.attributes["protocol_name"] = text

    def paintEvent(self, event):
        style_option = QStyleOption()
        style_option.initFrom(self)
        painter = QPainter(self)
        style = self.style()
        style.drawPrimitive(QStyle.PE_Widget, style_option, painter, self)
