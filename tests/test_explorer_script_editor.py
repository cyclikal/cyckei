
import os
import pytest
from cyckei.explorer import script_editor
from PySide2.QtCore import QThreadPool

# Testing the initialization of Script objects in script_editor


def test_make_script():
    # Script objects need a real file or they throw an exception
    f1 = open("tests/test_file1.txt", "w")
    f2 = open("tests/test_file2.txt", "w")
    f2.write("Testing the ability to read in some data.")
    f1.close()
    f2.close()
    test_script1 = script_editor.Script("./tests", "test_file1.txt")
    test_script2 = script_editor.Script("./tests", "test_file2.txt")
    # Testing the variables that are initialized by calling the constructor.
    assert test_script1.path == "./tests"
    assert test_script1.title == "test_file1.txt"
    assert test_script1.content == ""
    assert test_script2.path == "./tests"
    assert test_script2.title == "test_file2.txt"
    assert test_script2.content == "Testing the ability to read in some data."
    # cleaning up files that were created for testing
    os.remove("tests/test_file1.txt")
    os.remove("tests/test_file2.txt")

# Testing the save function on a Script object, which should overwrite the real file it is based off of


def test_save_script():
    with open("tests/test_file1.txt", "w") as f1:
        f1.write("Testing the ability to read in some data.")

    with open("tests/test_file1.txt", "r") as f1:
        match = f1.read()

    test_script1 = script_editor.Script("./tests", "test_file1.txt")
    # manually accessing and changing the "content" of the script
    test_script1.content = "Testing the ability to change some data."
    # file should not be the same as script content before a save is called
    assert match != test_script1.content
    test_script1.save()
    with open("tests/test_file1.txt", "r") as f1:
        match = f1.read()

    # now file should be the same
    assert match == test_script1.content
    # cleaning up files created for testing
    os.remove("tests/test_file1.txt")

# Testing the Script status function which compares Script content to the file it is based off of
# and inserts and * at the front of the script title if there are differences


def test_status_script():
    f1 = open("tests/test_file1.txt", "w")
    f1.write("Testing the ability to read in some data.")
    f1.close()
    test_script1 = script_editor.Script(
        "./tests", "test_file1.txt")
    test_script1.content = "Testing the ability to change some data."
    test_script1.update_status()
    # Only the script's internal title should be changing, not the actual file
    assert test_script1.text() == "* test_file1.txt"
    assert os.path.isfile(
        "tests/test_file1.txt") == True
    assert os.path.isfile(
        "tests/* test_file1.txt") == False
    # cleaning up files created for testing
    os.remove("tests/test_file1.txt")

# Testing the constructor for ScriptList objects


def test_make_scriptlist():
    # creating a directory and scripts for testing. If a directory already exists
    # with the requested name an error is thrown, so we chack first.
    if os.path.isdir("tests/scripts") == False:
        os.mkdir("tests/scripts")
    f1 = open("tests/scripts/test_file1.txt", "w")
    f1.close()
    f2 = open("tests/scripts/test_file2.txt", "w")
    f2.close()
    f3 = open("tests/scripts/test_file3.txt", "w")
    f3.close()
    # These are the pieces of the config file required for initialized a ScriptList
    config = {"arguments": {"record_dir": "tests"}}
    test_scriptlist1 = script_editor.ScriptList(config)
    assert len(test_scriptlist1.script_list) == 3
    assert test_scriptlist1.script_list[0].title == "test_file1.txt"
    assert test_scriptlist1.script_list[0].path == "tests/scripts"
    assert test_scriptlist1.script_list[1].title == "test_file2.txt"
    assert test_scriptlist1.script_list[1].path == "tests/scripts"
    assert test_scriptlist1.script_list[2].title == "test_file3.txt"
    assert test_scriptlist1.script_list[2].path == "tests/scripts"
    # cleaning up some files created for testing in order to test an empty dir
    os.remove("tests/scripts/test_file1.txt")
    os.remove("tests/scripts/test_file2.txt")
    os.remove("tests/scripts/test_file3.txt")
    test_scriptlist2 = script_editor.ScriptList(config)
    assert len(test_scriptlist2.script_list) == 0
    # removing the directory created for testing
    os.rmdir("tests/scripts")

# Testing the title seraching in ScriptList


def test_by_title_scriptlist():
    # creating a directory and files for testing
    if os.path.isdir("tests/scripts") == False:
        os.mkdir("tests/scripts")
    f1 = open("tests/scripts/test_file1.txt", "w")
    f1.close()
    f2 = open("tests/scripts/test_file2.txt", "w")
    f2.close()
    # Creating a dupe to manually insert at he end of the script list
    f2_script_name_dupe = script_editor.Script(
        "tests/scripts", "test_file2.txt")
    f2_script_name_dupe.path = "Different path, same file name"
    f3 = open("tests/scripts/test_file3.txt", "w")
    f3.close()
    config = {"arguments": {"record_dir": "tests"}}
    test_scriptlist1 = script_editor.ScriptList(config)
    title = "test_file2.txt"
    returned_script = test_scriptlist1.by_title(title)
    # checking if a search on a seemingly regular scriptlist is correct
    assert returned_script.path == "tests/scripts"
    test_scriptlist1.script_list.append(f2_script_name_dupe)
    returned_script = test_scriptlist1.by_title(title)
    # checking if a search on a scriptlist with a duplicate title returns the first matching instance
    assert returned_script.path == "tests/scripts"
    # removing the files and directory created for testing
    os.remove("tests/scripts/test_file1.txt")
    os.remove("tests/scripts/test_file2.txt")
    os.remove("tests/scripts/test_file3.txt")
    os.rmdir("tests/scripts")

# Testing initializing a ScriptEditor object


def test_make_scripteditor():
    # setup required for creating a ScriptEditor object (setup for Script and ScriptList is required too)
    resource = {}
    resource["threadpool"] = QThreadPool()
    config = {"arguments": {"record_dir": "tests"}}
    if os.path.isdir("tests/scripts") == False:
        os.mkdir("tests/scripts")
    f1 = open("tests/scripts/test_file1.txt", "w")
    f1.close()
    f2 = open("tests/scripts/test_file2.txt", "w")
    f2.close()
    f3 = open("tests/scripts/test_file3.txt", "w")
    f3.close()

    # test_scripteditor1 = script_editor.ScriptEditor(config, resource)

    # Cleanup
    os.remove("tests/scripts/test_file1.txt")
    os.remove("tests/scripts/test_file2.txt")
    os.remove("tests/scripts/test_file3.txt")
    os.rmdir("tests/scripts")


# def test_text_modified_scripteditor():
#     assert 1 == 1


# def test_open_scripteditor():
#     assert 1 == 1


# def test_new_scripteditor():
#     assert 1 == 1


# def test_check_scripteditor():
#     assert 1 == 1


# def test_delete_scripteditor():
#     assert 1 == 1


# def test_add_scripteditor():
#     assert 1 == 1
