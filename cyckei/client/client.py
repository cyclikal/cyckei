
"""
Methods that controls the cykei client.
Controls communication and initializes the MainWindow.
"""

import json
import sys
import logging
import traceback

from PySide2.QtCore import QThread
from PySide2.QtWidgets import QApplication
from PySide2.QtGui import QIcon

from os.path import expanduser

from .window import MainWindow


def main(app):
    """Initializes server and window"""
    print("Starting Client.")

    # Load configuration
    record_dir = expanduser("~") + "/cyckei"
    config = json.load(open(record_dir + "/config.json", "r"))
    config["path"] = record_dir

    # Start logging
    log_file = "{}/client.log".format(record_dir)
    logging.basicConfig(filename=log_file, level=config["verbosity"],
                        format='%(asctime)s %(message)s')
    sys.excepthook = handler
    logging.info("--- Client started.")

    window = MainWindow(config)
    window.show()

    sys.exit(app.exec_())


def handler(type, value, tb):
    logging.exception(traceback.format_exception(type, value, tb))
