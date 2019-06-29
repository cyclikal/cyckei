# Cyckei Change-log and Roadmap

## 0.0 - 08/16/2018
Original version of Cyckei developed by Vincent Chevrier and Gabriel Ewig for the Lithium-ion Battery Lab at 3M.

## 0.1 Vayu
Intended to significantly improve the performance and responsiveness of the application by improving the execution pattern and introducing threading to the Qt interface. Also overhauls the UI and brings many components up to date.

#### Notable Changes
*   Run client communication functions as QRunnable
*   Switch GUI from PyQt5 to PySide2
*   Improve layout and scaling of UI elements

#### Development Releases (Formerly 0.0.1.devX)

*   0.1.dev1, 05/26/2019 -- Initial Vayu release
*   0.1.dev2, 05/30/2019 -- Adjust layout and switch to PySide2
*   0.1.dev3, 05/31/2019 -- Create threaded workers for each action
*   0.1.dev4, 06/02/2019 -- All primary buttons execute as separate thread
*   0.1.dev5, 06/03/2019 -- Message Boxes and status updates are sent through signal/slot pattern
*   0.1.dev6, 06/12/2019 -- Overhaul visual appearance for simplicity
*   0.1.dev7, 06/12/2019 -- Separate client and server packages for proper file access during distribution
*   0.1.dev8, 06/13/2019 -- Fix over-threading and application exit
*   0.1.dev9, 06/27/2019 -- Move server to applet and improve OS integration
*   0.1.dev10, 06/27/2019 -- A bunch of script tab fixes and separated status and feedback on the channel tab

#### Release Candidates

*   0.1rc1, 06/28/2019 -- Initial Release Candidate
*   0.1rc2, 06/29/2019 -- Fixed some bugs, enable MenuBar on Windows, and added exception logging

#### Bug Tracker
*   None currently known

## 0.2
Focused on simplifying the code to aid in further development. This includes unifying as many commonly used functions as possible, and adding code documentation.
