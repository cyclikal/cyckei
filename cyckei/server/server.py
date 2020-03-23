"""Main script run by server application"""

import logging
import time
import traceback
from os.path import isfile, join, basename
from collections import OrderedDict
from importlib.util import spec_from_file_location, module_from_spec

import zmq
from visa import VisaIOError

from .protocols import STATUS, CellRunner

logger = logging.getLogger('cyckei')


def main(config):
    """
    Begins execution of Cyckei Server.

    Args:
        record_dir: Optional path to recording directory.
    Returns:
        Result of app.exec_(), Qt's main event loop.

    """
    logger.info(f"Initializing Cyckei Server {config['version']}")

    # Create Server's ZMQ Socket
    logger.debug("Binding socket")
    try:
        context = zmq.Context(1)
        socket = context.socket(zmq.REP)
        socket.bind("{}:{}".format(config["zmq"]["server-address"],
                                   config["zmq"]["port"]))

    except zmq.error.ZMQError as error:
        logger.critical(
            "It appears the server is already running: {}".format(error))
        return
    logger.debug("Socket bound successfully")

    # Initialize Device Plugins
    logger.info(f"Loading device: {config['device-plugin']}")
    device_file = join(config["record_dir"], "plugins",
                       f"{config['device-plugin']}.py")
    if isfile(device_file):
        spec = spec_from_file_location(f"model.{config['device-plugin']}", device_file)
        device_module = module_from_spec(spec)
        spec.loader.exec_module(device_module)

    # Initialize Data Plugins
    logger.info(f"Loading plugins: {config['data-plugins']}")
    plugins = []
    for plugin in config["data-plugins"]:
        plugin_file = join(config["record_dir"], "plugins", f"{plugin}.py")
        if isfile(plugin_file):
            spec = spec_from_file_location(f"plugin.{plugin}", plugin_file)
            plugin_module = module_from_spec(spec)
            spec.loader.exec_module(plugin_module)
            plugins.append(plugin_module.DataController())

    # Start server event loop
    event_loop(config, socket, plugins, device_module)


# def handler(exception_type, value, tb):
#     """Handler which writes exceptions to log and terminal"""
#     exception_list = traceback.format_exception(exception_type, value, tb)
#     text = "".join(str(l) for l in exception_list)
#     logger.exception(text)
#     print(text)


def event_loop(config, socket, plugins, device_module):
    try:
        """Main start method and loop for server application"""
        logger.debug("Starting server event loop")

        # Create list of sources (outputs)
        keithleys = []
        sources = []

        # Initialize sources
        logger.info("Attemping {} channels.".format(len(config["channels"])))
        for chd in config["channels"]:
            gpib_addr = chd["gpib_address"]
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
                                    chd["channel"],
                                    chd["gpib_address"])
                                 )
                    logger.error(e)
                    continue

                keithleys.append(keithley)
            source = keithley.get_source(chd["keithley_channel"],
                                         channel=chd["channel"])
            sources.append(source)

        logger.info("Connected {} channels.".format(len(sources)))

        # Initialize socket
        runners = []

        logger.info(
            "Socket bound to port {}. Entering main loop.".format(
                config["zmq"]["port"])
        )

        time.sleep(2)
        max_counter = 1e9
        counter = 0
        initial_time = time.time()

        while True:
            current_time = '{0:02.0f}.{1:02.0f}'.format(
                *divmod((time.time() - initial_time) * 60, 60)
            )

            # check messages on the socket and execute necessary tasks
            # ideally this would happen on a separate thread
            # but it might not be necessary
            # main loop without problem
            # logger.debug("cyckei.server.server.main: \
            #               Processing socket messages")
            process_socket(socket, runners, sources, current_time, plugins)

            # execute runners or sleep if none
            if runners:
                # logger.debug("cyckei.server.server.main: \
                #               Looping over runners")
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
                #    "cyckei.server.server.main: channel {} will be \
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

            # mod it by a large value to avoid ever overflowing
            counter = counter % max_counter + 1
    except Exception as e:
        logger.error("Failed with uncaught exception:")
        logger.exception(e)


def process_socket(socket, runners, sources, server_time, plugins):
    """

    Parameters
    ----------
    socket: zmq.REP socket
        Receives messages in a non-blocking way
        If a message is received it processes it and sends a response

    Returns
    -------
        None

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
                if fun == "start":
                    logger.debug("cyckei.server.server.process_socket: \
                        Packet request received: {}".format(fun))
                    try:
                        resp = start(kwargs["channel"], kwargs["meta"],
                                     kwargs["protocol"], runners, sources,
                                     plugins)
                    except Exception:
                        resp = "Error occured when running script."
                    logger.debug("cyckei.server.server.process_socket: \
                        Sending response: {}".format(resp))

                elif fun == "pause":
                    logger.debug("cyckei.server.server.process_socket: \
                        Packet request received: {}".format(fun))
                    resp = pause(kwargs["channel"], runners)
                    logger.debug("cyckei.server.server.process_socket: \
                        Sending response: {}".format(resp))

                elif fun == "resume":
                    logger.debug("cyckei.server.server.process_socket: \
                        Packet request received: {}".format(fun))
                    resp = resume(kwargs["channel"], runners)
                    logger.debug("cyckei.server.server.process_socket: \
                        Sending response: {}".format(resp))

                elif fun == "test":
                    logger.debug("cyckei.server.server.process_socket: \
                        Packet request received: {}".format(fun))
                    resp = test(kwargs["protocol"])
                    logger.debug("cyckei.server.server.process_socket: \
                        Sending response: {}".format(resp))

                elif fun == "stop":
                    logger.debug("cyckei.server.server.process_socket: \
                        Packet request received: {}".format(fun))
                    resp = stop(kwargs["channel"], runners)
                    logger.debug("cyckei.server.server.process_socket: \
                        Sending response: {}".format(resp))

                elif fun == "ping":
                    logger.debug("cyckei.server.server.process_socket: \
                        Packet request received: {}".format(fun))
                    port = socket.getsockopt_string(
                        zmq.LAST_ENDPOINT
                    ).split(":")[-1]
                    resp = "True: server is running on port {}".format(port)
                    logger.debug("cyckei.server.server.process_socket: \
                        Sending response: {}".format(resp))

                elif fun == "info_channel":
                    resp = info_channel(kwargs["channel"], runners, sources)

                elif fun == "info_all_channels":
                    resp = info_all_channels(runners, sources)

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
                logger.debug("cyckei.server.server.process_socket: Error \
                             occurred, sent response: {}".format(
                                response['response']))
                socket.send_json(response)


def info_all_channels(runners, sources):
    """Return info on all channels"""
    info = {}
    for source in sources:
        info[str(source.channel)] \
            = info_channel(source.channel, runners, sources)

    return info


def info_channel(channel, runners, sources):
    """Return info on specified channels"""
    info = OrderedDict(channel=channel, status=None, state=None,
                       current=None, voltage=None)
    runner = get_runner_by_channel(channel, runners)
    if runner:
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


def start(channel, meta, protocol, runners, sources, plugins):
    """Start channel with given protocol"""

    # check to see if there is a already a runner on that channel
    meta["channel"] = channel
    if get_runner_by_channel(channel, runners):
        return "Channel {} already in use.".format(channel)

    path = meta["path"]
    if isfile(path):
        return("Log file '{}' already in use.").format(basename(path))

    runner = CellRunner(plugins, **meta)
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
    """Pause channel"""
    success = False
    runner = get_runner_by_channel(channel, runners, status=STATUS.started)
    if runner is not None:
        success = runner.pause()

    if success:
        return "Succeeded in pausing channel {}".format(channel)
    return "Failed in pausing channel {}".format(channel)


def stop(channel, runners):
    """Stop channel"""
    success = False
    runner = get_runner_by_channel(channel, runners)
    if runner is not None:
        success = runner.stop()

    if success:
        return "Succeeded in stopping channel {}".format(channel)
    return "Failed in stopping channel {}".format(channel)


def resume(channel, runners):
    """Resume channel from pause"""
    success = False
    runner = get_runner_by_channel(channel, runners, status=STATUS.paused)
    if runner is not None:
        success = runner.resume()

    if success:
        return "Succeeded in resuming channel {}".format(channel)
    return "Failed in resuming channel {}".format(channel)


def test(protocol):
    """Test script load on server"""
    try:
        runner = CellRunner()
        runner.load_protocol(protocol, isTest=True)
        return "Passed"
    except Exception as e:
        return str(e).splitlines()[-1]


def get_runner_by_channel(channel, runners, status=None):
    """Get runner currently on given channel"""
    if status is None:
        for runner in runners:
            if runner.channel == channel or int(runner.channel) == channel:
                return runner
    else:
        for runner in runners:
            if runner.channel == channel and runner.status == status:
                return runner

    return None
