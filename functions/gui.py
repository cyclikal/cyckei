from PySide2.QtWidgets import QMessageBox


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

    return msg.exec_()
