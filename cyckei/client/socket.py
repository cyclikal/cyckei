import zmq
import json
import logging


class Socket(object):
    """Handles connection, communication, and control of server over ZMQ"""

    def __init__(self, config):
        self.config = config
        self.socket = zmq.Context().socket(zmq.REQ)
        self.socket.connect("{}:{}".format(
            config["zmq"]["client-address"],
            config["zmq"]["port"]))
        self.socket.setsockopt(zmq.LINGER, 0)

    def send(self, to_send):
        """Sends packet to server"""
        logging.debug("Sending: {}".format(to_send["function"]))

        self.socket.send_json(to_send)
        poller = zmq.Poller()
        poller.register(self.socket, zmq.POLLIN)
        if poller.poll(self.config["zmq"]["timeout"]*1000):
            response = self.socket.recv_json()
        else:
            response = (
                json.loads('{"response": "No Connection", "message": ""}'))
        logging.debug("Received: {}".format(response))
        self.socket.close()
        return response

    def send_file(self, file):
        """Sends packet loaded from JSON file"""
        script = json.load(open(file))
        return self.send(script)

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
        """Send "info_all_channel" to server"""
        script = json.loads("""{"function": "info_all_channels"}""")
        return self.send(script)["response"]
