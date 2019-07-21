# Installing Cyckei

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
#### For Users
Since version 0.2 (Alviss), Cyckei is being distributed using standalone executables for Linux, Mac OS, and Windows.

Installation is as simple as downloading the correct executable from the GitLab releases page at <https://gitlab.com/cyclikal/cyckei/-/releases>.

After downloading, simply double-click the executable to start Cyckei. A "cyckei" folder will automatically be created in the user's home directory to store scripts, configuration, and results.

Cyckei will almost certainly need to be configured to work with your instruments. See the `HELP` file for more details.

Frozen versions are only provided for major releases. For the latest (generally unstable) version see the developer section below.

#### For Developers
The Cyckei source code is available on GitLab, and can be cloned locally to run the latest version.

    git clone https://gitlab.com/cyclikal/cyckei.git
    cd cyckei

Cyckei requires Python 3, and assumes that \*NIX-style commands are available. If developing on Windows, `make` will not function properly, and you must manually setup all virtual environments and dependencies. This can be accomplished with the following commands.

    pip install virtualenv
    virtualenv venv
    .\venv\Scripts\activate.bat
    pip install -Ur requirements.txt

On Linux and Mac OS, `make` is used to easily handle setting up and running Cyckei from source. For example, you can setup a virtual environment, install necessary dependencies, and run Cyckei with the following commands. `make help` will show all options for testing and building Cyckei.

    make setup
    make run

For more information about editing and contributing to Cyckei see the `CONTRIBUTING` file.
