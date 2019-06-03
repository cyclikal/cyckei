import zmq
import json
import logging

from PySide2.QtWidgets import QMessageBox, QWidget

TIMEOUT = 3  # Seconds for listening to server before giving up.


class Socket(object):
    """Handles connection, communication, and control of server over ZMQ"""

    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.socket = zmq.Context().socket(zmq.REQ)
        self.socket.connect("{}:{}".format(self.address, self.port))

    def send(self, to_send):
        """Sends packet to server"""
        logging.debug("Sending: {}".format(to_send["function"]))

        self.socket.send_json(to_send)
        response = self.socket.recv_json()
        logging.debug("Received: {}".format(response))
        return response

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
