Installing Cyckei
=================

.. _Host System Setup:

Host System Setup
-----------------
Although Cyckei is developed on and for a variety of platforms, most internal usage and testing is done on Windows 10 running the latest release of Python 3. Other platforms may require more complex configuration and additional stability testing.

Cyckei relies on the PyVISA wrapper to communicate with any devices, and generally requires an additional VISA library as well as a driver for the device or adaptor which PyVISA controls. If the PyVISA python library is installed, you can use the following code to list the devices which it detects. If nothing is found, proceed with the Host System Setup.

::

    import visa
    rm = visa.ResourceManager()
    print(rm.list_resources())

Installing the necessary drivers can be difficult depending on your system. The National Instruments GPIB-USB-HS adaptors that we use require both a VISA library as well as a GPIB driver to function with PyVISA, Cyckei's core library. Installing each piece of software for different configurations is summarized below.

VISA
^^^^
`PyVISA-py`_
""""""""""""
PyVISA-py is a pure python backend for PyVISA. It offers less functionality than NI-VISA, but appears to work fine with Cyckei based on limited testing. More information about PyVISA-py and installation instructions can be found in their `documentation <https://pyvisa-py.readthedocs.io/>`_.

`NI-VISA`_
""""""""""
NI-VISA is the VISA library developed by National Instruments it is closed source and only available for certain platforms, but offers the most functionality. NI-VISA can be downloaded at `this site <https://www.ni.com/en-us/support/downloads/drivers/download.ni-visa.html>`_.

GPIB
^^^^
`NI-488.2`_
"""""""""""
Like NI-VISA, NI-488.2 is National Instruments' GPIB driver. It is simple to install, but has very limited compatibility especially on Linux. Downloads for NI-488.2 can be found `here <https://www.ni.com/en-us/support/downloads/drivers/download.ni-488-2.html>`_.

`Linux-GPIB`_
"""""""""""""
Linux-GPIB is a GPL licensed GPIB support package for Linux. In addition to the C API, it includes bindings for multiple languages including Python. Linux-GPIB must be compiled for your OS and requires some configuration, but works fine with PyVISA. To learn more about Linux-GPIB and download the source code, visit `sourceforge <https://linux-gpib.sourceforge.io/>`_.

Installation
------------
For Users
^^^^^^^^^
Cyckei is distributed using standalone executables for Linux, Mac OS, and Windows. Installation is as simple as downloading the correct executable from the GitLab `releases`_ page.

After downloading, simply double-click the executable to start Cyckei. A "cyckei" folder will automatically be created in the user's home directory to store scripts, configuration, and results.

Cyckei will almost certainly need to be configured to work with your instruments. See :ref:`Editing Configuration` for more details.

Frozen versions are only provided for major releases. For the latest (generally unstable) version see the below.

For Developers
^^^^^^^^^^^^^^
The Cyckei source code is available on `GitLab`_, and can be cloned locally to run the latest version.

.. code-block:: bash

  git clone https://gitlab.com/cyclikal/cyckei.git
  cd cyckei

Cyckei requires Python 3, and assumes that \*NIX-style commands are available. If developing on Windows, ``make`` will not function properly, and you must manually setup all virtual environments and dependencies. This can be accomplished with the following commands.

.. code-block:: bash

    pip install virtualenv
    virtualenv venv
    ./venv/Scripts/activate.bat
    pip install -Ur requirements.txt

On Linux and Mac OS, ``make`` is used to easily handle setting up and running Cyckei from source. For example, you can setup a virtual environment, install necessary dependencies, and run Cyckei with the following commands. ``make help`` will show all options for testing and building Cyckei.

.. code-block:: bash

    make setup
    make run

For more information about editing and contributing to Cyckei see :doc:`contributing`.

.. _GitLab: https://gitlab.com
.. _releases: https://gitlab.com/cyclikal/cyckei/-/releases
.. _PyVISA-py: https://pyvisa-py.readthedocs.io/
.. _NI-VISA: https://www.ni.com/en-us/support/downloads/drivers/download.ni-visa.html
.. _NI-488.2: https://www.ni.com/en-us/support/downloads/drivers/download.ni-488-2.html
.. _Linux-GPIB: https://linux-gpib.sourceforge.io/
