import os
import sys

from functions.gui import message, button, combo_box, \
     label, line_edit, status, feedback


def find_path(path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, path)
    return os.path.join(os.path.abspath('.'), path)


def not_none(value):
    """Sets a None value to "None" string"""
    return "None" if value is None else str(value)
