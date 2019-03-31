# Cyckei Client Help
#### A battery cycler written in Python 3
---

## Controlling the Server
Cyckei uses a server background process to interface directly with Keithley instruments.
This allows cycles to continue running even if the client is closed abruptly or becomes slow.
The server is started automatically with the client, or can be started directly with the following command:

    python cyckei.pyw -s

The server can be controlled from the "Server" menu of the client application.


## Starting a cycle
Various attributes of the cycle must be set in order to start a cycle. All of these have default values to prevent errors, however it is a good idea to manually specify them. The following should be set under the desired channel:

|Option      |Type    |Description                                                                                                       |Default           |
|:-----------|:------:|:-----------------------------------------------------------------------------------------------------------------|:----------------:|
|Script      |dropdown|Script with desired protocol. Automatically loaded from the 'cycleScripts' folder in the program's root directory.|First scanned file|
|Cell ID     |text    |Identification for cell. Recorded to output file.                                                                 |0                 |
|Log file    |text    |Path to output file. Placed in the specified logs folder.                                                         |"defaultLog.txt"  |
|Mass        |text    |Mass of cell.                                                                                                     |1                 |
|Comment     |text    |Requestor's comment for cycle. Recorded to output file.                                                           |"No Comment"      |
|Package type|dropdown|Type of cell package. Recorded to output file.                                                                    |"Pouch"           |
|Cell type   |dropdown|Type of cell. Recorded to output file.                                                                            |"Full"            |
|Requestor   |dropdown|Name of person starting cycle.                                                                                    |"Unspecified"     |

The available buttons can be used to Start, Stop, Pause, or Resume the protocol.
Note that the program will overwrite any existing output files if an identical log file is specified.
The *Fill* button allows you to automatically create a log file name based on the entered cell ID. This takes the format of [id]A.pyb where the "A" designates which log file within a series.

## Creating Scripts
Scripts can be created in the scripts tab of the client.
This editor will automatically load the default included scripts, but can be used to open and edit additional files.

Scripts are written in regular python code, and can contain loops and other statements to control cycle flow. There are seven built in protocols to control the cycler. Most of these protocols take some or all of the following parameters:

|Parameter|Description                                                                       |Format                                                              |
|:--------|:---------------------------------------------------------------------------------|:-------------------------------------------------------------------|
|Value    |Set a certain voltage or current to run at.                                       |float                                                               |
|Reports  |Set intervals of time and/or change in voltage or current to record at.           |reports=(("current", *float*), ("time", "*int*:*int*:*int*"))       |
|Ends     |Set threshold of time and/or change in voltage or current to end current protocol.|ends=(("current", "<", *float*), ("time", ">", "*int*:*int*:*int*"))|

The following protocols are available:

|Protocol    |Description                                              |Parameters          |Example                                                                                                              |
|:-----------|:--------------------------------------------------------|:------------------:|:--------------------------------------------------------------------------------------------------------------------|
|AdvanceCycle|Start recording under next cycle in output file.         |None                |AdvanceCycle()                                                                                                       |
|CCCharge    |Charge at a set current.                                 |Value, Reports, Ends|CCCharge(0.1, reports=(("voltage", 0.01), ("time", ":5:")), ends=(("voltage", ">", 4.2), ("time", ">", "4::")))      |
|CCDischarge |Discharge at a set current.                              |Value, Reports, Ends|CCDischarge(0.1, reports=(("voltage", 0.01), ("time", ":5:")), ends=(("voltage", "<", 3.0), ("time", ">", "4::")))   |
|CVCharge    |Charge at a set voltage.                                 |Value, Reports, Ends|CVCharge(4.2, reports=(("current", 0.01), ("time", ":5:")), ends=(("current", "<", 0.005), ("time", ">", "24::")))   |
|CVDischarge |Discharge at a set voltage.                              |Value, Reports, Ends|CVDischarge(4.2, reports=(("current", 0.01), ("time", ":5:")), ends=(("current", "<", 0.005), ("time", ">", "24::")))|
|Rest        |Record at a set interval.                                |Reports, Ends       |Rest(reports=(("time", "::1"),), ends=(("time", ">", "::15"),))                                                      |
|Sleep       |Record at a set interval and turn channel off in between.|Reports, Ends       |Sleep(reports=(("time", ":1:0"),), ends=(("time", ">", "::15"),))                                                    |

An example script is shown below.
There is also a simple script saved in the scripts folder which is available whenever the client is started.

    for i in range(3):
      AdvanceCycle()
      CCCharge(0.1, reports=(("voltage", 0.01), ("time", ":5:")), ends=(("voltage", ">", 4.2), ("time", ">", "4::")))
      CCDischarge(0.1, reports=(("voltage", 0.01), ("time", ":5:")), ends=(("voltage", "<", 3.0), ("time", ">", "4::")))
      Rest(reports=(("time", "::1"),), ends=(("time", ">", "::15"),))

Scripts are automatically checked when they are sent to the server.
They can also be manually checked by clicking the "Check" button in the scripts tab.
Checking a script ensures that (1) the script only contains legal arguments and (2) can be loaded by the server without immediate errors.
Checking your scripts is a good practice to mitigate possible formatting issues and errors.
However, care should still be taken while writing scripts as they are executed as any other python code within the application.

## Working With Batches
The "Batch" menu allows large tests with multiple cells to be run more easily.
Saving a batch writes the IDs and log files of each channel to the "batch" file which can be loaded later.
The "Fill All" and "Increment" options allow you to automatically create log files based on each ID, and increment the last letter to indicate which test is being run on the same cell.

## Viewing Logs
Logs are created to document measurements from each cell throughout it's cycle.
They also have details about the cell and the cycle that was run on it.
Log files are saved to the "tests" folder specified in the configuration under the specified name.
To view a log from the client application, just open the logging tab.
All logs are automatically loaded on startup, and new or updated ones can be viewed after clicking reload.
Although you can copy the contents of a log file to an excel spreadsheet, log files *should not* be opened with excel or another application directly.
Doing this can cause the file to become locked and prevent Cyckei from editing it.

## Editing Configuration
Editing the configuration file is crucial for the client to function properly. Any custom configuration files should be written in JSON and should mirror the default config.json in the program's root directory. Each section is described in more detail below:

-   **channels** - A list of channels currently connected to the computer.
    -   *channel (string)* - Channel number for identification within application
    -   *gpib_address (int)* - Hardware address of GPIB interface. Can be found with a NI VISA application or the following python code:

        import visa
        resource_manager = visa.ResourceManager()
        print(resource_manager.list_resources())
    -   *keithley_model (string)* - Model number of keithley being used.
    -   *keithley_channel (string)* - Particular channel on said keithley (a or b).


-   **zmq** - A dictionary of properties that control how the client and server communicate.
    -   *port* - Port to communicate over.
    -   *client*
        -   *address (string)* - Address for the client to connect to. Usually localhost.
        -   *retries (int)*
        -   *timeout (int)*
    -   *server*
        -   *address (string)* - Address for the server to listen on. Usually all.


-   **verbosity** - The amount of information to be saved to log files. Generally should be set to 20, but the following levels can also be used. Lower values print more information for debugging purposes.
    -   *Critical* - 50
    -   *Error* - 40
    -   *Warning* - 30
    -   *Info* - 20
    -   *Debug* - 10
    -   *Notset* - 0



Here is an example configuration file for a simple setup running on port 5556 with one Keithley with address 5:

    {
        "channels": [
            {
                "channel": "1",
                "gpib_address": 5,
                "keithley_model": "2602A",
                "keithley_channel": "a"
            },
            {
                "channel": "2",
                "gpib_address": 5,
                "keithley_model": "2602A",
                "keithley_channel": "b"
            }
        ],
        "zmq":{
            "port": 5556,
            "client":{
              "address":"tcp://localhost",
              "retries": 3,
              "timeout": 2500
            },
            "server":{
              "address":"tcp://*"
            }
        },
        "verbosity": 20,
    }
