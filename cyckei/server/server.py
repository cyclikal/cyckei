"""Main script run by server application"""

import logging
import time
import traceback
from os.path import isfile, basename
from collections import OrderedDict
import json
import zmq
from pyvisa import VisaIOError

from .protocols import STATUS, CellRunner
from . import keithley2602 as device_module

logger = logging.getLogger('cyckei_server')


def main(config, plugins, plugin_names):
    """Begins execution of Cyckei Server.

    Sets up the socket for communication with a client and starts the event_loop to 
    process commands.

    Args:
        config (dict): Holds Cyckei launch settings.
        plugins (list): A list of PluginControllers extending the BaseController object.
        plugin_names (dict):  A dict with a key of the plugin name and a value of the of the specific plugin instance's name.
    |
    """

    logger.info(
        f"Initializing Cyckei Server {config['versioning']['version']}")

    # Create Server's ZMQ Socket
    logger.debug("Binding socket")
    try:
        context = zmq.Context(1)
        socket = context.socket(zmq.REP)
        socket.bind("{}:{}".format(config["zmq"]["server-address"],
                                   int(config["zmq"]["port"])))

    except zmq.error.ZMQError as error:
        logger.critical(
            "It appears the server is already running: {}".format(error))
        return
    logger.debug("Socket bound successfully")

    # Start server event loop
    event_loop(config, socket, plugins, plugin_names, device_module)


# def handler(exception_type, value, tb):
#     """Handler which writes exceptions to log and terminal"""
#     exception_list = traceback.format_exception(exception_type, value, tb)
#     text = "".join(str(l) for l in exception_list)
#     logger.exception(text)
#     print(text)


def event_loop(config, socket, plugins, plugin_names, device_module):
    """Main start method and loop for server application.

    Connects cycling channels, sets up CellRunners for controlling channels,
    waits for runners then processes and discards them as necessary. Also records
    the channel statuses.
        
    Args:
        config (dict): Holds Cyckei launch settings.
        device_module (module): A module (in this case keithley.py) that includes a definition for DeviceController(gpib_addr (int) ). 
        plugins (list): A list of PluginControllers extending the BaseController object.
        plugin_names (dict):  A dict with a key of the plugin name and a value of the of the specific plugin instance's name.
        socket (zmq.Socket): An object that acts as a socket that can send and receive messages.
    |
    """
    try:
        logger.debug("Starting server event loop")

        # Create list of sources (outputs)
        keithleys = []
        sources = []

        # Initialize sources
        logger.info("Attemping {} channels.".format(len(config["channels"])))
        for channel in config["channels"]:
            gpib_addr = channel["gpib_address"]
            keithley = None
            for k in keithleys:
                if gpib_addr == k.gpib_addr:
                    keithley = k
            if keithley is None:
                try:
                    keithley = device_module.DeviceController(gpib_addr)
                except (ValueError, VisaIOError) as e:
                    logger.error("Could not establish connection: "
                                 "Channel {}, GPIB {}.".format(
                                     channel["channel"],
                                     channel["gpib_address"]
                                 )
                                 )
                    logger.error(e)
                    continue

                keithleys.append(keithley)
            source_object = keithley.get_source(channel["keithley_channel"],
                                                channel=channel["channel"])
            sources.append(source_object)

        logger.info("Connected {} channels.".format(len(sources)))

        # Initialize socket
        runners = []

        logger.info(
            "Socket bound to port {}. Entering main loop.".format(
                int(config["zmq"]["port"]))
        )

        time.sleep(2)
        max_counter = 1e9
        counter = 0
        initial_time = time.time()
        data_path = config["arguments"]["record_dir"]

        while True:
            current_time = '{0:02.0f}.{1:02.0f}'.format(
                *divmod((time.time() - initial_time) * 60, 60)
            )

            # check messages on the socket and execute necessary tasks
            # ideally this would happen on a separate thread
            # but it might not be necessary
            # main loop without problem
            # logger.debug("Processing socket messages")
            process_socket(config, socket, runners, sources, current_time,
                           plugins, plugin_names)

            # execute runners or sleep if none
            if runners:
                # logger.debug("Looping over runners")
                # Sort runners from most urgent to least urgent
                runners = sorted(runners, key=lambda x: x.next_time)

                channels_message = ""
                timing_message = ""

                for runner in runners:

                    if runner.status == STATUS.pending:
                        runner.run()
                    elif runner.status == STATUS.started:
                        # Don't bother with runners more than 1 second out
                        relative_next_time = runner.next_time - time.time()
                        channels_message = channels_message + "/" \
                            + runner.channel
                        timing_message = (timing_message
                                          + "/"
                                          + str(relative_next_time)[:5])

                        if relative_next_time <= 0.0:
                            runner.run()
                # logger.debug(
                #    "Channel {} will be \
                #     checked in approx {} seconds...".format(
                #        channels_message[1:], timing_message[1:]
                #     )
                # )

                # Discard completed runners
                ipop = sorted(
                    [i for i, p in enumerate(runners)
                        if p.status == STATUS.completed],
                    reverse=True
                )
                for i in ipop:
                    runners.pop(i)

            time.sleep(0.1)

            # records server status
            record_data(data_path, info_all_channels(runners, sources))

            # mod it by a large value to avoid ever overflowing
            counter = counter % max_counter + 1
    except Exception as e:
        logger.error("Failed with uncaught exception:")
        logger.exception(e)

def record_data(data_path, data):
    """Saves server status to a file.

    Uses the data_path to open an existing or new file, converts the data to a json,
    then writes the data to the file. If there is already existing data in channels
    it is not overwritten by the same channels now being empty.
        
    Args:
        data (dict): The data to be stored in a file.
        data_path (str): The path to the area where the user wants the server_data file stored.
    |
    """
    data_path = data_path + "\\server_data.txt"
    #loads server_file into a dict
    try:
        data_file = open(data_path, "r")
        old_data = json.load(data_file)
        data_file.close()
        #This section is to avoid overwriting the previous protocol with the nulls
        #from when a cell runner finishes and is deleted from runners
        for i in old_data:
            if old_data[i]["state"] != None and data[i]["state"] == None:
                data[i] = old_data[i]
    # The server_data file does not exist yet
    except IOError:
        pass
    #writes the data to the server file
    data_file = open(data_path, "w")
    data_file.write(json.dumps(data))
    data_file.close()

def process_socket(config, socket, runners, sources, server_time,
                   plugins, plugin_names):
    """Checks the running socket for messages and then parses them into actions to take.

    Args:
        config (dict): Holds Cyckei launch settings.
        plugins (list): A list of PluginControllers extending the BaseController object.
        plugin_names (dict):  A dict with a key of the plugin name and a value of the of the specific plugin instance's name.
        runners (list): A sorted list of active CellRunner objects.
        server_time (float): The time on the server (unused in the function)
        socket (zmq.REP socket): Receives messages in a non-blocking way.
            If a message is received it processes it and sends a response
        sources (list): A list of all of the Keithley channels connected to the server.
    |
    """

    # Check to see if there are new events on the socket
    # only waits 1 millisecond on the polling
    events = socket.poll(1)

    if events > 0:
        msg = socket.recv_json()

        if msg is not None:
            response = {"response": None, "message": None}
            try:
                # a message has been received
                fun = msg["function"]

                kwargs = msg.get("kwargs", None)
                # response = {"version": __version__, "response": None}
                resp = "Unknown function"
                logger.debug("Packet request received: {}".format(fun))
                if fun == "start":
                    try:
                        resp = start(kwargs["channel"], kwargs["meta"],
                                     kwargs["protocol"], runners, sources,
                                     plugins)
                    except Exception as e:
                        resp = "Error occured when running script."
                        logger.warning(e)

                elif fun == "pause":
                    resp = pause(kwargs["channel"], runners)

                elif fun == "resume":
                    resp = resume(kwargs["channel"], runners)

                elif fun == "test":
                    resp = test(kwargs["protocol"])

                elif fun == "stop":
                    resp = stop(kwargs["channel"], runners)

                elif fun == "ping":
                    port = socket.getsockopt_string(
                        zmq.LAST_ENDPOINT
                    ).split(":")[-1]
                    resp = "True: server is running on port {}".format(port)

                elif fun == "info_plugins":
                    plugin_info = []
                    for plugin in plugins:
                        info = {
                            "name": plugin.name,
                            "description": plugin.description,
                            "sources": plugin.names
                        }
                        plugin_info.append(info)
                    resp = plugin_info

                elif fun == "info_channel":
                    resp = info_channel(kwargs["channel"], runners, sources)

                elif fun == "info_all_channels":
                    resp = info_all_channels(runners, sources)

                elif fun == "info_server_file":
                    resp = info_server_file(config)

                logger.debug("Sending response: {}".format(resp))
                response["response"] = resp

                socket.send_json(response)
            except (IndexError, ValueError, TypeError, NameError) as exception:
                logger.exception(exception)
                response["response"] = (
                    "Call failed with error: {}\ntraceback:\n{}".format(
                        exception,
                        traceback.format_exc()
                    )
                )
                response["message"] = msg
                logger.debug("Error occurred, sent response: {}".format(
                    response['response']))
                socket.send_json(response)

def info_server_file(config):
    """Return the dict of channels in the server file
        
    Args:
        config (dict): Holds Cyckei launch settings.

    Returns:
        dict: The json data of channels recorded in a file, converted to a dict.
    |
    """
    data_path = config["arguments"]["record_dir"] + "\\server_data.txt"
    #loads server_file into a dict
    try:
        data_file = open(data_path, "r")
        server_data = json.load(data_file)
        data_file.close()
    #Server file doesn't exist
    except IOError:
        server_data = None
    return server_data
    
    

def info_all_channels(runners, sources):
    """Return info on all channels
        
    Args:
        runners (list): A sorted list of active CellRunner objects.
        sources (list): A list of all of the Keithley channels connected to the server.

    Returns:
        dict: A dictionary of dictionaries that each hold info from their respective
        CellRunner's meta, e.g. path, status, current, voltage, etc.
    |
    """
    info = {}
    for source in sources:
        info[str(source.channel)] \
            = info_channel(source.channel, runners, sources)

    return info


def info_channel(channel, runners, sources):
    """Return info about the specified channel.
        
    Args:
        channel (int): The channel number associated with the desired Keithley.
        runners (list): A sorted list of active CellRunner objects.
        sources (list): A list of all of the Keithley channels connected to the server.

    Returns:
        dict: Information about the requested channel from the CellRunner's
        meta, e.g. path, status, current, voltage, etc.
    |
    """
    info = OrderedDict(channel=channel, path=None, cellid=None, comment=None, protocol_name=None, protocol=None, status=None, state=None,
                       current=None, voltage=None)
    runner = get_runner_by_channel(channel, runners)
    if runner:
        info['path'] = runner.meta['path']
        info['cellid'] = runner.meta['cellid']
        info['comment'] = runner.meta['comment']
        info['protocol_name'] = runner.meta['protocol_name']
        info["status"] = STATUS.string_map[runner.status]
        info["state"] = runner.step.state_str
        try:
            try:
                # this will be the latest measured point
                last_data = runner.step.data[-1]
            except (TypeError, IndexError):
                # this will be the latest reported (written to file) point
                last_data = runner.last_data

            info["current"] = last_data[1]
            info["voltage"] = last_data[2]

        except (TypeError):
            info["current"] = "Not Available"
            info["voltage"] = "Not Available"

    else:
        info["status"] = STATUS.string_map[STATUS.available]
    # for src in sources:
    #     if int(src.channel) == int(channel):
    #         info["current"], info["voltage"] = src.read_iv()
    #         break
    return info


def start(channel, meta, protocol, runners, sources, plugin_objects):
    """Start channel with given protocol.
        
    Args:
        channel (int): The channel number associated with the desired Keithley.
        meta (dict): The metadata about a channel, which is provided to the CellRunner.
        plugin_objects (list): A list of PluginControllers extending the BaseController object. (The same as 'plugins' in other functions of server.py)
        protocol (str): The protocol to be loaded onto a CellRunner.
        runners (list): A sorted list of active CellRunner objects.
        sources (list): A list of all of the Keithley channels connected to the server.

    Returns:
        str: The result message of trying to start a channel.
    |
    """
    # check to see if there is a already a runner on that channel
    meta["channel"] = channel
    if get_runner_by_channel(channel, runners):
        return "Channel {} already in use.".format(channel)

    path = meta["path"]
    if isfile(path):
        return("Log file '{}' already in use.").format(basename(path))
    runner = CellRunner(plugin_objects, **meta)
    # Set the channel source
    for source in sources:
        if runner.channel == source.channel:
            runner.set_source(source)

    # Protocol must be added after source since some
    # protocol steps require knowledge of the source
    runner.load_protocol(protocol)

    if runner.source is None:
        return "Failed to start channel {}. No source found.".format(channel)

    runners.append(runner)
    return "Succeeded in starting channel {}.".format(channel)


def pause(channel, runners):
    """Pauses the specified channel.
        
    Args:
        channel (int): The channel number associated with the desired Keithley.
        runners (list): A sorted list of active CellRunner objects.

    Returns:
        str: The result message of trying to pause a channel.
    |
    """
    success = False
    runner = get_runner_by_channel(channel, runners, status=STATUS.started)
    if runner is not None:
        success = runner.pause()

    if success:
        return "Succeeded in pausing channel {}".format(channel)
    return "Failed in pausing channel {}".format(channel)


def stop(channel, runners):
    """Stop the specified channel.

    Args:
        channel (int): The channel number associated with the desired Keithley.
        runners (list): A sorted list of active CellRunner objects.

    Returns:
        str: The result message of trying to strop a channel.
    |
    """
    success = False
    runner = get_runner_by_channel(channel, runners)
    if runner is not None:
        success = runner.stop()

    if success:
        return "Succeeded in stopping channel {}".format(channel)
    return "Failed in stopping channel {}".format(channel)


def resume(channel, runners):
    """Attempts to resume the specified channel from pause.

    Args:
        channel (int): The channel number associated with the desired Keithley.
        runners (list): A sorted list of active CellRunner objects.

    Returns:
        str: The result message of trying to resume a channel.
    |
    """
    success = False
    runner = get_runner_by_channel(channel, runners, status=STATUS.paused)
    if runner is not None:
        success = runner.resume()

    if success:
        return "Succeeded in resuming channel {}".format(channel)
    return "Failed in resuming channel {}".format(channel)


def test(protocol):
    """Test the specified protocol for compliance.
    
    Args:
        protocol ():

    Returns:
        str: The result message of testing the protocol.
    |
    """
    try:
        runner = CellRunner()
        runner.load_protocol(protocol, isTest=True)
        return "Passed"
    except Exception as e:
        return str(e).splitlines()[-1]


def get_runner_by_channel(channel, runners, status=None):
    """Get runner currently on given channel.

    Args:
        channel (int or str): The channel number associated with the desired Keithley.
        runners (list): A sorted list of active CellRunner objects.
        status (int, optional): The status number associated with different runner statuses. -1 to 5. Defaults to None.

    Returns:
        CellRunnner: Returns the runner serving the given channel, returns None otherwise.
    |
    """
    if status is None:
        for runner in runners:
            if runner.channel == channel or int(runner.channel) == channel:
                return runner
    else:
        for runner in runners:
            if runner.channel == channel and runner.status == status:
                return runner

    return None
