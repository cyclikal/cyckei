from os.path import join, dirname
import os.path


def asset_path(path):
    """Appends a given path to the end of the path to the assests folder.

    Args:
        path (str): The path starting from the assests folder.

    Raises:
        FileNotFoundError: Error is raised when the given path doesn't point to an existing folder or file.

    Returns:
        str: the input path appended to the assests folder path.
    """
    asset = join(dirname(__file__), "..", "assets", path)
    if os.path.exists(asset):
        return asset
    else:
        raise FileNotFoundError(f"could not find asset {asset}")


def not_none(value):
    """Sets a None value to "None" string

    Args:
        value (None): Expects a None, but able to handle anything convertabile to a str.
    
    Returns:
        str: Returns "None" as a string or converts the given value to a string and returns it.
    """
    return "None" if value is None else str(value)
