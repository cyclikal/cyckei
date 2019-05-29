"""
Methods that controls the cykei client.
Controls communication and initializes the MainWindow.
"""

import json
import sys
import logging
import time
# from subprocess import Popen, CREATE_NEW_CONSOLE
import zmq

from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox
from PyQt5.QtCore import QTimer
from os.path import expanduser

from cyckei.client.window import MainWindow
from cyckei.client import scripts

TIMEOUT = 3  # Seconds for listening to server before giving up.


def main():
    """Initializes server and window"""

    # Load configuration
    record_dir = expanduser("~") + "/cyckei"
    config = json.load(open(record_dir + "/config.json", "r"))
    config["path"] = record_dir

    # Start logging
    log_file = "{}/client.log".format(record_dir)
    logging.basicConfig(filename=log_file, level=config["verbosity"],
                        format='%(asctime)s %(message)s')
    logging.info("--- Client started.")

    scripts.load_default_scripts(config["path"] + "/scripts")
    server = Server(config["zmq"]["client"]["address"], config["zmq"]["port"])
    server.start_socket()

    app = QApplication(sys.argv)
    window = MainWindow(config, server)
    window.show()

    sys.exit(app.exec_())


class Server(object):
    """Handles connection, communication, and control of server over ZMQ"""

    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.communication = False
        self.context = zmq.Context()
        self.socket = None

    def send(self, to_send):
        """Sends packet to server"""
        if self.communication:
            start_time = time.time()
            logging.debug("Sending: {}".format(to_send["function"]))
            self.socket.send_json(to_send)

            while True:  # time.time() - start_time < TIMEOUT:
                try:
                    response = self.socket.recv_json(flags=zmq.NOBLOCK)
                    logging.debug("Received: {}".format(response))
                    return response
                except zmq.error.Again:
                    pass
                self.close_socket()

        return json.loads("""{"response": "No Connection"}""")

    def close_socket(self):
        """Closes connection with server to reset queue"""
        self.socket.close()
        self.communication = False

    def start_socket(self):
        """Connects socket to specified ZMQ port"""
        logging.info("Client connecting to port {}...".format(self.port))
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect("{}:{}".format(self.address, self.port))
        self.communication = True

    def start_server_app(self):
        """Launches server as another process and tries to connect"""
        logging.info("Attempting to connect to server.")
        self.start_socket()
        ping_result = self.ping()
        logging.info(ping_result)
        if ping_result == "No Connection":
            logging.error("Could not connect, retrying")
            QTimer.singleShot(5000, self.start_socket)

    def ping_server(self):
        """Sends ping to server to check if connection functions"""
        ping_response = self.ping()
        msg = QMessageBox()
        msg.setText("Ping response: {}".format(ping_response))
        msg.setWindowTitle("Ping")
        msg.exec_()

    def get_server_time(self):
        """Gets time since server began listening for commands"""
        script = json.loads('{"function": "time", "kwargs": ""}')
        server_time = self.send(script)
        msg = QMessageBox()
        msg.setText("Server time in seconds: {}".format(
            server_time["response"]
        ))
        msg.setWindowTitle("Time")
        msg.exec_()

    def send_file(self, file):
        """Sends packet loaded from JSON file"""
        script = json.load(open(file))
        return self.send(script)

    def channel_status(self, channel):
        """Asks server for "channel_status" information"""
        script = json.loads(
            """{"function": "channel_status", "kwargs": {"channel": """
            + str(channel)
            + """}}""")
        return self.send(script)

    def kill_server(self):
        """Tells server to kill itself and closes connection"""
        reply = QMessageBox.question(
            QWidget(),
            "Message",
            "Kill server?\nAll jobs will be cancelled.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            script = json.loads('{"function": "kill_server"}')
            print(self.send(script))
            self.close_socket()
        else:
            pass

    def ping(self):
        """Send "ping" to server"""
        script = json.loads('{"function": "ping"}')
        response = self.send(script)["response"]
        return response

    def info_channel(self, channel):
        """Send "info_channel" to server"""
        script = json.loads(
            """{"function": "info_channel", "kwargs": {"channel": """
            + str(channel)
            + """}}""")
        return self.send(script)

    def info_all_channels(self):
        """Send "info_all_channels" to server"""
        script = json.loads('{"function": "info_all_channels"}')
        return self.send(script)


if __name__ == "__main__":
    main()