Plugins
=======

.. _Host System Setup:

Plugin Overview
---------------
Although the base version fo Cyckei is designed to control and capture data from Keithley SourceMeters, the functionality can be extended with plugins.
Plugins aim to support simultaneous data collection with additional instruments that can interface with a computer.
This requires that the data capturing eventually be queried and returned by python code, but the method that this is done is very flexible.

Installation & Configuration
----------------------------
Plugins are distributed independently of Cyckei as python packages.
These packages are generally able to be executed independently for testing purposes, but are designed to be loaded by Cyckei for data capture.

Generally, installation involves cloning the github repository, changing to the directory and installing the python package:

.. code-block: python

  git clone https://github.com/cyclikal/cyp-[package].git
  cd ./cyp-[package]
  python setup.py install

To be loaded by cyckei, an entry must also be added to the ``plugins`` section of Cyckei's ``config.json``.
Plugins should provide an example configuration and instructions on how to adjust it.
The configuration for the [randomizer] plugin is included for reference.

.. code-block:: json

  {
    "name": "randomizer",
    "enabled": true,
    "sources": [
      {
        "port": null,
        "meta": [1, 10]
      },
      {
        "port": null,
        "meta": [11, 20]
      }
    ]
},

The configuration includes a number of reference values such as a name, whether the plugin should be enabled.
It also has a list of sources that can be assigned to different channels.
The ``mettler-ag204`` plugin, for example, has the ability to interface with multiple Mettler Toldedo AG-204 scales, and declares them as several sources.
The Cyckei interface then has the ability to assign different scales to individual channels for data capture.
The exact parts of each source entry may depend on the individual plugin, but a port number and meta information are pretty standard.
Port numbers and other information should be changed as necessary for your setup.


Running
-------
Once configured, the different data sources exposed by plugins will be visible in the Cyckei Client.

.. figure:: _static/images/plugins.png

Once available, it is as simple as selecting the source in the corresponding dropdown to assign a device to each channel.
Once assigned, data from the device will be merged into the output file for that channel.

Custom Plugins
--------------
Custom plugins are simple to create, especially if there is an established method of reading device data into python already.
It is recommended that you follow the scheme of the [Randomizer Plugin](https://github.com/cyclikal/cyp-randomizer).

The main component of any plugin is the ``PluginController`` class.
This class is a child of Cyckei's BaseController class which provides a number of helper functions including the very important ``read()`` method.
The ``cyp-andomizer`` package includes in-line documentation to demonstrate the changes that need to be made to create a plugin for a new device.
The process is fairly self-explanatory, but generally most setup should be put in the ``load_sources()`` method, and any steps to capture data should be put into the ``read()`` method.
It is good practice to create some basic documentation to accompany a custom plugin, particularly if additional drivers need to be installed.

Another good example is the ``mettlerscale`` plugin, which gathers data from a Mettler-Toledo balance.
In addition to having a ``read()`` function, this plugin utilizes a ``MettlerLogger`` object to interact with each individual scale on a different port.
