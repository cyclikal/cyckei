import functools

from PySide2.QtWidgets import QMessageBox, QPushButton, QComboBox, QLineEdit, \
     QLabel, QAction


class Icon(object):
    def __init__(self):
        self.Question = QMessageBox.Question
        self.Information = QMessageBox.Information
        self.Warning = QMessageBox.Warning
        self.Critical = QMessageBox.Critical


def message(text=None, info=None, icon=QMessageBox.Information,
            detail=None, confirm=False):
    """
    Show a Qt Message with given information.

    Arguments:
        text -- Main text
        info -- Additional text
        icon -- Icon to show
        detail -- Details which need to be displayed manually
        title -- Name of message window
        confirm -- Displays 'yes/no' prompt if True, otherwise only 'ok'

    Returns:
        Button pressed in message
    """

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


def button(text, status, connect):
    """Creates a button with given information"""
    button = QPushButton()
    button.setText(text)
    button.setStatusTip(status)
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


def action(text=None, connect=None, disabled=False, separator=False):
    action = QAction(text)
    action.triggered.connect(connect)
    action.setDisabled(disabled)
    action.setSeparator(separator)
    return action


def status(status, channel):
    channel.status.setText(status)


def feedback(status, channel):
    channel.feedback.setText(status)
