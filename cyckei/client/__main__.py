"""
Methods that controls the cykei client.
Controls communication and initializes the MainWindow.
"""

import json
import sys
import logging

from PySide2.QtWidgets import QApplication
from os.path import expanduser
from pkg_resources import require, DistributionNotFound

from cyckei.client.window import MainWindow


def main():
    """Initializes server and window"""

    try:
        version = require("cyckei")[0].version
    except DistributionNotFound:
        version = "(unpackaged)"

    print("Welcome to Cyckei Client version {}.".format(version))

    # Load configuration
    record_dir = expanduser("~") + "/cyckei"
    config = json.load(open(record_dir + "/config.json", "r"))
    config["path"] = record_dir

    # Start logging
    log_file = "{}/client.log".format(record_dir)
    logging.basicConfig(filename=log_file, level=config["verbosity"],
                        format='%(asctime)s %(message)s')
    logging.info("--- Client started.")

    app = QApplication(sys.argv)
    app.setStyle("fusion")
    window = MainWindow(config)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
