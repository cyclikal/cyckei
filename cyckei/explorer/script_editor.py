"""Tab to view and edit scripts, also has access to checking procedure"""
import logging
from os.path import join
from os import listdir
import webbrowser

from PySide2.QtWidgets import QVBoxLayout, QHBoxLayout, \
    QListWidget, QFileDialog, QWidget, QListWidgetItem

from .workers import Check
from cyckei.functions import gui

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
        self.editor = gui.text_edit("Edit Script", self.text_modified)
        self.title_bar = gui.label("Select or open file to edit.")

        edit_rows.addWidget(InsertBar(self.editor))
        edit_rows.addWidget(self.title_bar)
        edit_rows.addWidget(self.editor)

        controls = QHBoxLayout()
        edit_rows.addLayout(controls)

        buttons = [
            ["Open", "Open Another Script", self.open],
            ["New", "Start New Script", self.new],
            ["Save", "Save Current Script", self.save],
            ["Check", "Check for Basic Syntax Errors", self.check],
            ["Help", "Script Writing Help", self.help]
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

    def help(self, text):
        webbrowser.open("https://docs.cyclikal.com/projects/cyckei/en/stable/"
                        "usage.html#creating-scripts")

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


class InsertBar(QWidget):
    """Controls and stores information for a given channel"""
    def __init__(self, editor):
        super(InsertBar, self).__init__()
        self.attributes = {
            "protocol": "CCCharge",
            "value": "0.01",
            "report_val": "0.1",
            "report_time": ":5:",
            "end_val": "3.8",
            "end_time": "5::",
        }
        self.editor = editor

        # General UI
        layout = QVBoxLayout(self)

        # Settings
        settings = QHBoxLayout()
        layout.addLayout(settings)
        self.settings = self.get_settings()
        for element in self.settings:
            settings.addWidget(element)

        # Status
        lower = QHBoxLayout()
        layout.addLayout(lower)

        args = ["Edit Protocol to Generate...",
                "Generated Protocol for Copy/Paste", None, None]
        self.output = gui.line_edit(*args)
        lower.addWidget(self.output)

        lower.addWidget(gui.button("Insert", "Insert Protocol into Script",
                        self.insert))

    def get_settings(self):
        """Creates all UI elements and adds them to elements list"""
        elements = []
        # Script File Dialog
        items = ["CCCharge", "CCDischarge", "CVCharge", "CVDischarge",
                 "Sleep", "Rest", "Comment", "For Loop"]
        elements.append(gui.combo_box(items, "Select Protocol", "protocol",
                        self.update))

        # Line Edits
        editables = [
            ["V/I Value", " Set Voltage or Current", "value"],
            ["Report Threshhold", "Threshold to Record At", "report_val"],
            ["Report Interval (hh:mm:ss)",
             "Maximum Length Between Recording  in Format HH:MM:SS",
             "report_time"],
            ["End Threshhold", "Threshold to End Step", "end_val"],
            ["End Duration (hh:mm:ss)",
             "Max Duration of End Step in Format HH:MM:SS", "end_time"],
        ]
        for line in editables:
            elements.append(gui.line_edit(*line, self.update))

        return elements

    def update(self, key, text):
        self.attributes[key] = text
        self.write()

    def write(self):
        d = self.attributes

        if d['protocol'] == "Sleep" or d['protocol'] == "Rest":
            out = f"{d['protocol']}(reports=(('time', '{d['report_time']}'),)"\
                  f", ends=(('time', '>', '{d['end_time']}'), ))"
        elif d['protocol'] == "CCCharge" or d['protocol'] == "CVCharge":
            out = f"{d['protocol']}({d['value']}," \
                  f"reports=(('voltage', '{d['report_val']}'), "\
                  f"('time', '{d['report_time']}')), "\
                  f"ends=(('voltage', '>', '{d['end_val']}'), "\
                  f"('time', '>', '{d['end_time']}')))"
        elif d['protocol'] == "CCDischarge" or d['protocol'] == "CVDischarge":
            out = f"{d['protocol']}({d['value']}, "\
                  f"reports=(('voltage', '{d['report_val']}'), "\
                  f"('time', '{d['report_time']}')), "\
                  f"ends=(('voltage', '<', '{d['end_val']}'), "\
                  f"('time', '>', '{d['end_time']}')))"
        elif d['protocol'] == "Comment":
            out = f"# {d['value']}"
        elif d['protocol'] == "For Loop":
            out = f"for i in range({d['value']}):"

        self.output.setText(out.replace("\'", "\""))
        logger.debug(self.output.text)

    def insert(self, text):
        content = self.output.text()
        if content:
            self.editor.appendPlainText(content)


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
