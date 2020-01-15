"""
Universal GUI Functions
"""
import functools
import os
import sys

from PySide2.QtWidgets import QMessageBox, QPushButton, QComboBox, QLineEdit, \
     QLabel, QAction
from PySide2.QtGui import QIcon

from functions import func

Question = QMessageBox.Question
Information = QMessageBox.Information
Warning = QMessageBox.Warning
Critical = QMessageBox.Critical

orange = "#f05f40"
teal = "#3eb58a"
gray = "#a6a6a6"

css = """
* {
    font-size:16px;
    selection-background-color: {color};
} ChannelWidget {
    border-bottom: 2px solid {color};
} QLabel#id_label {
    color: {color};
    font-weight:bold;
} QPushButton:pressed {
    background-color: {color};
} QPlainTextEdit:focus, QListWidget:focus {
    border:1px solid  {color}
} InsertBar {
    border-bottom: 2px solid {color};
    border-top: 2px solid {color};
}
"""


def style(app, icon="assets/cyckei.png", highlight=orange):
    app.setStyle("Fusion")
    app.setWindowIcon(QIcon(func.find_path(icon)))
    app.setStyleSheet(css.replace("{color}", highlight))


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


def message(text=None, info=None, icon=QMessageBox.Information,
            detail=None, confirm=False):
    """Show a Qt Message with given information."""

    msg = QMessageBox()
    msg.setText(text)
    msg.setInformativeText(info)
    msg.setIcon(icon)
    msg.setDetailedText(detail)
    if confirm:
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

    if msg.exec_() == QMessageBox.No:
        return False
    return True


def button(text=None, status=None, connect=None, enabled=True):
    """Creates a button with given information"""
    button = QPushButton()
    button.setText(text)
    button.setStatusTip(status)
    button.setEnabled(enabled)
    button.clicked.connect(functools.partial(connect, text))
    return button


def combo_box(items, status, key, connect):
    """Creates a combo box with given information"""
    box = QComboBox()
    box.addItems(items)
    box.setStatusTip(status)
    box.activated[str].connect(functools.partial(connect, key))
    return box


def label(text, status=None, tag=None):
    label = QLabel()
    label.setText(text)
    label.setStatusTip(status)
    label.setObjectName(tag)
    return label


def line_edit(label, status, key, connect):
    """Creates text edit field with given information"""
    text = QLineEdit()
    text.setMinimumSize(60, 20)
    text.setPlaceholderText(label)
    text.setStatusTip(status)
    text.textChanged.connect(functools.partial(connect, key))
    return text


def action(text=None, connect=None, tip=None, parent=None,
           disabled=False, separator=False):
    action = QAction(text, parent)
    action.setStatusTip(tip)
    action.triggered.connect(connect)
    action.setDisabled(disabled)
    action.setSeparator(separator)
    return action


def feedback(status, channel):
    channel.feedback.setText(status)
