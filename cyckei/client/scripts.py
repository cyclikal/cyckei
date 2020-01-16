"""Methods and object to handle scripts"""

from PySide2.QtWidgets import QListWidgetItem


# class ScriptList(object):
#     def __init__(self, config):
#         self.script_list = []
#         self.default_scripts(config["record_dir"] + "/scripts")

#     def default_scripts(self, path):
#         """Load scripts from scripts folder"""
#         files = listdir(path)
#         if files is not None:
#             for file in files:
#                 self.script_list.append(Script(file, path))

#     def by_title(self, title):
#         """Returns script object with given title"""
#         for script in self.script_list:
#             if script.title == title:
#                 return script
#         return None


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
