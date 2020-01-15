"""Tab to view and edit scripts, also has access to checking procedure"""
import logging
from os.path import join
from os import listdir

from PySide2.QtWidgets import QVBoxLayout, QHBoxLayout, \
    QPlainTextEdit, QListWidget, QFileDialog, QWidget, QListWidgetItem

from .workers import Check
from functions import gui

logger = logging.getLogger('cyckei')


class ScriptEditor(QWidget):
    """Main object of script tab"""
    def __init__(self, config, resource):
        QWidget.__init__(self)
        self.scripts = ScriptList(config)
        self.threadpool = resource["threadpool"]
        self.config = config

        # Create overall layout
        columns = QHBoxLayout(self)
        edit_rows = QVBoxLayout()
        columns.addLayout(edit_rows)
        columns.setStretch(0, 1)
        columns.setStretch(1, 5)

        # Create edit_rows
        edit_rows.addWidget(InsertBar())

        self.title_bar = gui.label("Select or open file to edit.")
        edit_rows.addWidget(self.title_bar)

        self.editor = QPlainTextEdit()
        self.editor.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.editor.textChanged.connect(self.text_modified)
        edit_rows.addWidget(self.editor)

        controls = QHBoxLayout()
        edit_rows.addLayout(controls)

        buttons = [
            ["Open", "Open Another Script", self.open],
            ["New", "Start New Script", self.new],
            ["Save", "Save Current Script", self.save],
            ["Check", "Check for Basic Syntax Errors", self.check],
        ]
        for button in buttons:
            controls.addWidget(gui.button(*button))

        self.setup_file_list()
        columns.addWidget(self.file_list)

    def setup_file_list(self):
        """Create list of script files"""
        self.file_list = QListWidget()
        self.file_list.itemClicked.connect(self.list_clicked)
        for script in self.scripts.script_list:
            self.file_list.addItem(script)
        self.file_list.setCurrentItem(self.file_list.item(0))
        self.list_clicked()

    def list_clicked(self):
        """Display contents of script when clicked"""
        try:
            item = self.file_list.currentItem()
            self.title_bar.setText(join(item.path, item.title))
            self.editor.setPlainText(self.file_list.currentItem().content)
        except AttributeError:
            logger.warning("Cannot load scripts, none found.")

    def text_modified(self):
        """Update content of script and update status to show if edited"""
        if self.file_list.currentItem() is not None:
            self.file_list.currentItem().content = self.editor.toPlainText()
            self.file_list.currentItem().update_status()

    def open(self, text):
        """Open new file and add as script"""
        script_file = QFileDialog.getOpenFileName(
            QWidget(), "Open Script File"
        )[0].rsplit("/", 1)
        if script_file[0]:
            self.add(script_file)

    def new(self, text):
        """Create new file and add to list as script"""
        script_file = QFileDialog.getSaveFileName(QWidget(),
                                                  "Select Directory")[0]
        if script_file:
            open(script_file, "a")
            self.add(script_file.rsplit("/", 1))

    def save(self, text):
        """Save script"""
        try:
            self.file_list.currentItem().save()
        except AttributeError:
            pass

    def check(self, text):
        """Run check protocol to verify validity"""
        worker = Check(self.config, self.file_list.currentItem().content)
        self.threadpool.start(worker)
        worker.signals.status.connect(self.alert_check)

    def alert_check(self, result, message):
        if result:
            msg = {
                "text": message,
                "info": "Script is good to go.",
            }
        else:
            msg = {
                "text": "Failed!",
                "info": "Script did not pass the check.",
                "detail": message,
                "icon": gui.Warning
            }
        gui.message(**msg)

    def add(self, file):
        """Add new script to list to make available"""
        self.scripts.script_list.append(Script(file[1], file[0]))
        self.file_list.addItem(self.scripts.script_list[-1])
        for channel in self.channels:
            channel.settings[1].addItem(self.scripts.script_list[-1].title)


class InsertBar(QWidget):
    """Controls and stores information for a given channel"""
    def __init__(self):
        super(InsertBar, self).__init__()
        # General UI
        layout = QVBoxLayout(self)

        # Settings
        settings = QHBoxLayout()
        layout.addLayout(settings)
        self.settings = self.get_settings()
        for element in self.settings:
            settings.addWidget(element)

        # Status
        args = ["Edit Protocol to Generate...",
                "Generated Protocol for Copy/Paste", "output", self.update]
        self.status = gui.line_edit(*args)
        layout.addWidget(self.status)

    def get_settings(self):
        """Creates all UI elements and adds them to elements list"""
        elements = []
        # Script File Dialog
        items = ["CCCharge", "CCDischarge", "CVCharge", "CVDischarge",
                 "Sleep", "Rest"]
        elements.append(gui.combo_box(items, "Select Protocol", "protocol",
                        self.update))

        # Line Edits
        editables = [
            ["V/I Value", " Set Voltage or Current", "value"],
            ["Report Threshhold", "Threshold to Record At", "report_val"],
            ["Report Interval", "Maximum Length Between Recording",
             "report_time"],
            ["End Threshhold", "Threshold to End Step", "end_val"],
            ["End Duration", "Max Duration of End Step", "end_time"],
        ]
        for line in editables:
            elements.append(gui.line_edit(*line, self.update))

        return elements

    def update(self, key, text):
        logger.debug(f"Key: {key}, Text: {text}")

    def set(self, key, text):
        """Sets object's script to one selected in dropdown"""
        pass


class Script(QListWidgetItem):
    """Object to store and manipulate scripts"""
    def __init__(self, title, path):
        super(Script, self).__init__()
        self.title = title
        self.path = path
        try:
            self.content = open(self.path + "/" + self.title, "r").read()
        except (UnicodeDecodeError, PermissionError) as error:
            self.content = "Could not read file: {}".format(error)
        self.setText(self.title)

    def save(self):
        """Saves script to file"""
        with open(self.path + "/" + self.title, "w") as file:
            file.write(self.content)
        self.update_status()

    def update_status(self):
        """Updates title with '*' if script has been edited"""
        try:
            file_content = open(self.path + "/" + self.title, "r").read()
        except UnicodeDecodeError as error:
            file_content = "Could not decode: {}".format(error)

        if self.content == file_content:
            self.setText(self.title)
        else:
            self.setText("* " + self.title)


class ScriptList(object):
    def __init__(self, config):
        self.script_list = []
        self.default_scripts(config["record_dir"] + "/scripts")

    def default_scripts(self, path):
        """Load scripts from scripts folder"""
        files = listdir(path)
        if files is not None:
            for file in files:
                self.script_list.append(Script(file, path))

    def by_title(self, title):
        """Returns script object with given title"""
        for script in self.script_list:
            if script.title == title:
                return script
        return None
