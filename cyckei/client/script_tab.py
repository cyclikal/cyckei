"""Tab to view and edit scripts, also has access to checking procedure"""

from PySide2.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel,\
    QPlainTextEdit, QPushButton, QListWidget, QFileDialog, QMessageBox,\
    QWidget, QStyleOption, QStyle
from PySide2.QtCore import Qt
from PySide2.QtGui import QPainter
from . import scripts
from .workers import Check


class ScriptEditor(QWidget):
    """Main object of script tab"""
    def __init__(self, channels, scripts, threadpool):
        QWidget.__init__(self)
        self.channels = channels
        self.scripts = scripts
        self.threadpool = threadpool

        # Create overall layout
        columns = QHBoxLayout(self)
        self.setup_file_list()
        columns.addWidget(self.file_list)
        edit_rows = QVBoxLayout()
        columns.addLayout(edit_rows)
        columns.setStretch(0, 1)
        columns.setStretch(1, 5)

        # Create edit_rows
        self.title_bar = QLabel()
        self.title_bar.setText("Select or open file to edit.")
        edit_rows.addWidget(self.title_bar)

        self.editor = QPlainTextEdit()
        self.editor.textChanged.connect(self.text_modified)
        edit_rows.addWidget(self.editor)

        controls = QHBoxLayout()
        edit_rows.addLayout(controls)

        buttons = []
        buttons.append(QPushButton())
        buttons[-1].setText("Open")
        buttons[-1].clicked.connect(self.open)
        buttons.append(QPushButton())
        buttons[-1].setText("Remove")
        buttons[-1].clicked.connect(self.remove)
        buttons.append(QPushButton())
        buttons[-1].setText("New")
        buttons[-1].clicked.connect(self.new)
        buttons.append(QPushButton())
        buttons[-1].setText("Save")
        buttons[-1].clicked.connect(self.save)
        buttons.append(QPushButton())
        buttons[-1].setText("Check")
        buttons[-1].clicked.connect(self.check)
        for button in buttons:
            controls.addWidget(button)

    def setup_file_list(self):
        """Create list of script files"""
        self.file_list = QListWidget()
        self.file_list.itemClicked.connect(self.list_clicked)
        for script in self.scripts.script_list:
            self.file_list.addItem(script)

    def list_clicked(self):
        """Display contents of script when clicked"""
        self.title_bar.setText(self.file_list.currentItem().path)
        self.editor.setPlainText(self.file_list.currentItem().content)

    def text_modified(self):
        """Update content of script and update status to show if edited"""
        if self.file_list.currentItem() is not None:
            self.file_list.currentItem().content = self.editor.toPlainText()
            self.file_list.currentItem().update_status()

    def open(self):
        """Open new file and add as script"""
        script_file = QFileDialog.getOpenFileName(
            QWidget(), "Open Script File"
        )[0].rsplit("/", 1)
        if script_file[0]:
            self.add(script_file)

    def remove(self):
        """Remove script from list and channel selector"""
        self.scripts.script_list.pop(self.file_list.currentRow())
        for channel in self.channels:
            channel.elements[1].removeItem(channel.elements[1].findText(
                    self.file_list.currentItem().title,
                    Qt.MatchFixedString
                ))
        self.file_list.takeItem(self.file_list.currentRow())
        try:
            self.list_clicked()
        except AttributeError:
            pass

    def new(self):
        """Create new file and add to list as script"""
        script_file = QFileDialog.getSaveFileName(QWidget(),
                                                  "Select Directory")[0]
        if script_file:
            open(script_file, "a")
            self.add(script_file.rsplit("/", 1))

    def save(self):
        """Save script"""
        self.file_list.currentItem().save()

    def check(self):
        """Run check protocol to verify validity"""
        worker = Check(self.file_list.currentItem().content)
        self.threadpool.start(worker)
        worker.signals.status.connect(self.post_message)

    def post_message(self, result, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        if result:
            msg.setText("Passed!")
            msg.setInformativeText("Script is good to go.")
            msg.setWindowTitle("Check Passed")
            msg.exec_()
        else:
            msg.setText("Failed!")
            msg.setInformativeText("Script did not pass the check.")
            msg.setWindowTitle("Check Failed")
            msg.setDetailedText(message)
            msg.exec_()
            return False

    def add(self, file):
        """Add new script to list to make available"""
        self.scripts.script_list.append(scripts.Script(file[1], file[0]))
        self.file_list.addItem(self.scripts.script_list[-1])
        for channel in self.channels:
            channel.elements[1].addItem(self.scripts.script_list[-1].title)

    def paintEvent(self, event):
        style_option = QStyleOption()
        style_option.initFrom(self)
        painter = QPainter(self)
        style = self.style()
        style.drawPrimitive(QStyle.PE_Widget, style_option, painter, self)
