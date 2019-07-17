from PySide2.QtWidgets import QMessageBox
import os
import sys


def post_message(text):
    msg = QMessageBox()
    msg.setText(text)
    msg.exec_()


def find_path(path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, path)
    return os.path.join(os.path.abspath('.'), path)
