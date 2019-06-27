from setuptools import setup
import platform

with open("README.md", "r") as fh:
    long_description = fh.read()

dependencies = [
    "zmq",
    "pyvisa",
    "pyvisa-py",
    "PySide2"
]

if platform.system() == "Darwin":
    dependencies.append("pyobjc-framework-Cocoa")

setup(
    name="cyckei",
    version="0.1.dev9",
    author="Gabriel Ewig",
    author_email="gabriel@cyclikal.com",
    description="Keithley Battery Cycler for Python3",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="keithley battery lithium-ion cycling calorimetry",
    url="https://gitlab.com/cyclikal/cyckei",

    packages=["cyckei", "cyckei.server", "cyckei.client"],
    package_dir={
        "cyckei": "cyckei",
        "cyckei.server": "cyckei/server",
        "cyckei.client": "cyckei/client"
    },
    package_data={
        "cyckei.server": ["cyckei/server/res"],
        "cyckei.client": ["cyckei/client/res"],
    },
    include_package_data=True,

    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering",
    ],
    install_requires=dependencies,
    entry_points={
        "gui_scripts": [
            "cyckei = cyckei.cyckei:main",
            "cyckei-server = cyckei.server.__main__:main",
            "cyckei-client = cyckei.client.__main__:main"
        ]
    },
    test_suite='cyckei.tests',
)
