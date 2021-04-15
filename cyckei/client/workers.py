import json
import logging
import os
import tempfile
import time
import sys
from datetime import date, datetime

from PySide2.QtCore import QRunnable, Slot, Signal, QObject

from .socket import Socket
from cyckei.functions import func

logger = logging.getLogger('cyckei_client')


def prepare_json(channel, function, protocol, temp):
    """Populates a new package with channel data and returns it

    Args:
        channel (ChannelWidget): Channel object that stores info about itself.
        function (str): Used by the server when determining what action to take.
        protocol (str): A protocol for the server to execute. 
        temp (bool): True records in a temporary file, false records to the proper record directory.

    Returns:
        dict: A package populated with the protocol and info about the specified channel.
    """
    with open(func.asset_path("default_packet.json")) as file:
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
        dir = os.path.join(channel.attributes["record_folder"],
                           str(date.today().year))

        os.makedirs(dir, exist_ok=True)

    if channel.settings[2].text() == "":
        channel.attributes["path"] = datetime.now().strftime(
            '%m-%d_%H-%M-%S')
    packet["kwargs"]["meta"]["path"] \
        = os.path.join(dir, channel.attributes["path"])

    # Force the file extension to be .pyb by simply adding it (not replacing)
    if not packet["kwargs"]["meta"]["path"].lower().endswith('.pyb'):
        packet["kwargs"]["meta"]["path"] += '.pyb'

    return packet

class Signals(QObject):
    """Object used by other objects to alert the user to changes, statuses, etc.
    """

    alert = Signal(object)
    status = Signal(object, object)
    info = Signal(object)

class Ping(QRunnable):
    """Object used to check for an active server.

    Attributes:
        config (dict): Holds Cyckei launch settings.
        signals (Signals): Used for gui signals. Shows the server's response.
    """

    def __init__(self, config):
        """Inits Ping with signals and config.

        Args:
            config (dict): Holds Cyckei launch settings.
        """
        super(Ping, self).__init__()
        self.signals = Signals()
        self.config = config

    @Slot()
    def run(self):
        """[summary]"""
        response = Socket(self.config).ping()
        self.signals.alert.emit(response)

class UpdateStatus(QRunnable):
    """Updates the status below the controls, shown after contacting server
    
    Attributes:
        channels (list): A list of all of the ChannelWidget objects to be updated.
        config (dict): Holds Cyckei launch settings.
    """

    def __init__(self, channels, config):
        """Inits UpdateStatus with channles and config

        Args:
            channels (list): A list of all of the ChannelWidget objects to be updated.
            config (dict): Holds Cyckei launch settings.
        """
        super(UpdateStatus, self).__init__()
        self.channels = channels
        self.config = config

    @Slot()
    def run(self):
        """Goes through the channels list and sets the gui status text depending on server response from info_all query."""
        info_all = Socket(self.config).info_all_channels()

        for channel in self.channels:
            if type(info_all) is not dict:
                channel.status.setText("No Response")
                pass
            try:
                info = info_all[str(channel.attributes["channel"])]
                status = (func.not_none(info["status"])
                          + " - " + func.not_none(info["state"])
                          + " | C: " + func.not_none(info["current"])
                          + ", V: " + func.not_none(info["voltage"]))

                # if info["status"] == "started":
                #    channel.divider.setStyleSheet(
                #        "background-color: {}".format(gui.orange))
                # else:
                #    channel.divider.setStyleSheet(
                #        "background-color: {}".format(gui.gray))

            except (TypeError, KeyError) as error:
                logger.error(f"Could not get status from server: {error}")
                logger.error(
                    f"Contents of info_all for diagnosis: {info_all}")
                status = "Could not get status!"

            #    channel.divider.setStyleSheet(
            #        "background-color: {}".format(gui.gray))
            logger.debug("Updating channel {} with status {}".format(
                         channel.attributes["channel"], status))
            try:
                channel.status.setText(status)
            except TypeError as error:
                logger.error(f"Set status to '{status}', failed with: {error}")
                channel.status.setText("No Status Update, Check Log")

            except RuntimeError as error:
                print(f"Looks like QTimer ran after Cyckei closed: {error}")
                sys.exit()

class Read(QRunnable):
    """Object used in reading cell information from the server.
    
    Attributes:
        channel (ChannelWidget): Channel object that stores info about itself.
        config (dict): Holds Cyckei launch settings.
        signals (Signals): Used for gui signals. Shows the server's response.
    """

    def __init__(self, config, channel):
        """Inits Read with channel, config, and signals.

        Args:
            channel (ChannelWidget): Channel object that stores info about itself.
            config (dict): Holds Cyckei launch settings.
        """
        super(Read, self).__init__()
        self.channel = channel
        self.config = config
        self.signals = Signals()

    @Slot()
    def run(self):
        """Tell channel to Rest() long enough to get voltage reading on cell."""
        status = Socket(self.config).info_channel(
            self.channel.attributes["channel"])["response"]
        if status["status"] == "available":
            script = """Rest(ends=(("time", ">", "::5"),))"""
            Control(self.config, self.channel, "start", script=script,
                    temp=True).run()
            time.sleep(3)
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
    """Object for storing a script and sendng it to the server.
    
    Attributes:
        channel (ChannelWidget): Channel object that stores info about itself.
        command (str): Used by Control in determining which actions to take.
        config (dict): Holds Cyckei launch settings.
        script (str): The script for the server to execute. Passed in or taken from the channel.
        signals (Signals): Used for gui signals. Shows the server's response.
        temp (bool): Indicates whether recording should be done in temporary files (true) or not (false)
    """

    def __init__(self, config, channel, command, script=None, temp=False):
        """Inits Control with channel, command, config, script, signals, and temp.

        Args:
            channel (ChannelWidget): Channel object that stores info about itself. 
            command (str): Used by Control in determining which actions to take.
            config (dict): Holds Cyckei launch settings.
            script (str, optional): The script for the server to execute. Defaults to None.
            temp (bool, optional): Indicates whether recording should be done in temporary files (true) or not (false). Defaults to False.
        """
        # TODO: Make sure read passes correct script
        super(Control, self).__init__()
        self.channel = channel
        if script is not None:
            self.script = script
        elif self.channel.attributes['script_content'] is not None:
            self.script = self.channel.attributes['script_content']
        self.config = config
        self.command = command
        self.signals = Signals()
        self.temp = temp

    @Slot()
    def run(self):
        """Calls for a viability check on the loaded script and then sends it to the server."""
        try:
            if self.script is None:
                self.script = None
        except AttributeError:
            self.script = None

        if self.command == "start" and self.script is not None:
            script_ok, msg = Check(self.config, self.script).run()
            if script_ok is False:
                self.signals.status.emit("Script Failed", self.channel)
                logger.warning(msg)
                return

        packet =  json(self.channel, self.command,
                              self.script, self.temp)
        response = Socket(self.config).send(packet)["response"]
        self.signals.status.emit(response, self.channel)

class Check(QRunnable):
    """Object used for testing whether a certain protocol can be run.

    Attributes:
        protocol (str): The protocol being checked for legality.
        config (dict): Holds Cyckei launch settings.
        signals (Signals): Used for gui signals. Shows the server's response.
    """

    def __init__(self, config, protocol):
        """Inits Check with config, protocol, and signals.

        Args:
            config (dict): Holds Cyckei launch settings.
            protocol (str): The protocol being checked for legality.
        """
        super(Check, self).__init__()
        self.protocol = protocol
        self.config = config
        self.signals = Signals()

    @Slot()
    def run(self):
        """Runs the tests for checking the script.

        Returns:
            bool: True if protocol is legal and loaded, False otherwise.
            str: The message that goes with the legality/load test results.
        """
        passed, msg = self.legal_test(self.protocol)
        if not passed:
            self.signals.status.emit(passed, msg)
            return passed, msg
        passed, msg = self.run_test(self.protocol)
        self.signals.status.emit(passed, msg)
        return passed, msg

    def legal_test(self, protocol):
        """Checks if script only contains valid commands.

        Args:
            protocol (str): The protocol being checked for legality.

        Returns:
            bool: True if protocol is legal, False otherwise.
            str: The message that goes with the legality test results.
        """
        conditions = ["#",
                      "for",
                      "AdvanceCycle()",
                      "CCCharge(",
                      "CCDischarge(",
                      "CVCharge(",
                      "CVDischarge(",
                      "Rest(",
                      "Sleep("]
        protocol = protocol.replace(" ", "")
        protocol = protocol.replace("\t", "")
        if protocol == "":
            return False, "An empty file can not be run."

        for line in protocol.splitlines():

            valid = False
            for condition in conditions:
                if line.startswith(condition) or not line:
                    valid = True
                    break
            if not valid:
                return False, "Illegal command: \"" + line + "\"."

        return True, "Passed"

    def run_test(self, protocol):
        """Checks if server can load script successfully.

        Args:
            protocol (str): The protocol being checked for server loading.

        Returns:
            bool: True if protocol is loaded, False otherwise.
            str: The message that goes with the load test results.
        """
        packet = self.prepare_json(protocol)
        response = Socket(self.config).send(packet)["response"]
        if response == "Passed":
            return True, "Passed"
        return False, \
            "Server failed to run script. Error: \"{}\".".format(response)

    def prepare_json(self, protocol):
        """Packages protocol in json dict to send to server.

        Args:
            protocol (str): The protocol being sent to the server.

        Returns:
            dict: The protocol packaged with an indication that this is a test for the server.
        """
        packet = json.load(
            open(func.asset_path("default_packet.json")))

        packet["function"] = "test"
        packet["kwargs"]["protocol"] = protocol

        return packet
