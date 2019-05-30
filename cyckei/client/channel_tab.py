"""
Widget that controls a single channnel.
Listed in the channel tab of the main window.
"""

import json
import logging
from os.path import exists
from os import remove
from os import makedirs
from datetime import date


from PySide2.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, \
    QLineEdit, QPushButton, QLabel, QMessageBox, QScrollArea, QStyleOption, \
    QStyle
from PySide2.QtCore import QMetaObject, QTimer
from PySide2.QtGui import QPainter

from cyckei.client import scripts
from cyckei.client import check


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
    combo_box = QComboBox()
    combo_box.addItems(items)
    combo_box.setStatusTip(status)
    combo_box.activated[str].connect(connect)
    return combo_box


def new_text_element(label, status, connect):
    """Creates text edit field with given information"""
    text = QLineEdit()
    text.setPlaceholderText(label)
    text.setStatusTip(status)
    text.textChanged.connect(connect)
    return text


class ChannelTab(QWidget):
    def __init__(self, config, server):
        """Setup each channel widget and place in QVBoxlayout"""
        QWidget.__init__(self)

        layout = QHBoxLayout(self)

        scroll_area = QScrollArea()
        layout.addWidget(scroll_area)
        scroll_area.setWidgetResizable(True)
        scroll_contents = QWidget()
        scroll_area.setWidget(scroll_contents)
        rows = QVBoxLayout(scroll_contents)
        rows.setSpacing(0)

        self.channels = []
        for channel in config["channels"]:
            self.channels.append(ChannelWidget(channel["channel"],
                                 server,
                                 config["path"] + "/tests"))
            rows.addWidget(self.channels[-1])

    def paintEvent(self, event):
        style_option = QStyleOption()
        style_option.initFrom(self)
        painter = QPainter(self)
        style = self.style()
        style.drawPrimitive(QStyle.PE_Widget, style_option, painter, self)


class ChannelWidget(QWidget):
    """Controls and stores information for a given channel"""

    def __init__(self, channel, server, record_folder):
        super().__init__()
        # Assignments
        self.server = server
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

        self.setMinimumSize(800, 54)

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
        self.json = json.load(open("resources/defaultJSON.json"))

        # Update status
        self.update_status()

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

        # 1 - Script selection box
        available_scripts = []
        if scripts.SCRIPTS:
            self.attributes["script_title"] = scripts.SCRIPTS[0].title
            for script in scripts.SCRIPTS:
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
            self.auto_fill
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

        # 10 - Start button
        self.elements.append(new_button_element(
            "Check Cell",
            "Check Status of Connected Cell",
            self.check
        ))

        # 11 - Start button
        self.elements.append(new_button_element(
            "Start",
            "Start Cycle",
            self.start
        ))

        # 12 - Pause button
        self.elements.append(new_button_element(
            "Pause",
            "Pause Cycle",
            self.pause
        ))

        # 13 - Resume button
        self.elements.append(new_button_element(
            "Resume",
            "Resume Cycle",
            self.resume
        ))

        # 14 - Stop button
        self.elements.append(new_button_element(
            "Stop",
            "Stop Cycle",
            self.stop
        ))

        # 15 Cell Status
        self.elements.append(QLabel())
        self.elements[-1].setStatusTip("Cell status")

        QMetaObject.connectSlotsByName(self)

    def prepare_json(self, function):
        """Sets the channel's json script to current values"""
        protocol = scripts.get_script_by_title(
            self.attributes["script_title"]).content

        self.json["function"] = function
        self.json["kwargs"]["channel"] = self.attributes["channel"]
        self.json["kwargs"]["meta"]["cellid"] = self.attributes["id"]
        self.json["kwargs"]["meta"]["comment"] = self.attributes["comment"]
        self.json["kwargs"]["meta"]["package"] = self.attributes["package"]
        self.json["kwargs"]["meta"]["cell_type"] = self.attributes["type"]
        temp_path = (
            self.attributes["record_folder"]
            + "/"
            + str(date.today())
        )
        if not exists(temp_path):
            makedirs(temp_path)
        self.json["kwargs"]["meta"]["path"] = (
            temp_path
            + "/"
            + self.attributes["path"]
        )
        self.json["kwargs"]["meta"]["mass"] = self.attributes["mass"]
        self.json["kwargs"]["meta"]["protocol_name"] = (
            self.attributes["script_title"]
        )
        self.json["kwargs"]["meta"]["requester"] = self.attributes["requestor"]
        self.json["kwargs"]["meta"]["channel"] = self.attributes["channel"]
        self.json["kwargs"]["meta"]["protocol"] = protocol
        self.json["kwargs"]["protocol"] = protocol

    def update_status(self):
        """Update status shown below controls by contacting server"""
        info_channel = self.server.info_channel(
            self.attributes["channel"]
        )["response"]
        channel_status = self.server.channel_status(
            self.attributes["channel"]
        )["response"]
        try:
            status = (channel_status
                      + " - " + not_none(info_channel["state"])
                      + " | C: " + not_none(info_channel["current"])
                      + ", V: " + not_none(info_channel["voltage"]))
        except TypeError:
            status = info_channel
        self.elements[15].setText(status)
        QTimer.singleShot(1000, self.update_status)

    def start(self):
        """Update json and send "start" function to server"""
        check_true = check.check(
                                 scripts.get_script_by_title(
                                    self.attributes["script_title"]
                                 ).content, self.server)
        if check_true:
            self.prepare_json("start")
            self.send()

    def pause(self):
        """Update json and send "pause" function to server"""
        self.prepare_json("pause")
        self.send()

    def resume(self):
        """Update json and send "resume" function to server"""
        self.prepare_json("resume")
        self.send()

    def stop(self):
        """Update json and send "stop" function to server"""
        self.prepare_json("stop")
        self.send()

    def send(self):
        """Sends json to server and updates status with response"""
        resp = self.server.send(self.json)["response"]
        logging.info(resp)
        self.elements[15].setText(resp)

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

    def auto_fill(self):
        """Fill log text with value derived from cell identification"""
        if self.elements[2].text():
            self.elements[3].setText("{}A.pyb".format(self.elements[2].text()))

    def check(self):
        """Tell channel to Rest() long enough to get voltage reading on cell"""
        package = json.load(open("resources/defaultJSON.json"))
        package["function"] = "start"
        package["kwargs"]["channel"] = self.attributes["channel"]
        package["kwargs"]["meta"]["path"] = (
            self.attributes["record_folder"]
            + "/{}.temp".format(self.attributes["channel"])
        )
        package["kwargs"]["protocol"] = """Rest()"""
        self.server.send(package)

        info_channel = self.server.info_channel(
            self.attributes["channel"])["response"]
        try:
            status = ("Voltage of cell: "
                      + not_none(info_channel["voltage"]))
        except Exception:
            status = "Could not read cell voltage."

        package["function"] = "stop"
        self.server.send(package)

        msg = QMessageBox()
        msg.setText(status)
        msg.setWindowTitle("Cell Status")
        msg.exec_()

        if exists(package["kwargs"]["meta"]["path"]):
            remove(package["kwargs"]["meta"]["path"])

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
