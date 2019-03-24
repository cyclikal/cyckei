# Cyckei Client Information
#### A battery cycler written in Python 3
---

## About
Cyckei is a battery cycling application designed to interface with the Keithley 2602A/B SourceMeter.
Two applications, a server and a client, are used to issue commands to the Keithley and make measurements.
The application uses a simple scripting format in order to write cycles that are carried out on cells.

Cyckei is currently developed and maintained by Cyclikal, LLC.

## How-To
Before the first launch, be sure to edit the config.json file as described in the HELP.md file.
To start the application, double-click the cyckei.bat file or run the following command from the Cyckei installation folder.
The "-s" flag can be used to start the server independently, but this is not necessary as it will be called by the client automatically.

    pythonw cyckei.py

For more details on using the application, refer to the HELP.md file or go to Menu > Help from within the client.

## Dependencies
Cyckei is currently developed and tested on the latest version of Vanilla Python 3, but should work on most installations including Anaconda. We use Windows 10 for both development and deployment.

*The following additional modules are required, and should be installed with pip.*
* pyvisa
* PyQt5
* zmq


    pip install pyvisa PyQt5 zmq

  In addition, there may be additional drivers necessary depending on how you interface with the Keithley SourceMeter. We use the National Instruments GPIB-USB-HS adaptors which require NI's 488.2 driver and NI-VISA. There is a python based visa library included with py-visa, but this has not been tested with Cyckei.
