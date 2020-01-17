from setuptools import setup
import json

with open("README.rst", "r") as file:
    long_description = file.read()
with open("cyckei/assets/variables.json", "r") as file:
    var = json.load(file)

setup(
    name=var["name"],
    version=var["version"],
    author=var["author"],
    author_email=var["email"],
    description=var["description"],
    long_description=long_description,
    long_description_content_type="text/x-rst",
    keywords=var["keywords"],
    url=var["url"],

    packages=["cyckei", "cyckei.server", "cyckei.client", "cyckei.explorer",
              "cyckei.functions"],
    include_package_data=True,

    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering",
    ],
    install_requires=[
        "pyzmq",
        "pyvisa",
        "PySide2",
        "matplotlib",
    ],
    entry_points={
        "console_scripts": [
            "cyckei = cyckei.cyckei:main"
        ],
    },
)
