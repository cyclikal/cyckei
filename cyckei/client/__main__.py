
"""
Methods that controls the cykei client.
Controls communication and initializes the MainWindow.
"""

import json
import sys
import logging

from pkg_resources import resource_filename

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QApplication
from os.path import expanduser

from .window import MainWindow


def main():
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
    logging.info("--- Client started.")

    app = QApplication(sys.argv)
    app.setStyle("fusion")
    app.setWindowIcon(QIcon(resource_filename(
            "cyckei.client",
            "res/cyckei.png")))

    window = MainWindow(config)
    window.show()

    return app.exec_()


if __name__ == "__main__":
    main()
