from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="cyckei",
    version="0.1.dev6",
    author="Gabriel Ewig",
    author_email="gabriel@cyclikal.com",
    description="Keithley Battery Cycler for Python3",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords='keithley battery lithium-ion cycling calorimetry',
    url="https://gitlab.com/cyclikal/cyckei",

    packages=find_packages(),
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
    ],
    entry_points={
        "console_scripts": [
            "cyckei = cyckei.__main__:main"
        ],
    },
)
