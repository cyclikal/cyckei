import os
import sys

<<<<<<< HEAD:functions/processing.py
=======

>>>>>>> ba156f7cd847635083df9b99e0cae7c10a8ecfb5:functions/__init__.py
def find_path(path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, path)
    local = os.path.join(os.path.abspath('.'), path)
    if os.path.exists(local):
        return local
    return os.path.join(os.path.abspath('..'), path)


def not_none(value):
    """Sets a None value to "None" string"""
    return "None" if value is None else str(value)
