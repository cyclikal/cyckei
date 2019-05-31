"""
Methods that controls the cykei client.
Controls communication and initializes the MainWindow.
"""

import json
import sys
import logging

from PySide2.QtWidgets import QApplication
from os.path import expanduser

from cyckei.client.window import MainWindow
from cyckei.client import scripts
from cyckei.client.client_server import Server


def main():
    """Initializes server and window"""

    # Load configuration
    record_dir = expanduser("~") + "/cyckei"
    config = json.load(open(record_dir + "/config.json", "r"))
    config["path"] = record_dir

    # Start logging
    log_file = "{}/client.log".format(record_dir)
    logging.basicConfig(filename=log_file, level=config["verbosity"],
                        format='%(asctime)s %(message)s')
    logging.info("--- Client started.")

    scripts.load_default_scripts(config["path"] + "/scripts")
    server = Server(config["zmq"]["client"]["address"], config["zmq"]["port"])

    app = QApplication(sys.argv)
    window = MainWindow(config, server)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
