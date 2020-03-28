Changes & Features
==================


0.0 Yin - 11/14/2018
----------------

Original version of Cyckei.

Notable Changes
^^^^^^^^^^^^^^^

-  Create complex UI to handle all software functions
-  Implement cycling protocols such as CCCharge and Sleep


0.1 Vayu - 07/2/2019
--------------------

Intended to significantly improve the performance and responsiveness of
the application by improving the execution pattern and introducing
threading to the Qt interface. Also overhauls the UI and brings many
components up to date.

Notable Changes
^^^^^^^^^^^^^^^

-  Run client communication functions as synchronous worker
-  Switch GUI from PyQt5 to PySide2
-  Improve layout and scaling of UI elements

Development Releases
^^^^^^^^^^^^^^^^^^^^

-  0.1.dev1, 05/26/2019 -- Initial Cyclikal commits
-  0.1.dev2, 05/30/2019 -- Adjust layout and switch to PySide2
-  0.1.dev3, 05/31/2019 -- Create threaded workers for each action
-  0.1.dev4, 06/02/2019 -- All primary buttons execute as separate thread
-  0.1.dev5, 06/03/2019 -- Message Boxes and status updates are sent through signal/slot pattern
-  0.1.dev6, 06/12/2019 -- Overhaul visual appearance for simplicity
-  0.1.dev7, 06/12/2019 -- Separate client and server packages for proper file access during distribution
-  0.1.dev8, 06/13/2019 -- Fix over-threading and application exit
-  0.1.dev9, 06/27/2019 -- Move server to applet and improve OS integration
-  0.1.dev10, 06/27/2019 -- A bunch of script tab fixes and separated status and feedback on the channel tab

Release Candidates
^^^^^^^^^^^^^^^^^^

-  0.1rc1, 06/28/2019 -- Initial Release Candidate
-  0.1rc2, 06/29/2019 -- Fixed some bugs, enable MenuBar on Windows, and added exception logging


0.2 Alviss - 8/01/2019
----------------------

Smaller update focused on simplifying the code to aid in further
development. This includes unifying as many commonly used functions as
possible and adding code documentation. Also adds single file
executables because they're fun.

Notable Changes
^^^^^^^^^^^^^^^

-  Unify common functions and generally refactor codebase
-  Support distribution of compiled executables
-  Improve documentation
-  Small UI adjustments including dark mode
-  Rewrite "Read" and "StatusUpdate" functions for better performance and functionality

Development Releases
^^^^^^^^^^^^^^^^^^^^

-  0.2.dev1, 7/15/2019 -- Improve Documentation
-  0.2.dev2, 7/17/2019 -- Switch to PyInstaller build system
-  0.2.dev3, 7/20/2019 -- Simplify client codebase, unify common functions, improve UI
-  0.2.dev4, 7/21/2019 -- Introduce Sphinx and add contribution documentation
-  0.2.dev5, 7/24/2019 -- Small adjustments to prepare release candidates

Release Candidates
^^^^^^^^^^^^^^^^^^

-  0.2rc1, 7/24/2019 -- Fix some small bugs
-  0.2rc2, 7/24/2019 -- Fix bugs, reduce server calls, and document issues
-  0.2rc3, 7/30/2019 -- Improve status updates and "Read Cell" function
-  0.2rc4, 7/31/2019 -- Fix file naming while reading cell, unify versioning
-  0.2rc5, 8/01/2019 -- Report pre-logging runtime errors


0.2.1
-----

Hotfix updates to Alviss. Includes fixes to delay and improper current measurement and a basic test suite.

Notable Changes
^^^^^^^^^^^^^^^

-  Fixes to measurement and report timing
-  Basic test suite

Development Releases
^^^^^^^^^^^^^^^^^^^^

-  0.2.1.dev1, 8/19/2019 -- Fix issues with delay and improper current measurement


0.3 Tenzin
----------

Rebuilding existing interfaces after fixing an OS-level threading error.
Adds Cyckei Explorer for editing scripts and viewing recent log files.
Now, again, uses PyPI release system as opposed to freezing.

Development Releases
^^^^^^^^^^^^^^^^^^^^

- 0.3.dev1, 1/16/2020 -- Implements Cyckei Explorer and rebuilds distribution system
- 0.3.dev2, 1/31/2020 -- Rebuild check, pause, & resume functionality
- 0.3.dev3, 3/28/2020 -- Add plugin scheme to support additional data collection

Release Candidates
^^^^^^^^^^^^^^^^^^

- 0.3rc1, 0/00/0000 -- TBD


Possible Features
----------------
- Client Interface
   - Better batch management
   - Multi-folder script storage
   - Script highlighting
- Server Software
   - "Plug-in" style core (lua) script management for different devices
   - Implement Cython and threading for improved performance with massive cycles
- Hardware Support
   - Complete Support for Linux
   - Simplify VISA and driver installation for end user
- Miscellaneous
   - Automated release delivery
   - Add test suite


Bug Tracker
-----------

-  Line flickering
