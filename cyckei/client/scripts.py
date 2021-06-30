"""Methods and object to handle scripts

|
"""

from PySide2.QtWidgets import QListWidgetItem


# class ScriptList(object):
#     def __init__(self, config):
#         self.script_list = []
#         self.default_scripts(config["arguments"]["record_dir"] + "/scripts")

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
    """Object for storing and manipulating strings that act as scripts
    
    Attributes:
        content (str): The text that acts as the script in the file of the script.
        path (str): The filepath of the file of the script.
        title (str): The filename of the script being held.
    |
    """

    def __init__(self, title, path):
        """Inits Script with content, path, and title.
        
        Args:
        title (str): The filename of the script being held.
        path (str): The filepath of the file of the script.
        |
        """
        super(Script, self).__init__()
        self.title = title
        self.path = path
        try:
            self.content = open(self.path + "/" + self.title, "r").read()
        except (UnicodeDecodeError, PermissionError) as error:
            self.content = "Could not read file: {}".format(error)
        self.setText(self.title)

    def save(self):
        """Saves script content to file using the script's path and title.
        
        |
        """
        with open(self.path + "/" + self.title, "w") as file:
            file.write(self.content)
        self.update_status()

    def update_status(self):
        """Updates the script's title with '*' if the script's contents has been edited
        
        |
        """
        try:
            file_content = open(self.path + "/" + self.title, "r").read()
        except UnicodeDecodeError as error:
            file_content = "Could not decode: {}".format(error)

        if self.content == file_content:
            self.setText(self.title)
        else:
            self.setText("* " + self.title)
