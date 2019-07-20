import json
import logging
import time
import os
from datetime import date

from PySide2.QtCore import QRunnable, Slot, Signal, QObject

from .socket import Socket
import functions as func


def prepare_json(channel, function, scripts):
    """Sets the channel's json script to current values"""
    protocol = scripts.by_title(
        channel.attributes["protocol_name"]).content
    packet = json.load(open(func.find_path("assets/default_packet.json")))

    packet["function"] = function
    packet["kwargs"]["channel"] = channel.attributes["channel"]
    packet["kwargs"]["protocol"] = protocol
    packet["kwargs"]["meta"] = channel.attributes
    packet["kwargs"]["meta"]["protocol"] = protocol

    dir = os.path.join(channel.attributes["record_folder"],
                       str(date.today()))
    os.makedirs(dir, exist_ok=True)
    packet["kwargs"]["meta"]["path"] \
        = os.path.join(dir, channel.attributes["path"])

    return packet


class Signals(QObject):
    # TODO: Standardize signals and alerts
    alert = Signal(object)
    status = Signal(object, object)
    info = Signal(object)


class Ping(QRunnable):
    def __init__(self, config):
        super(Ping, self).__init__()
        self.port = port
        self.address = address
        self.signals = Signals()
        self.config = config

    @Slot()
    def run(self):
        # TODO: Load info from config
        response = Socket(self.config).ping()
        self.signals.alert.emit(response)


class UpdateStatus(QRunnable):
    """Update status shown below controls by contacting server"""
    def __init__(self, channel, config):
        super(UpdateStatus, self).__init__()
        self.channel = channel
        self.port = port
        self.address = address
        self.signals = Signals()
        self.config = config

    @Slot()
    def run(self):
        info_channel = Socket(self.config).info_channel(
            self.channel.attributes["channel"])["response"]
        channel_status = Socket(self.config).channel_status(
            self.channel.attributes["channel"])["response"]
        try:
            status = (channel_status
                      + " - " + func.not_none(info_channel["state"])
                      + " | C: " + func.not_none(info_channel["current"])
                      + ", V: " + func.not_none(info_channel["voltage"]))
        except TypeError:
            status = info_channel
        logging.debug("Updating channel {} with satus {}".format(
            self.channel.attributes["channel"], status))
        self.channel.status.setText(status)
        self.signals.info.emit(channel_status)


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
        package = json.load(open(func.find_path("assets/default_packet.json")))
        package["function"] = "start"
        package["kwargs"]["channel"] = self.channel.attributes["channel"]
        package["kwargs"]["meta"]["path"] = (
            self.channel.attributes["record_folder"]
            + "/{}.temp".format(self.channel.attributes["channel"])
        )
        # TODO: prevent current cycle overwrite
        package["kwargs"]["protocol"] = """Rest()"""
        Socket(self.config).send(package)

        time.sleep(1)
        info_channel = Socket(self.config).info_channel(
            self.channel.attributes["channel"])["response"]
        try:
            status = ("Voltage of cell: "
                      + func.not_none(info_channel["voltage"]))
        except Exception:
            status = "Could not read cell voltage."

        package["function"] = "stop"
        Socket(self.config).send(package)

        self.signals.status.emit(status, self.channel)


class Control(QRunnable):
    """Update json and send "start" function to server"""
    def __init__(self, config, channel, command, scripts):
        super(Control, self).__init__()
        self.channel = channel
        self.config = config
        self.command = command
        self.scripts = scripts
        self.port = port
        self.address = address
        self.signals = Signals()

    @Slot()
    def run(self):
        if self.command == "start":
            script_ok, msg = Check(self.config, self.scripts.by_title(
                self.channel.attributes["protocol_name"]).content).run()
            if script_ok is False:
                self.signals.status.emit("Script Check Failed", self.channel)
                return

        response = Socket(self.config).send(prepare_json(
            self.channel, self.command, self.scripts))["response"]
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
