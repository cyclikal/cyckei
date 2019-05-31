import json
import logging

from PySide2.QtCore import QRunnable, Slot
from PySide2.QtWidgets import QMessageBox
from os.path import exists
from os import makedirs, remove
from datetime import date
from time import sleep

import scripts
import check


def not_none(value):
    """Sets a None value to "None" string"""
    return "None" if value is None else str(value)


def send(server, json, channel):
    """Sends json to server and updates status with response"""
    resp = server.send(json)["response"]
    logging.info(resp)
    channel.elements[15].setText(resp)


def prepare_json(self, json, channel, function):
    """Sets the channel's json script to current values"""
    protocol = scripts.get_script_by_title(
        channel.attributes["script_title"]).content

    json["function"] = function
    json["kwargs"]["channel"] = channel.attributes["channel"]
    json["kwargs"]["meta"]["cellid"] = channel.attributes["id"]
    json["kwargs"]["meta"]["comment"] = channel.attributes["comment"]
    json["kwargs"]["meta"]["package"] = channel.attributes["package"]
    json["kwargs"]["meta"]["cell_type"] = channel.attributes["type"]
    temp_path = (
        channel.attributes["record_folder"]
        + "/"
        + str(date.today())
    )
    if not exists(temp_path):
        makedirs(temp_path)
    json["kwargs"]["meta"]["path"] = (
        temp_path
        + "/"
        + channel.attributes["path"]
    )
    json["kwargs"]["meta"]["mass"] = channel.attributes["mass"]
    json["kwargs"]["meta"]["protocol_name"]\
        = channel.attributes["script_title"]
    json["kwargs"]["meta"]["requester"]\
        = channel.attributes["requestor"]
    json["kwargs"]["meta"]["channel"] = channel.attributes["channel"]
    json["kwargs"]["meta"]["protocol"] = protocol
    json["kwargs"]["protocol"] = protocol

    return json


class UpdateStatus(QRunnable):
    """Update status shown below controls by contacting server"""
    def __init__(self, channel, server):
        super(UpdateStatus, self).__init__()
        self.channel = channel
        self.server = server

    @Slot()
    def run(self):
        while True:
            info_channel = self.server.info_channel(
                self.channel.attributes["channel"])["response"]
            channel_status = self.server.channel_status(
                self.channel.attributes["channel"])["response"]
            try:
                status = (channel_status
                          + " - " + not_none(info_channel["state"])
                          + " | C: " + not_none(info_channel["current"])
                          + ", V: " + not_none(info_channel["voltage"]))
            except TypeError:
                status = info_channel
            logging.debug("Updating channel {} with satus {}".format(
                self.channel.attributes["channel"], status))
            self.channel.elements[15].setText(status)
            sleep(2)


class AutoFill(QRunnable):
    """Fill log text with value derived from cell identification"""
    def __init__(self, channel, server):
        super(AutoFill, self).__init__()
        self.channel = channel
        self.server = server

    @Slot()
    def run(self):
        if self.channel.elements[2].text():
            self.channel.elements[3].setText(
                "{}A.pyb".format(self.elements[2].text()))


class Check(QRunnable):
    """Tell channel to Rest() long enough to get voltage reading on cell"""
    def __init__(self, channel, server):
        super(Check, self).__init__()
        self.channel = channel
        self.server = server

    @Slot()
    def run(self):
        package = json.load(open("resources/defaultJSON.json"))
        package["function"] = "start"
        package["kwargs"]["channel"] = self.channel.attributes["channel"]
        package["kwargs"]["meta"]["path"] = (
            self.channel.attributes["record_folder"]
            + "/{}.temp".format(self.channel.attributes["channel"])
        )
        package["kwargs"]["protocol"] = """Rest()"""
        self.server.send(package)

        info_channel = self.server.info_channel(
            self.channel.attributes["channel"])["response"]
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


class Start(QRunnable):
    """Update json and send "start" function to server"""
    def __init__(self, channel, server):
        super(Start, self).__init__()
        self.channel = channel
        self.server = server

    @Slot()
    def run(self):
        check_true = check.check(
            scripts.get_script_by_title(
                self.channel.attributes["script_title"]
            ).content, self.server
        )
        if check_true:
            self.send(
                self.server,
                prepare_json(json, self.channel, "start"),
                self.channel
            )


class Pause(QRunnable):
    """Update json and send "pause" function to server"""
    def __init__(self, channel, server):
        super(Pause, self).__init__()
        self.channel = channel
        self.server = server

    @Slot()
    def run(self):
        self.send(
            self.server,
            prepare_json(json, self.channel, "pause"),
            self.channel
        )


class Resume(QRunnable):
    """Update json and send "resume" function to server"""
    def __init__(self, channel, server):
        super(Resume, self).__init__()
        self.channel = channel
        self.server = server

    @Slot()
    def run(self):
        self.send(
            self.server,
            prepare_json(json, self.channel, "resume"),
            self.channel
        )


class Stop(QRunnable):
    """Update json and send "stop" function to server"""
    def __init__(self, channel, server):
        super(Stop, self).__init__()
        self.channel = channel
        self.server = server

    @Slot()
    def run(self):
        self.send(
            self.server,
            prepare_json(json, self.channel, "stop"),
            self.channel
        )
