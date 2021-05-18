from os.path import join, dirname
import os.path


def asset_path(path):
    asset = join(dirname(__file__), "..", "assets", path)
    if os.path.exists(asset):
        return asset
    else:
        raise FileNotFoundError(f"could not find asset {asset}")


def not_none(value):
    """Sets a None value to "None" string"""
    return "None" if value is None else str(value)
