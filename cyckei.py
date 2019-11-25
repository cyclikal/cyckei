import sys

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QApplication

import functions
import functions.configuration
import functions.gui
from applet import applet
from client import client


def main(record_dir="Cyckei"):
    """
    Begins execution of Cyckei.

    Args:
        record_dir: Optional path to recording directory.
    Returns:
        Result of app.exec_(), Qt's main event loop.

    """
    try:
        config, record_dir = functions.configuration.read_config(record_dir)
        logger = functions.configuration.setup_logging('cyckei', record_dir, config)

    except Exception as e:
        print("An error occured before logging began.")
        print(e)

    logger.info(f"cyckei.main: Initializing Cyckei version {config['version']}")
    logger.debug("cyckei.main: Logging at debug level")

    # Create QApplication
    logger.debug("cyckei.main: Creating QApplication")
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setWindowIcon(QIcon(functions.find_path("assets/cyckei.png")))

    # Create Applet
    logger.debug("cyckei.main: Creating Applet")
    applet_object = applet.Icon(config)
    applet_object.show()

    # Create Client
    logger.debug("cyckei.main: Creating Initial Client")
    main_window = client.MainWindow(config)
    main_window.show()

    return app.exec_()


if __name__ == "__main__":
    print("Starting Cyckei...")
    sys.exit(main())
