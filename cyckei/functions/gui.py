"""
Universal GUI Functions
"""
import functools

from PySide2.QtWidgets import QMessageBox, QPushButton, QComboBox, QLineEdit, \
     QLabel, QAction, QPlainTextEdit
from PySide2.QtGui import QIcon

from cyckei.functions import func
from cyckei.functions.syntax import Highlighter

Question = QMessageBox.Question
Information = QMessageBox.Information
Warning = QMessageBox.Warning
Critical = QMessageBox.Critical

green = "#8be87d"
yellow = "#e8dd7d"
red = "#e87d7d"
orange = "#f05f40"
teal = "#3eb58a"
blue = "#33658a"
gray = "#a6a6a6"
dark = "#303036"

css = """
* {
    font-size:16px;
    selection-background-color: {color};
} InsertBar {
    border-bottom: 2px solid {color};
    border-top: 2px solid {color};
} ChannelWidget {
    border-bottom: 3px solid {color};
} QLabel#id_label {
    color: {color};
    font-weight:bold;
} QPushButton:pressed {
    background-color: {color};
} QPlainTextEdit:focus, QListWidget:focus {
    border: 1px solid {color}
}
"""


def style(app, icon="icon-client.png", highlight=orange):
    """Customizes the style of a QApplication window.

    Args:
        app (QApplication): Any object descended from QApplication.
        icon (str, optional): The filename, including extension, of an image to be the QIcon for the App. Defaults to "icon-client.png".
        highlight (str, optional): The highlight color for the QApp, in HEX color form. Defaults to orange.
    """
    app.setStyle("Fusion")
    app.setWindowIcon(QIcon(func.asset_path(icon)))
    app.setStyleSheet(css.replace("{color}", highlight))


def not_none(value):
    """Sets a None value to "None" string

    Args:
        value (None): Expects a None, but able to handle anything convertabile to a str.
    
    Returns:
        str: Returns "None" as a string or converts the given value to a string and returns it.
    """
    return "None" if value is None else str(value)


def message(text=None, info=None, icon=QMessageBox.Information,
            detail=None, confirm=False):
    """Show a QMessageBox with given information.

    The QMessageBox defaults to simply a popup window, but can also be used to let the user respond with "yes" or "no" and send a corresponding
    bool. The user can change aspects of the window such as body text, informative text, and detail text.

    Args:
        text (str, optional): The body text of the message. Defaults to None.
        info (str, optional): In most systems this text is appended to the body text, however in some in appears as smaller text below the body text. Defaults to None.
        icon (int, optional): An int (0-4) usable for setting the icon in QMessageBox. Defaults to QMessageBox.Information, an enum from the class representing a 1 int.
        detail (str, optional): This is the text that appears in the extra details section. Defaults to None.
        confirm (bool, optional): If True gives the user the option to select "Yes" or "No" in the message box. Defaults to False.

    Returns:
        bool: returns False if no was selected in the message box, else returns True.
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


def button(text=None, status=None, connect=None, enabled=True):
    """Creates a QPushButton with given information.

    Args:
        text (str, optional): The text on the button. Defaults to None.
        status (str, optional): The text of the status tip that appears when the cursor hovers over the button. Defaults to None.
        connect (func, optional): The function to connect to pushing the button. Defaults to None.
        enabled (bool, optional): Whether the button is enabled or not. False is Disabled. Defaults to True.

    Returns:
        QPushButton: A button with the specified features.
    """
    button = QPushButton()
    button.setText(text)
    button.setStatusTip(status)
    button.setEnabled(enabled)
    button.clicked.connect(functools.partial(connect, text))
    return button


def combo_box(items, status, key, connect):
    """Creates a QComboBox with given information. Essentially creates a dropdown selector.

    This is a combo box that is connected to a specified function.

    Args:
        items (list): Adds a list of strings as selectable items to the dropdown.
        status (str): The text of the status tip that appears when the cursor hovers over the button.
        key: The parameter that will be needed by the connected function (connect).
        connect (func): The function to connect to selecting an item in the dropdown window.

    Returns:
        QComboBox: A combined button and popup list with the specified features.
    """
    box = QComboBox()
    box.addItems(items)
    box.setStatusTip(status)
    box.activated[str].connect(functools.partial(connect, key))
    return box


def label(text, status=None, tag=None):
    """Creates a QLabel for your QApplication.

    Args:
        text (str): Sets the text of the QLabel
        status (str, optional): he text of the status tip that appears when the cursor hovers over the label. Defaults to None.
        tag (str, optional): Sets the QObject name for this label. Defaults to None.

    Returns:
        Qlabel: A label with the desired info.
    """
    label = QLabel()
    label.setText(text)
    label.setStatusTip(status)
    label.setObjectName(tag)
    return label


def line_edit(label, status, key, connect):
    """Creates an editable text edit field with given information

    Args:
        label (str): [description]
        status (str): [description]
        key ([type]): [description]
        connect ([type]): [description]

    Returns:
        [type]: [description]
    """
    
    text = QLineEdit()
    text.setMinimumSize(60, 20)
    text.setPlaceholderText(label)
    text.setStatusTip(status)
    if connect:
        text.textChanged.connect(functools.partial(connect, key))
    return text


def text_edit(status=None, connect=None, readonly=False,
              wrap=QPlainTextEdit.NoWrap):
    """[summary]

    Args:
        status ([type], optional): [description]. Defaults to None.
        connect ([type], optional): [description]. Defaults to None.
        readonly (bool, optional): [description]. Defaults to False.
        wrap ([type], optional): [description]. Defaults to QPlainTextEdit.NoWrap.

    Returns:
        [type]: [description]
    """
    editor = QPlainTextEdit()
    editor.setLineWrapMode(wrap)
    Highlighter(editor.document())
    if connect:
        editor.textChanged.connect(connect)
    editor.setReadOnly(readonly)
    editor.setStatusTip(status)

    return editor


def action(text=None, connect=None, tip=None, parent=None,
           disabled=False, separator=False):
    """[summary]

    Args:
        text ([type], optional): [description]. Defaults to None.
        connect ([type], optional): [description]. Defaults to None.
        tip ([type], optional): [description]. Defaults to None.
        parent ([type], optional): [description]. Defaults to None.
        disabled (bool, optional): [description]. Defaults to False.
        separator (bool, optional): [description]. Defaults to False.

    Returns:
        [type]: [description]
    """
    action = QAction(text, parent)
    action.setStatusTip(tip)
    action.triggered.connect(connect)
    action.setDisabled(disabled)
    action.setSeparator(separator)
    return action


def feedback(status, channel):
    """[summary]

    Args:
        status ([type]): [description]
        channel ([type]): [description]
    """
    channel.feedback.setText(status)
