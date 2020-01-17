from setuptools import setup

with open("README.rst", "r") as fh:
    long_description = fh.read()

setup(
    name="cyckei",
    version="0.3.dev1",
    author="Cyclikal, LLC.",
    author_email="gabriel@cyclikal.com",
    description="Keithley Battery Cycler for Python 3",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    keywords='keithley battery lithium-ion cycling calorimetry',
    url="https://gitlab.com/cyclikal/cyckei",

    packages=["cyckei", "cyckei.server", "cyckei.client", "cyckei.explorer",
              "cyckei.functions"],
    package_dir={
        "cyckei": "cyckei",
        "server": "cyckei/server",
        "client": "cyckei/client",
        "explorer": "cyckei/explorer",
        "functions": "cyckei/functions"
    },

    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering",
    ],
    install_requires=[
        "zmq",
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
