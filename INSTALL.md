# Installing Cyckei
#### A battery cycler written in Python 3
---

## Host System Setup
As briefly discussed in the `README`, installing the necessary drivers can be difficult depending on your system. The National Instruments GPIB-USB-HS adaptors that we use require both a VISA library as well as a GPIB driver to function with PyVISA, Cyckei's core library. Installing each piece of software for different configurations is summarized below.

### VISA
##### PyVISA-py
PyVISA-py is a pure python backend for PyVISA. It offers less functionality than NI-VISA, but appears to work fine with Cyckei based on limited testing. More information about PyVISA-py and installation instructions can be found at <https://pyvisa-py.readthedocs.io/>.

##### NI-VISA
NI-VISA is the VISA library developed by National Instruments it is closed source and only available for certain platforms, but offers the most functionality. NI-VISA can be downloaded at <https://www.ni.com/en-us/support/downloads/drivers/download.ni-visa.html>.

### GPIB
##### NI-488.2
Like NI-VISA, NI-488.2 is National Instruments' GPIB driver. It is simple to install, but has very limited compatibility especially on Linux. Downloads for NI-488.2 can be found at <https://www.ni.com/en-us/support/downloads/drivers/download.ni-488-2.html>.

##### Linux-GPIB
Linux-GPIB is a GPL licensed GPIB support package for Linux. In addition to the C API, it includes bindings for multiple languages including Python. Linux-GPIB must be compiled for your OS and requires some configuration, but works fine with PyVISA. To learn more about Linux-GPIB and download the source code visit <https://linux-gpib.sourceforge.io/>.

## Installation
#### For User
Since version 0.2 (Alviss), Cyckei has been distributed using "frozen" executables generated with PyInstaller.

Installation is as simple as downloading the correct executable from the GitLab releases page at <https://gitlab.com/cyclikal/cyckei/-/releases>.

After downloading, simply double-click the executable to start Cyckei. A "cyckei" folder will automatically be created in the user's home directory to store scripts, configuration, and results.

Frozen versions are only provided for major releases. For the latest (generally unstable) version see the developer section below.

#### For Developer
Developers should clone the Cyckei Git repository to run and develop the latest versions. {TODO: write more and automate dependencies}

For more information about editing cyckei see the `CONTRIBUING` file.
