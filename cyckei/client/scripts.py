"""Methods and object to handle scripts"""

from os import listdir

from PySide2.QtWidgets import QListWidgetItem


class Scripts(object):
    def __init__(self):
        self.script_list = []

    def load_default_scripts(self, path):
        """Load scripts from scripts folder"""
        files = listdir(path)
        if files is not None:
            for file in files:
                self.script_list.append(Script(file, path))

    def get_script_by_title(self, title):
        """Returns script object with given title"""
        for script in self.script_list:
            if script.title == title:
                return script
        return None


class Script(QListWidgetItem):
    """Object to store and manipulate scripts"""
    def __init__(self, title, path):
        super().__init__()
        self.title = title
        self.path = path
        self.content = open(self.path + "/" + self.title, "r").read()
        self.setText(self.title)

    def save(self):
        """Saves script to file"""
        with open(self.path + "/" + self.title, "w") as file:
            file.write(self.content)
        self.update_status()

    def update_status(self):
        """Updates title with '*' if script has been edited"""
        if self.content == open(self.path + "/" + self.title, "r").read():
            self.setText(self.title)
        else:
            self.setText("* " + self.title)
