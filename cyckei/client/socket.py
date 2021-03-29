import zmq
import json
import logging

logger = logging.getLogger('cyckei_client')


class Socket(object):
    """Object that handles connection, communication, and control of server from the client over ZMQ.
    
    Attributes:
        config (dict): Holds Cyckei launch settings.
        socket (zmq.socket): The underlying scoket that acts as the communication between client and server.
    """

    def __init__(self, config):
        """Inits Socket with config and socket.

        Args:
            config (dict): Holds Cyckei launch settings.
        """
        self.config = config
        self.socket = zmq.Context().socket(zmq.REQ)
        self.socket.connect("{}:{}".format(
            config["zmq"]["client-address"],
            int(config["zmq"]["port"])))
        self.socket.setsockopt(zmq.LINGER, 0)

    def send(self, to_send):
        """Sends JSON packet from client to server over zmq socket.
        
        Args:
            to_send (dict): JSON in the form of a python dict to be sent to server.

        Returns:
            response (dict): A JSON response from the server in the form of a python dict.

        """
        logger.debug("Sending: {}".format(to_send["function"]))

        self.socket.send_json(to_send)
        poller = zmq.Poller()
        poller.register(self.socket, zmq.POLLIN)
        if poller.poll(int(self.config["zmq"]["timeout"])*1000):
            response = self.socket.recv_json()
        else:
            response = (
                json.loads('{"response": "Request Timed Out", "message": ""}'))
        logger.debug("Received: {}".format(response))
        self.socket.close()
        return response

    def send_file(self, file):
        """Sends a JSON packet from the client to the server over a zmq socket, loaded from a file.

        Args:
            file (str): File path of the JSON file to be loaded and sent to the server.

        Returns:
            dict:  A JSON response from the server in the form of a python dict.
        """
        script = json.load(open(file))
        return self.send(script)

    def ping(self):
        """Sends a JSON "ping" to the server to check status

        Returns:
            dict: A JSON response from the server with the port the server is on.
        """
        script = json.loads('{"function": "ping"}')
        response = self.send(script)["response"]
        return response

    def info_plugins(self):
        """Sends a JSON request for information on plugins to server.

        Returns:
            list: A list from the server of the plugins that are installed.
        """
        script = json.loads('{"function": "info_plugins"}')
        response = self.send(script)["response"]
        return response

    def info_channel(self, channel):
        """Sends a JSON request for information on a channel to server.
        
        Args:
            channel (int): The id number of the channel to request info about.

        Returns:
            dict: Information about the requested channel.
        """
        script = json.loads(
            """{"function": "info_channel", "kwargs": {"channel": """
            + str(channel)
            + """}}""")
        return self.send(script)

    def info_all_channels(self):
        """Sends a JSON request for information on all channel to server.
        
        Returns:
            dict: A dict of nested dicts containing info about all connected channels.
        """
        script = json.loads("""{"function": "info_all_channels"}""")
        return self.send(script)["response"]
