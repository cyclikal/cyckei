import setuptools
import configparser

with open("README.rst", "r") as file:
    long_description = file.read()
    var = configparser.ConfigParser()
    var.read("cyckei/assets/variables.ini")

setuptools.setup(
    name=var["Versioning"]["name"],
    version=var["Versioning"]["version"],
    author=var["Publishing"]["author"],
    author_email=var["Publishing"]["email"],
    description=var["Meta"]["description"],
    long_description=long_description,
    long_description_content_type="text/x-rst",
    keywords=var["Meta"]["keywords"],
    url=var["Meta"]["url"],

    packages=["cyckei", "cyckei.server", "cyckei.client", "cyckei.explorer",
              "cyckei.functions", "cyckei.plugins"],
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
        "matplotlib"
    ],
    entry_points={
        "console_scripts": [
            "cyckei = cyckei.cyckei:main"
        ],
    },
)
