"""
A battery cycler that controls the 2602A/B SYSTEM SourceMeter from Keithley.
This script starts execution of either the server or the user interface.
"""

import argparse
import json
import logging
import time
import sys

PARSER = argparse.ArgumentParser()
GROUP = PARSER.add_argument_group(
    "required arguments"
).add_mutually_exclusive_group()
GROUP.add_argument("-s", "--server",
                   action="store_true",
                   help="Starts server without GUI")


def setup_logging(log_file):
    """Setup logging and configure"""
    logging.basicConfig(filename=log_file, level=CONFIG["verbosity"],
                        format='%(asctime)s %(message)s')
    logging.info("Logging to {}".format(log_file))
    print("Logging to {}".format(log_file))


# OVERWRITE
def handle_exception(exception_type, value, traceback):
    """Rewrite exception to log errors"""
    logging.exception("EXCEPTION!\n",
                      exc_info=(exception_type, value, traceback))
    print("Exception: {}\nCheck log for details.")
    quit()


sys.excepthook = handle_exception
ARGS = PARSER.parse_args()
START_TIME = time.strftime("%H-%M-%S_%d-%b-%G")
CONFIG = json.load(open("config.json", "r"))

if ARGS.server:
    print("Welcome to the cyckei server.")
    setup_logging("{}/program/server_{}.log".format(CONFIG["record_dir"],
                                                    START_TIME))
    logging.info("STARTING Server at {}.".format(START_TIME))

    from server import server
    server.main(CONFIG)

else:
    print("Welcome to the cyckei client.")
    setup_logging("{}/program/client_{}.log".format(CONFIG["record_dir"],
                                                    START_TIME))
    logging.info("STARTING Client at {}.".format(START_TIME))

    from client import client
    client.main(CONFIG)
