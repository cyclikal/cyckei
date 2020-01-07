import logging

from PySide2.QtCore import QRunnable, Slot, Signal, QObject


logger = logging.getLogger('cyckei')


class Signals(QObject):
    alert = Signal(object)
    status = Signal(object, object)
    info = Signal(object)


class Control(QRunnable):
    """Update json and send "start" function to server"""
    def __init__(self, config, channel, command, script=None, temp=False):
        # TODO: Make sure read passes correct script
        super(Control, self).__init__()

    @Slot()
    def run(self):
        print("Code Not Written")
