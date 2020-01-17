"""Main window for the cyckei client."""

import logging
import sys

from PySide2.QtWidgets import QApplication, QMainWindow, QTabWidget
from PySide2.QtCore import QThreadPool

from cyckei.functions import gui
from .script_editor import ScriptEditor
from .log_viewer import LogViewer

logger = logging.getLogger('cyckei')


def main(config):
    """
    Begins execution of Cyckei.

    Args:
        record_dir: Optional path to recording directory.
    Returns:
        Result of app.exec_(), Qt's main event loop.

    """

    logger.info("Initializing Explorer version {}".format(
        config["version"]))

    # Create QApplication
    logger.debug("Creating QApplication")
    app = QApplication(sys.argv)
    gui.style(app, "icon-explorer.png", gui.teal)

    # Create Client
    logger.debug("Creating Window")
    main_window = MainWindow(config)
    main_window.show()

    return app.exec_()


class MainWindow(QMainWindow):
    """Main Window class which is and sets up itself"""
    # Setup main windows
    def __init__(self, config):
        super(MainWindow, self).__init__()
        # Set basic window properties
        self.setWindowTitle("Cyckei Explorer")
        self.config = config
        self.resize(1100, 600)

        resource = {}
        # Setup ThreadPool
        resource["threadpool"] = QThreadPool()
        self.threadpool = resource["threadpool"]
        logger.info("Multithreading set with maximum {} threads".format(
            resource["threadpool"].maxThreadCount()
        ))

        # # Load scripts
        # resource["scripts"] = ScriptList(config)

        # Create menu and status bar
        self.status_bar = self.statusBar()

        resource["tabs"] = QTabWidget(self)
        self.setCentralWidget(resource["tabs"])

        resource["tabs"].addTab(ScriptEditor(config, resource), "Scripts")
        resource["tabs"].addTab(LogViewer(config, resource), "Results")
