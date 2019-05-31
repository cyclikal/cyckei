import zmq
import json
import logging

from time import sleep, time
from PySide2.QtWidgets import QMessageBox, QWidget

TIMEOUT = 3  # Seconds for listening to server before giving up.


class Server(object):
    """Handles connection, communication, and control of server over ZMQ"""

    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.communication = False
        self.context = zmq.Context()
        self.socket = None
        self.start_socket()

    def send(self, to_send):
        """Sends packet to server"""
        if self.communication:
            logging.debug("Sending Packet")
            start_time = time()
            logging.debug("Sending: {}".format(to_send["function"]))

            self.socket.send_json(to_send)
            response = self.socket.recv_json()
            logging.debug("Received: {}".format(response))
            return response

            while True:
                if time() - start_time < TIMEOUT:
                    try:
                        response = self.socket.recv_json()
                        logging.debug("Received: {}".format(response))
                        return response
                    except zmq.error.Again as error:
                        logging.debug("Retrying: {}".format(error))
                        sleep(0.1)
                else:
                    logging.debug("Reached Timeout, closing socket.")
                    self.close_socket()
                    break

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
