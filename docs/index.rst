.. toctree::
  :maxdepth: 3
  :caption: Contents:
  :hidden:

  install
  usage
  plugins
  contributing
  changes
  methods


About the Cyckei Project
========================
Cyckei is a battery cycling application designed to carry out charging, discharging, and data collection on lithium-ion cells. It is designed to interface with the Keithley 2602A/B SourceMeter for calorimetry testing, but can be used in a variety or setups.

The application uses a Python-like scripting format in order to write cycles that are carried out on cells. To learn more about scripts, read the :ref:`Creating Scripts` section or look at the example below.

::

  for i in range(3):
    AdvanceCycle()
    CCCharge(0.1, reports=(("voltage", 0.01), ("time", ":5:")), ends=(("voltage", ">", 4.2), ("time", ">", "4::")))
    CCDischarge(0.1, reports=(("voltage", 0.01), ("time", ":5:")), ends=(("voltage", "<", 3.0), ("time", ">", "4::")))
    Rest(reports=(("time", "::1"),), ends=(("time", ">", "::15"),))

Cyckei is open source, and we encourage users to modify the code to fit a given setup. Details on contributing to the project are in our :doc:`contributing` section.

Cyckei is currently developed and maintained by Vincent Chevrier at Cyclikal LLC, Clark Ohnesorge, and Gabriel Ewig. For more information about Cyclikal, visit `cyclikal.com`_.

.. figure:: _static/images/client.png

  Screen shot of Cyckei channel tab on Mac OS.

.. _cyclikal.com: https://cyclikal.com
