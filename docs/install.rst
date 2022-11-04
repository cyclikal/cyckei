Installation
============

.. _Host System Setup:

Host System Setup
-----------------
Although Cyckei is developed on and for a variety of platforms, most internal usage and testing is done on Windows 10 running the latest release of Python 3. Other platforms may require more complex configuration and additional stability testing.

Cyckei relies on the PyVISA wrapper to communicate with any devices, and generally requires an additional VISA library as well as a driver for the device or adaptor which PyVISA controls. If the PyVISA python library is installed, you can use the following code in a python interpreter to list the devices which it detects. If nothing is found, proceed with the Host System Setup.

::

    import pyvisa
    rm = pyvisa.ResourceManager()
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

..
  Cyckei is distributed on PyPi and can easily be acquired with pip. It is recommended that Cyckei is installed into a virtual environment.

  After downloading, simply run ``cyckei`` in the command prompt to launch a component. A "cyckei" folder will automatically be created in the user's home directory to store scripts, configuration, and results.

  A stable version of Cyckei can be found on the master branch of our public GitHub repository.

  Cyckei will almost certainly need to be configured to work with your instruments. See :ref:`Editing Configuration` for more details.


For Users and Developers
^^^^^^^^^^^^^^^^^^^^^^^^
The Cyckei source code is available on `GitHub`_ at our public `repository`_ , and can be cloned locally to run the latest version.

.. code-block:: bash

  git clone https://github.com/cyclikal/cyckei.git
  cd cyckei

Cyckei requires Python 3 in addition to some packages which can be installed via pip and the included requirements file. Consult ``setup.py`` for a complete list of requirements.

Python can be run directly from source using the ``cyckei.py`` script in the root of the repository.

.. code-block:: bash

  python cyckei.py

..
  It can also be installed as a package and run by packaging it with ``setup.py``.

  .. code-block:: bash
    
    python setup.py sdist
    pip install dist/cyckei.tar.gz
    cyckei

For more information about editing and contributing to Cyckei see :doc:`contributing`.

.. _GitHub: https://github.com
.. _repository: https://github.com/cyclikal/cyckei
.. _releases: https://github.com/cyclikal/cyckei/-/releases
.. _PyVISA-py: https://pyvisa-py.readthedocs.io/
.. _NI-VISA: https://www.ni.com/en-us/support/downloads/drivers/download.ni-visa.html
.. _NI-488.2: https://www.ni.com/en-us/support/downloads/drivers/download.ni-488-2.html
.. _Linux-GPIB: https://linux-gpib.sourceforge.io/
