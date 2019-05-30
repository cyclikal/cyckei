"""Run tests to verify that script is valid and contains only legal commands"""

import json

from PySide2.QtWidgets import QMessageBox


def check(protocol, server):
    """Initiates checking tests"""
    passed, msg = legal_test(protocol)
    if not passed:
        return end_false(msg)
    passed, msg = run_test(protocol, server)
    if not passed:
        return end_false(msg)
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


def run_test(protocol, server):
    """Checks if server can load script successfully"""
    packet = prepare_json(protocol)
    response = server.send(packet)["response"]
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
