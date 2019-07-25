Changes & Features
==================


0.0 - 08/16/2018
----------------

Original version of Cyckei developed by Vincent Chevrier and Gabriel
Ewig for the Lithium-ion Battery Lab.

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
-  0.1.dev4, 06/02/2019 -- All primary buttons execute as separate
   thread
-  0.1.dev5, 06/03/2019 -- Message Boxes and status updates are sent
   through signal/slot pattern
-  0.1.dev6, 06/12/2019 -- Overhaul visual appearance for simplicity
-  0.1.dev7, 06/12/2019 -- Separate client and server packages for
   proper file access during distribution
-  0.1.dev8, 06/13/2019 -- Fix over-threading and application exit
-  0.1.dev9, 06/27/2019 -- Move server to applet and improve OS
   integration
-  0.1.dev10, 06/27/2019 -- A bunch of script tab fixes and separated
   status and feedback on the channel tab

Release Candidates
^^^^^^^^^^^^^^^^^^

-  0.1rc1, 06/28/2019 -- Initial Release Candidate
-  0.1rc2, 06/29/2019 -- Fixed some bugs, enable MenuBar on Windows, and
   added exception logging


0.2 Alviss
----------

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

Development Releases
^^^^^^^^^^^^^^^^^^^^

-  0.2.dev1, 7/15/2019 -- Improve Documentation
-  0.2.dev2, 7/17/2019 -- Switch to PyInstaller build system
-  0.2.dev3, 7/20/2019 -- Simplify client codebase, unify common
   functions, improve UI
-  0.2.dev4, 7/21/2019 -- Introduce Sphinx and add contribution
   documentation
-  0.2.dev5, 7/24/2019 -- Small adjustments to prepare release
   candidates

Release Candidates
^^^^^^^^^^^^^^^^^^

-  0.2rc1, 7/24/2019 -- Fix some small bugs
-  0.2rc2, 7/24/2019 -- Fix bugs, reduce server calls, and document
   issues
-  0.2rc3, 0/00/0000 -- TBD


0.3 Tenjin
----------

Add significant features which make the platform more efficient. This
includes automatic scripting, better batch management, pretty log view,
multi-folder scripts, and more.

Development Releases
^^^^^^^^^^^^^^^^^^^^

- 0.3.dev1, 0/00/0000 -- TBD

Release Candidates
^^^^^^^^^^^^^^^^^^

- 0.3rc1, 0/00/0000 -- TBD


Planned Features
----------------
- Client Interface
  - Automatic scripting
  - Better batch management
  - Pretty log wiew
  - Multi-folder script storage
- Server software
  - "Plug-in" style core (lua) script management for different devices
  - Threading and improved performance for massive cycles
  - Auto shutoff due to crash or inactivity
  - Possibly better logging format, dependent on Cell Explorer
- Hardware Support
  - Complete Support for Mac and Linux
  - Make equivalent for Windows
  - Simplify VISA and driver installation for end user


Bug Tracker
-----------

-  ``Segmentation Fault: 11`` on Darwin
