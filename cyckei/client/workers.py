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
from socket import Socket


def not_none(value):
    """Sets a None value to "None" string"""
    return "None" if value is None else str(value)


def send(json, channel):
    """Sends json to server and updates status with response"""
    # TODO: Load info from config
    socket = Socket("tcp://localhost", 5556)
    resp = socket.send(json)["response"]
    logging.info(resp)
    channel.elements[15].setText(resp)
    socket.socket.close()


def prepare_json(json, channel, function):
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


class Ping(QRunnable):
    def __init__(self):
        super(Ping, self).__init__()

    @Slot()
    def run(self):
        # TODO: Load info from config
        Socket("tcp://localhost", 5556).ping_server()


class UpdateStatus(QRunnable):
    """Update status shown below controls by contacting server"""
    def __init__(self, channel):
        super(UpdateStatus, self).__init__()
        self.channel = channel

    @Slot()
    def run(self):
        socket = Socket("tcp://localhost", 5556)
        while True:
            info_channel = socket.info_channel(
                self.channel.attributes["channel"])["response"]
            channel_status = socket.channel_status(
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
    def __init__(self, channel):
        super(AutoFill, self).__init__()
        self.channel = channel

    @Slot()
    def run(self):
        if self.channel.elements[2].text():
            self.channel.elements[3].setText(
                "{}A.pyb".format(self.elements[2].text()))


class Read(QRunnable):
    """Tell channel to Rest() long enough to get voltage reading on cell"""
    def __init__(self, channel):
        super(Check, self).__init__()
        self.channel = channel

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


class Control(QRunnable):
    """Update json and send "start" function to server"""
    def __init__(self, channel, command):
        super(Control, self).__init__()
        self.channel = channel
        self.command = command

    @Slot()
    def run(self):
        if self.command == "start":
            script_ok = self.threadpool.start(
                check(scripts.get_script_by_title(
                    self.channel.attributes["script_title"]).content))
            if script_ok is False:
                return

        send(
            prepare_json(json, self.channel, self.command),
            self.channel
        )


class Check(QRunnable):
    def __init__(self, protocol):
        super(Control, self).__init__()
        self.protocol = protocol

    @Slot()
    def run(self):
        """Initiates checking tests"""
        passed, msg = self.legal_test(self.protocol)
        if not passed:
            return self.end_false(msg)
        passed, msg = self.run_test(self.protocol)
        if not passed:
            return self.end_false(msg)
        return True

    def legal_test(protocol):
        """Checks if script only contains valid commands"""
        conditions = ["#",
                      "for",
                      "AdvanceCycle()",
                      "CCCharge(",
                      "CCDischarge(",
                      "CVCharge(",
                      "CVDischarge(",
                      "Rest(",
                      "Sleep("]

        for line in protocol.splitlines():
            line = line.replace(" ", "")
            line = line.replace("\t", "")

            valid = False
            for condition in conditions:
                if line.startswith(condition) or not line:
                    valid = True
                    break
            if not valid:
                return False, "Illegal command: \"" + line + "\"."

        return True, "Passed"

    def run_test(protocol):
        """Checks if server can load script successfully"""
        packet = prepare_json(protocol)
        response = send(packet)["response"]
        if response == "Passed":
            return True, "Passed"
        return (False,
                "Server failed to run script. Error: \"{}\".".format(response))

    def end_false(reason):
        """Show message box with error statement and return false"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText("Failed!")
        msg.setInformativeText("Script did not pass the check.")
        msg.setWindowTitle("Check Failed")
        msg.setDetailedText(reason)
        msg.exec_()
        return False

    def prepare_json(protocol):
        """create json to send to server"""
        json_packet = json.load(open("resources/defaultJSON.json"))

        json_packet["function"] = "test"
        json_packet["kwargs"]["protocol"] = protocol

        return json_packet
