import setuptools
import configparser

with open("README.rst", "r") as file:
    long_description = file.read()
    var = configparser.ConfigParser()
    var.read("cyckei/assets/variables.ini")

setuptools.setup(
    name=var["versioning"]["name"],
    version=var["versioning"]["version"],
    author=var["publishing"]["author"],
    author_email=var["publishing"]["email"],
    description=var["meta"]["description"],
    long_description=long_description,
    long_description_content_type="text/x-rst",
    keywords=var["meta"]["keywords"],
    url=var["meta"]["url"],

    packages=setuptools.find_packages(),
    include_package_data=True,

    classifiers=[
        "Programming Language :: Python :: 3",
        'Programming Language :: Python :: 3.7',
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering",
    ],
    install_requires=[
        "pyzmq",
        "pyvisa",
        "PySide2",
        "matplotlib",
        "numpy"
    ],
    extras_require={
        'dev': [
            'pytest',
            'pytest-cov',
            'scipy',
            'pylint',
            'autopep8'
        ]
    },
    entry_points={
        "console_scripts": [
            "cyckei = cyckei.cyckei:main"
        ],
    },
)
