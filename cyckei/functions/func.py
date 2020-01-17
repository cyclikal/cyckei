from os.path import join, dirname


def asset_path(path):
    return join(dirname(__file__), "..", "assets", path)


def not_none(value):
    """Sets a None value to "None" string"""
    return "None" if value is None else str(value)
