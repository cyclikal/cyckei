# from subprocess import Popen, DEVNULL
from threading import Thread
import sys

from PySide2.QtWidgets import QApplication
from PySide2.QtGui import QIcon

from client import __main__ as client
from server import __main__ as server


def main():
    # TODO: Pass version number
    version = "dev"

    print("\nWelcome to Cyckei {}!".format(version))

    app = QApplication(sys.argv)
    app.setStyle("fusion")
    app.setQuitOnLastWindowClosed(False)
    app.setWindowIcon(QIcon("client/res/cyckei.png"))

    server.main()
    client.main(app)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
