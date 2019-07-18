import json
import logging
from os.path import exists
from os import makedirs
from datetime import date

from PySide2.QtCore import QRunnable, Slot, Signal, QObject

from .socket import Socket
import functions as func


def send(json):
    """Sends json to server and updates status with response"""
    # TODO: Load info from config
    resp = Socket("tcp://localhost", 5556).send(json)["response"]
    logging.info(resp)
    return resp


def prepare_json(channel, function, scripts):
    """Sets the channel's json script to current values"""
    protocol = scripts.get_script_by_title(
        channel.attributes["script_title"]).content
    json_packet = json.load(open(func.find_path("assets/defaultJSON.json")))

    json_packet["function"] = function
    json_packet["kwargs"]["channel"] = channel.attributes["channel"]
    json_packet["kwargs"]["meta"]["cellid"] = channel.attributes["id"]
    json_packet["kwargs"]["meta"]["comment"] = channel.attributes["comment"]
    json_packet["kwargs"]["meta"]["package"] = channel.attributes["package"]
    json_packet["kwargs"]["meta"]["cell_type"] = channel.attributes["type"]
    temp_path = (
        channel.attributes["record_folder"]
        + "/"
        + str(date.today())
    )
    if not exists(temp_path):
        makedirs(temp_path)
    json_packet["kwargs"]["meta"]["path"] = (
        temp_path
        + "/"
        + channel.attributes["path"]
    )
    json_packet["kwargs"]["meta"]["mass"] = channel.attributes["mass"]
    json_packet["kwargs"]["meta"]["protocol_name"]\
        = channel.attributes["script_title"]
    json_packet["kwargs"]["meta"]["requester"]\
        = channel.attributes["requestor"]
    json_packet["kwargs"]["meta"]["channel"] = channel.attributes["channel"]
    json_packet["kwargs"]["meta"]["protocol"] = protocol
    json_packet["kwargs"]["protocol"] = protocol

    return json_packet


class Signals(QObject):
    # TODO: Standardize signals and alerts
    alert = Signal(object)
    status = Signal(object, object)


class Ping(QRunnable):
    def __init__(self):
        super(Ping, self).__init__()
        self.signals = Signals()

    @Slot()
    def run(self):
        # TODO: Load info from config
        response = Socket("tcp://localhost", 5556).ping()
        self.signals.alert.emit(response)


class UpdateStatus(QRunnable):
    """Update status shown below controls by contacting server"""
    def __init__(self, channel):
        super(UpdateStatus, self).__init__()
        self.channel = channel
        self.signals = Signals()

    @Slot()
    def run(self):
        # TODO: Utilize configuration
        info_channel = Socket("tcp://localhost", 5556).info_channel(
            self.channel.attributes["channel"])["response"]
        channel_status = Socket("tcp://localhost", 5556).channel_status(
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
        self.signals.status.emit(status, self.channel)


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
    def __init__(self, channel):
        super(Read, self).__init__()
        self.channel = channel
        self.signals = Signals()

    @Slot()
    def run(self):
        package = json.load(open(func.find_path("assets/defaultJSON.json")))
        package["function"] = "start"
        package["kwargs"]["channel"] = self.channel.attributes["channel"]
        package["kwargs"]["meta"]["path"] = (
            self.channel.attributes["record_folder"]
            + "/{}.temp".format(self.channel.attributes["channel"])
        )
        package["kwargs"]["protocol"] = """Rest()"""
        Socket("tcp://localhost", 5556).send(package)

        info_channel = Socket("tcp://localhost", 5556).info_channel(
            self.channel.attributes["channel"])["response"]
        try:
            status = ("Voltage of cell: "
                      + func.not_none(info_channel["voltage"]))
        except Exception:
            status = "Could not read cell voltage."

        package["function"] = "stop"
        Socket("tcp://localhost", 5556).send(package)

        self.signals.status.emit(status, self.channel)


class Control(QRunnable):
    """Update json and send "start" function to server"""
    def __init__(self, channel, command, scripts):
        super(Control, self).__init__()
        self.channel = channel
        self.command = command
        self.scripts = scripts
        self.signals = Signals()

    @Slot()
    def run(self):
        if self.command == "start":
            script_ok, msg = Check(self.scripts.get_script_by_title(
                    self.channel.attributes["script_title"]).content).run()
            if script_ok is False:
                self.signals.status.emit("Script Check Failed", self.channel)
                return

        response = send(prepare_json(self.channel, self.command, self.scripts))
        self.signals.status.emit(response, self.channel)


class Check(QRunnable):
    def __init__(self, protocol):
        super(Check, self).__init__()
        self.protocol = protocol
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
        response = send(packet)
        if response == "Passed":
            return True, "Passed"
        return (False,
                "Server failed to run script. Error: \"{}\".".format(response))

    def prepare_json(self, protocol):
        """create json to send to server"""
        json_packet = json.load(
            open(func.find_path("assets/defaultJSON.json")))

        json_packet["function"] = "test"
        json_packet["kwargs"]["protocol"] = protocol

        return json_packet
