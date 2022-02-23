# Tab to view and edit scripts, also has access to checking procedure
import logging
from os.path import join
from os import listdir

from os import remove
from os.path import exists, join as joinPaths

import webbrowser

from PySide2.QtWidgets import QVBoxLayout, QHBoxLayout, \
    QListWidget, QFileDialog, QWidget, QListWidgetItem
from PySide2 import QtCore

from .workers import Check
from cyckei.functions import gui

logger = logging.getLogger('cyckei')

class ScriptEditor(QWidget):
    """ UI window for the script tab of Cyckei Explorer """

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
        edit_rows.setStretch(0, 1)
        # edit_rows.setStretch(1, 1)
        edit_rows.setStretch(2, 5)
        # edit_rows.setStretch(3, 1)

        buttons = [
            ["Open", "Open Another Script", self.open],
            ["New", "Start New Script", self.new],
            ["Save", "Save Current Script", self.save],
            ["Check", "Check for Basic Syntax Errors", self.check],
            ['Delete', 'Delete Currently Active Script', self.delete],
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

    def update_editor(self, active_script_index):
        """Updates the UI when which script is active is changed"""
        # Checking for out of bounds error
        if active_script_index >= 0 and active_script_index < self.file_list.count():
            self.file_list.setCurrentItem(self.file_list.item(active_script_index))
            self.title_bar.setText(join(self.file_list.currentItem().path, self.file_list.currentItem().title))
            self.editor.setPlainText(self.file_list.currentItem().content)
        else:
            self.title_bar.setText("")
            self.editor.setPlainText("")

    def open(self, text):
        """Opens a new file and adds it as a script"""
        script_file = QFileDialog.getOpenFileName(
            QWidget(), "Open Script File", ""
        )[0].rsplit("/", 1)
        if script_file[0]:
            # This section opens a new script if it is not already open
            dupe = False
            for script_index in range (len(self.scripts.script_list)):
                script = self.scripts.script_list[script_index]
                if(script.title == script_file[1]):
                    self.update_editor(script_index)
                    dupe = True
                    break
            if not dupe:
                self.add(script_file)
                self.update_editor(self.file_list.count()-1)

    def new(self, text):
        """Creates new file and adds it to list as script"""
        script_file = QFileDialog.getSaveFileName(QWidget(),
                                                  "Select Directory")[0]
        if script_file:
            open(script_file, "a")
            self.add(script_file.rsplit("/", 1))
        self.update_editor(self.file_list.count()-1)

    def save(self, text):
        """Calls the save function of a Script object"""
        try:
            self.file_list.currentItem().save()
        except AttributeError:
            pass

    def check(self, text):
        """Creates and runs a worker to check protocol and verify the validity of a script"""
        worker = Check(self.config, self.file_list.currentItem().content)
        self.threadpool.start(worker)
        worker.signals.status.connect(self.alert_check)

    def delete(self, text):
        """Deletes the active file and removes it from the UI"""
        active_file = self.file_list.currentItem()
        path_to_delete = joinPaths(active_file.path, active_file.title)
        # Checking path with os.path.exists()
        if exists(path_to_delete):
            verify_msg = {
                "text": "Are you sure you would like to delete:",
                "info": path_to_delete + "  ?",
                "confirm": True
            }
            delete = gui.message(**verify_msg)
            if delete:
                # removing path with os.path.remove()
                remove(path_to_delete)
                current_row = self.file_list.row(self.file_list.currentItem())
                # takeItem removes the item at the row of the currentItem
                self.file_list.takeItem(current_row)
                        
                result_msg = {
                    "text": "Success!",
                    "info": "You have deleted: "+path_to_delete,
                }
                if current_row <= self.file_list.count()-1:
                    self.update_editor(current_row)
                else:
                    self.update_editor(current_row-1)
        else:
            result_msg = {
                "text": "Failed!",
                "info": "There was no file at the specified path.",
                "icon": gui.Warning
            }
        
        gui.message(**result_msg)

    def help(self, text):
        """Opens the Cyclikal Guide for creating scripts"""
        webbrowser.open("https://docs.cyclikal.com/projects/cyckei/en/stable/"
                        "usage.html#creating-scripts")

    def alert_check(self, result, message):
        """Opens a pop-up window with an input message"""
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
        """Creates and adds a Script object to the front of the ScriptList and UI FileList"""
        self.scripts.script_list.append(Script(file[0], file[1]))
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

        args = ["Generated Protocol for Copy/Paste"]
        self.output = gui.text_edit(*args)
        self.output.setReadOnly(True)
        lower.addWidget(self.output)
        lower.setGeometry(QtCore.QRect(100, 100, 100, 100))

        lower.addWidget(gui.button("Insert", "Insert Protocol into Script",
                        self.insert))

        self.write()

    def get_settings(self):
        """Creates all UI elements and adds them to elements list"""
        elements = []
        # Script File Dialog
        items = ["CCCharge", "CCDischarge", "CVCharge", "CVDischarge",
                 "Sleep", "Rest", "Comment", "Loop"]
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
            out = f"{d['protocol']}({d['value']}, " \
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
        elif d['protocol'] == "Loop":
            out = f"for i in range({d['value']}):\n\tAdvanceCycle()"

        self.output.setPlainText(out.replace("\'", "\""))
        logger.debug(self.output.toPlainText())

    def insert(self, text):
        content = self.output.toPlainText()
        if content:
            self.editor.appendPlainText(content)
 
class Script(QListWidgetItem):
    """Stores the File Path, Title, and content of a file"""

    def __init__(self, path, title):
        super(Script, self).__init__()
        self.title = title
        self.path = path
        try:
            self.content = open(joinPaths(self.path, self.title), "r").read()
        except (UnicodeDecodeError, PermissionError) as error:
            self.content = "Could not read file: {}".format(error)
        self.setText(self.title)

    def save(self):
        """Overwrites the file that shares a file path and title witht the script"""
        with open(joinPaths(self.path, self.title), "w") as file:
            file.write(self.content)
        self.update_status()

    def update_status(self):
        """Changes the file title in the Script interface if the script and the file differ"""
        try:
            file_content = open(joinPaths(self.path, self.title), "r").read()
        except UnicodeDecodeError as error:
            file_content = "Could not decode: {}".format(error)

        if self.content == file_content:
            self.setText(self.title)
        else:
            self.setText("* " + self.title)


class ScriptList(object):
    def __init__(self, config):
        self.script_list = []
        self.default_scripts(joinPaths(config["arguments"]["record_dir"], "scripts"))

    def default_scripts(self, path):
        """Load scripts from scripts folder in the directory specified by the config file"""
        files = listdir(path)
        if files is not None:
            for file in files:
                self.script_list.append(Script(path, file))

    def by_title(self, title):
        """Returns the first script object with a matching title"""
        for script in self.script_list:
            if script.title == title:
                return script
        return None
