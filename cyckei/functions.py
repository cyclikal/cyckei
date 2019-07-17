from PySide2.QtWidgets import QMessageBox


def post_message(text):
    msg = QMessageBox()
    msg.setText(text)
    msg.exec_()
