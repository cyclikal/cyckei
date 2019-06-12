"""Main script run by server application"""

import time
import traceback
from collections import OrderedDict
import logging
from os.path import isfile

import zmq
from visa import VisaIOError

from cyckei.server.models import Keithley2602
from cyckei.server.protocols import CellRunner, STATUS


def main(config):
    """Main start method and loop for server application"""
    # Initialize the channels from a config file
    logging.info("cyckei.server.server.main: Initializing...")

    # Create list of sources (outputs)
    keithleys = []
    sources = []

    # Initialize sources
    logging.info("Attemping {} channels.".format(len(config["channels"])))
    for chd in config["channels"]:
        gpib_addr = chd["gpib_address"]
        keithley = None
        for k in keithleys:
            if gpib_addr == k.gpib_addr:
                keithley = k
        if keithley is None:
            try:
                keithley = Keithley2602(gpib_addr)
            except (ValueError, VisaIOError) as e:
                logging.error("Could not esablish connection: "
                              "Channel {}, GPIB {}.".format(
                                chd["channel"],
                                chd["gpib_address"])
                              )
                logging.error(e)
                continue

            keithleys.append(keithley)

        source = keithley.get_source(chd["keithley_channel"],
                                     channel=chd["channel"])
        sources.append(source)

    logging.info("Connected {} channels.".format(len(sources)))

    # Initialize socket
    runners = []
    socket = initialize_socket(config["zmq"]["port"],
                               config["zmq"]["server"]["address"])

    logging.info(
        "Socket bound to port {}. Entering main loop.".format(
            config["zmq"]["port"])
    )

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
        # TODO verify this is fast enough to be blocking
        # main loop without problem
        logging.debug("cyckei.server.server.main: Processing socket messages")
        process_socket(socket, runners, sources, current_time)

        # execute runners or sleep if none
        if runners:
            logging.debug("cyckei.server.server.main: Looping over runners")
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
                    channels_message = channels_message + "/" + runner.channel
                    timing_message = (timing_message
                                      + "/"
                                      + str(relative_next_time)[:5])

                    if relative_next_time <= 0.0:
                        runner.run()
            logging.debug(
                "cyckei.server.server.main: "
                + "channel {} will be checked in approx {} seconds...".format(
                    channels_message[1:], timing_message[1:]
                )
            )

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


def initialize_socket(port, address):
    """Initialize zmq socket"""
    context = zmq.Context(1)
    socket = context.socket(zmq.REP)
    socket.bind("{}:{}".format(address, port))
    return socket


def process_socket(socket, runners, sources, server_time):
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

    msg = socket.recv_json()

    if msg is not None:
        response = {"response": None, "message": None}
        try:
            # a message has been received
            fun = msg["function"]
            logging.info("Packet request received: {}".format(fun))
            kwargs = msg.get("kwargs", None)
            # response = {"version": __version__, "response": None}
            resp = "Unknown function"
            if fun == "start":
                try:
                    resp = start(kwargs["channel"], kwargs["meta"],
                                 kwargs["protocol"], runners, sources)
                except Exception:
                    resp = "Error occured when running script."
                    logging.warning("Error occured when running script.")

            elif fun == "pause":
                resp = pause(kwargs["channel"], runners)

            elif fun == "resume":
                resp = resume(kwargs["channel"], runners)

            elif fun == "test":
                resp = test(kwargs["protocol"])

            elif fun == "channel_status":
                resp = channel_status(kwargs["channel"], runners)

            elif fun == "time":
                resp = str(server_time)

            elif fun == "kill_server":
                for protocol in runners:
                    protocol.close()
                response["response"] = "Killing server now"
                socket.send_json(response)
                socket.close()
                socket.context.term()
                exit()

            elif fun == "stop":
                resp = stop(kwargs["channel"], runners)

            elif fun == "ping":
                port = socket.getsockopt_string(
                    zmq.LAST_ENDPOINT
                ).split(":")[-1]
                resp = "True: server is running on port {}".format(port)

            elif fun == "info_all_channels":
                resp = info_all_channels(runners, sources)

            elif fun == "info_channel":
                resp = info_channel(kwargs["channel"], runners)

            response["response"] = resp
            socket.send_json(response)
        except (IndexError, ValueError, TypeError, NameError) as exception:
            response["response"] = (
                "Call failed with error: {}\ntraceback:\n{}".format(
                    exception,
                    traceback.format_exc()
                )
            )
            response["message"] = msg
            logging.debug("cyckei.server.server.process_socket: Sent response")
            socket.send_json(response)


def info_all_channels(runners, sources):
    """Return info on all channels"""
    infos = OrderedDict()
    for source in sources:
        infos[source.channel] = info_channel(source.channel, runners)

    return infos


def info_channel(channel, runners):
    """Return info on specified channels"""
    info = OrderedDict(channel=channel, status=None, state=None,
                       current=None, voltage=None)
    runner = get_runner_by_channel(channel, runners)
    if runner:
        info["status"] = STATUS.string_map[runner.status]
        info["state"] = runner.step.state_str
        data = runner.last_data
        if data:
            info["current"] = data[1]
            info["voltage"] = data[2]
    else:
        info["statuses"] = STATUS.string_map[STATUS.available]

    return info


def start(channel, meta, protocol, runners, sources):
    """Start channel with given protocol"""

    # check to see if there is a already a runner on that channel
    meta["channel"] = channel
    if get_runner_by_channel(channel, runners):
        return "Failed to start channel {}, already in use.".format(channel)

    # check if log file is being used
    path = meta["path"]
    if isfile(path):
        return(
            "Failed to start channel, log file '{}' already in use."
        ).format(path)

    runner = CellRunner(**meta)
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


def channel_status(channel, runners):
    """Get current state of channel"""
    status = STATUS.string_map[STATUS.available]
    runner = get_runner_by_channel(channel, runners)
    if runner:
        status = STATUS.string_map[runner.status]
    return status


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
