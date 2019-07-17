import PyInstaller.__main__
import os
import random
import string


def rand_string(length=10):
    """Generate random string"""
    return "".join(random.choice(string.printable) for i in range(length))


name = "cyckei"
identifier = "com.cyclikal.cyckei"
key = rand_string()
icon = os.path.join("assets", "cyckei.icns")
data = os.path.join("assets", "*") + ":assets"


PyInstaller.__main__.run([
    "--name=%s" % name,
    "--onefile",
    "--windowed",
    "--noconfirm",
    "--clean",
    "--add-data=%s" % data,
    "--icon=%s" % icon,
    "--key=%s" % key,
    "--osx-bundle-identifier=%s" % identifier,
    "cyckei.py"
])
