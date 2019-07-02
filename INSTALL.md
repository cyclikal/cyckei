# Cyckei Install
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
Cyckei expects to packaged and installed with setuptools. The easiest method of installation is to install Cyckei with `pip`. It is recommended to do so within a virtual environment in order to prevent conflicting dependencies.

    pip install cyckei

Cyckei can also be installed from source by cloning or downloading the git repository at <https://gitlab.com/cyclikal/cyckei>. To package and install Cyckei run the following from the `cyckei` directory.

    python setup.py sdist
    pip install dist/cyckei-X.X.tar.gz

Cyckei is run by executing the `cyckei` command from a terminal. Alternatively, the server and client components can be started separately with `cyckei-server` and `cyckei-client`.

After installing, refer to the `HELP` file to configure devices.
