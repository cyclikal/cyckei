# Cyckei Changelog and Roadmap

## 0.0 - 08/16/2018
Original version of Cyckei developed by Vincent Chevrier and Gabriel Ewig for the Lithium-ion Battery Lab at 3M.

## 0.1 Vayu
Intended to significantly improve the performance and responsiveness of the application by improving the execution pattern and introducing threading to the Qt interface.

#### Notable Changes
*   Run client communication functions as QRunnable
*   Switch GUI from PyQt5 to PySide2
*   Improve layout and scaling of UI elements

#### Development Releases (Formerly 0.0.1.devX)

*   0.1.dev1, 05/26/2019 -- Initial Vayu release
*   0.1.dev2, 05/30/2019 -- Adjust layout and switch to PySide2
*   0.1.dev3, 05/31/2019 -- Create threaded workers for each action
*   0.1.dev4, 06/02/2019 -- All primary buttons execute as separate thread
*   0.1.dev5, 06/03/2019 -- Messsage Boxes and status updates are sent through signal/slot pattern
*   0.1.dev6, 06/12/2019 -- Overhaul visual appearance for simplicity

## 0.2
Small update focused on simplifying the code to aid in further development.
