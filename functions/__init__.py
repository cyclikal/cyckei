import os
import sys

from PySide2.QtWidgets import QMessageBox

from functions.gui import message, button, combo_box, \
     label, line_edit, feedback, action

orange = "#f05f40"
grey = "#a6a6a6"

Question = QMessageBox.Question
Information = QMessageBox.Information
Warning = QMessageBox.Warning
Critical = QMessageBox.Critical


def find_path(path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, path)
    local = os.path.join(os.path.abspath('.'), path)
    if os.path.exists(local):
        return local
    return os.path.join(os.path.abspath('..'), path)


def not_none(value):
    """Sets a None value to "None" string"""
    return "None" if value is None else str(value)
