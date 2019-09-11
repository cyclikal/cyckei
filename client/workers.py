import json
import logging
import os
import tempfile
import time
from datetime import date

from PySide2.QtCore import QRunnable, Slot, Signal, QObject

from .socket import Socket
import functions as func


def prepare_json(channel, function, protocol, temp):
    """Sets the channel's json script to current values"""
    with open(func.find_path("assets/default_packet.json")) as file:
        packet = json.load(file)

    packet["function"] = function
    for key, value in channel.attributes.items():
        packet["kwargs"]["meta"][key] = value
    packet["kwargs"]["channel"] = channel.attributes["channel"]
    packet["kwargs"]["protocol"] = protocol
    packet["kwargs"]["meta"]["protocol"] = protocol

    if temp:
        dir = tempfile.mkdtemp()
    else:
        # dir = os.path.join(channel.attributes["record_folder"],
        #                   str(date.today()))
        dir = os.path.abspath(channel.attributes["record_folder"])
        os.makedirs(dir, exist_ok=True)

    packet["kwargs"]["meta"]["path"] \
        = os.path.join(dir, channel.attributes["path"])

    return packet


class Signals(QObject):
    alert = Signal(object)
    status = Signal(object, object)
    info = Signal(object)


class Ping(QRunnable):
    def __init__(self, config):
        super(Ping, self).__init__()
        self.signals = Signals()
        self.config = config

    @Slot()
    def run(self):
        response = Socket(self.config).ping()
        self.signals.alert.emit(response)


class UpdateStatus(QRunnable):
    """Update status shown below controls by contacting server"""
    def __init__(self, channels, config):
        super(UpdateStatus, self).__init__()
        self.channels = channels
        self.config = config

    @Slot()
    def run(self):
        info_all = Socket(self.config).info_all_channels()
        for channel in self.channels:
            try:
                info = info_all[channel.attributes["channel"]]
                status = (func.not_none(info["status"])
                          + " - " + func.not_none(info["state"])
                          + " | C: " + func.not_none(info["current"])
                          + ", V: " + func.not_none(info["voltage"]))
            except (TypeError, KeyError):
                status = "Could not get status!"
            logging.debug("Updating channel {} with satus {}".format(
                channel.attributes["channel"], status))
            channel.status.setText(status)
            # Make cleaner
            try:
                if info["status"] == "started":
                    channel.divider.setStyleSheet(
                        "background-color: {}".format(func.orange))
                else:
                    channel.divider.setStyleSheet(
                        "background-color: {}".format(func.grey))
            except UnboundLocalError:
                channel.divider.setStyleSheet(
                    "background-color: {}".format(func.grey))


class AutoFill(QRunnable):
    """Fill log text with value derived from cell identification"""
    def __init__(self, channel):
        super(AutoFill, self).__init__()
        self.channel = channel

    @Slot()
    def run(self):
        if self.channel.settings[2].text():
            self.channel.settings[3].setText(
                "{}A.pyb".format(self.channel.settings[2].text()))


class Read(QRunnable):
    """Tell channel to Rest() long enough to get voltage reading on cell"""
    def __init__(self, config, channel):
        super(Read, self).__init__()
        self.channel = channel
        self.config = config
        self.signals = Signals()

    @Slot()
    def run(self):
        status = Socket(self.config).info_channel(
            self.channel.attributes["channel"])["response"]
        if status["status"] == "available":
            script = """Rest(ends=(("time", ">", "::3"),))"""
            Control(self.config, self.channel, "start", script=script,
                    temp=True).run()
            time.sleep(1)
            info_channel = Socket(self.config).info_channel(
                self.channel.attributes["channel"])["response"]
            try:
                status = ("Voltage of cell: "
                          + func.not_none(info_channel["voltage"]))
            except Exception:
                status = "Could not read cell voltage."
        else:
            status = "Cannot read voltage during cycle"

        self.signals.status.emit(status, self.channel)


class Control(QRunnable):
    """Update json and send "start" function to server"""
    def __init__(self, config, channel, command, scripts=None,
                 script=None, temp=False):
        super(Control, self).__init__()
        self.channel = channel
        self.config = config
        self.command = command
        self.scripts = scripts
        self.script = script
        self.signals = Signals()
        self.temp = temp

    @Slot()
    def run(self):
        if self.command == "start" and self.script is None:
            self.script = self.scripts.by_title(
                self.channel.attributes["protocol_name"]).content
            script_ok, msg = Check(self.config, self.script).run()
            if script_ok is False:
                self.signals.status.emit("Script Failed", self.channel)
                return

        packet = prepare_json(self.channel, self.command,
                              self.script, self.temp)
        response = Socket(self.config).send(packet)["response"]
        self.signals.status.emit(response, self.channel)


class Check(QRunnable):
    def __init__(self, config, protocol):
        super(Check, self).__init__()
        self.protocol = protocol
        self.config = config
        self.signals = Signals()

    @Slot()
    def run(self):
        """Initiates checking tests"""
        passed, msg = self.legal_test(self.protocol)
        if not passed:
            self.signals.status.emit(passed, msg)
            return passed, msg
        passed, msg = self.run_test(self.protocol)
        self.signals.status.emit(passed, msg)
        return passed, msg

    def legal_test(self, protocol):
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

    def run_test(self, protocol):
        """Checks if server can load script successfully"""
        packet = self.prepare_json(protocol)
        response = Socket(self.config).send(packet)["response"]
        if response == "Passed":
            return True, "Passed"
        return False, \
            "Server failed to run script. Error: \"{}\".".format(response)

    def prepare_json(self, protocol):
        """create json to send to server"""
        packet = json.load(
            open(func.find_path("assets/default_packet.json")))

        packet["function"] = "test"
        packet["kwargs"]["protocol"] = protocol

        return packet
