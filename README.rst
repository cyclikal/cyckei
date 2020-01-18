Cyckei
======

Details about Cyckei can be found in our `documentation`_.

Cyckei is a battery cycling application designed to carry out charging, discharging, and data collection on lithium-ion cells. It is designed to interface with the Keithley 2602A/B SourceMeter for calorimetry testing, but can be used in a variety or setups.

The application uses a Python-like scripting format in order to write cycles that are carried out on cells. To learn more about scripts, read the Creating Scripts section in our `documentation`_ or look at the example below.

::

    for i in range(3):
      AdvanceCycle()
      CCCharge(0.1, reports=(("voltage", 0.01), ("time", ":5:")), ends=(("voltage", ">", 4.2), ("time", ">", "4::")))
      CCDischarge(0.1, reports=(("voltage", 0.01), ("time", ":5:")), ends=(("voltage", "<", 3.0), ("time", ">", "4::")))
      Rest(reports=(("time", "::1"),), ends=(("time", ">", "::15"),))

Cyckei is open source, and we encourage users to modify the code to fit a given setup. Details on contributing to the project are in the Contributing of our `documentation`_.

Cyckei is currently developed and maintained by Gabriel Ewig and Vincent Chevrier at Cyclikal, LLC. For more information about Cyclikal, visit `cyclikal.com`_.

.. figure:: docs/_static/images/client-low.png
  Screen shot of Cyckei channel tab on Mac OS.

.. _cyclikal.com: http://cyclikal.com
.. _documentation: https://docs.cyclikal.com/projects/cyckei/en/stable/
