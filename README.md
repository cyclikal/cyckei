# Cyckei
#### A battery cycler written in Python 3
---

## About
Cyckei is a battery cycling application designed to carry out charging, discharging, and data collection on lithium-ion cells. It is developed to interface with the Keithley 2602A/B SourceMeter, but could be modified to work with other instruments. The application uses a simple scripting format in order to write cycles that are carried out on cells.

Cyckei is currently developed and maintained by Gabriel Ewig and Vincent Chevrier at Cyclikal, LLC. For more information about Cyclikal, visit <http://cyclikal.com/>

## System Requirements
Cyckei is currently developed, tested, and deployed using the latest version of Python 3 running on Windows 10. It has been used on various other configurations including Mac and Linux, but may require additional setup and stability testing.

Cyckei relies on the PyVISA wrapper to communicate with any devices, and generally requires an additional VISA library as well as a driver for the device or adaptor which PyVISA controls. We use the National Instruments GPIB-USB-HS adaptors, which require both the NI VISA library and the NI 488.2 GPIB driver. The following Python code is helpful to verify whether PyVISA can find your devices.

    import visa
    rm = visa.ResourceManager()
    print(rm.list_resources())

For more information about installing system components, see the `INSTALL` file.

## Installation
See the `INSTALL` file for more information.

## How-To
Upon first launch, Cyckei will create a `cyckei` directory in the user's home folder to hold scripts, test results, logs, and configuration. Before running tests, Cyckei must be configured to properly interface with any devices. Each channel should be setup in the `config.json` file with the correct GPIB address and any other relevant information. A default configuration is automatically generated, and instructions on further configuration can be found in the `HELP` file.
