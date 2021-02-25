import logging

from PySide2.QtCore import QRunnable, Slot, Signal, QObject


logger = logging.getLogger('cyckei')


class Signals(QObject):
    alert = Signal(object)
    status = Signal(object, object)
    info = Signal(object)


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

        return True, "Passed 'Legal Arguments' Test"


class Control(QRunnable):
    """Update json and send "start" function to server"""
    def __init__(self, config, channel, command, script=None, temp=False):
        # TODO: Make sure read passes correct script
        super(Control, self).__init__()

    @Slot()
    def run(self):
        print("Code Not Written")
