import functools

from PySide2.QtWidgets import (QAction, QComboBox, QLabel, QLineEdit,
                               QMessageBox, QPushButton)


orange = "#f05f40"
grey = "#a6a6a6"

Question = QMessageBox.Question
Information = QMessageBox.Information
Warning = QMessageBox.Warning
Critical = QMessageBox.Critical


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
