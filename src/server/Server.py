import zmq
import sys
import os
import logging

from src.common.ShoppingList import ShoppingList
from src.common.ShoppingListItem import ShoppingListItem

# Logger setup
script_filename = os.path.splitext(os.path.basename(__file__))[0] + ".py"
logger = logging.getLogger(script_filename)
logger.setLevel(logging.DEBUG)

stream_h = logging.StreamHandler()
file_h = logging.FileHandler('../logs.log')

stream_h.setLevel(logging.DEBUG)
file_h.setLevel(logging.DEBUG)

formatter = logging.Formatter(fmt='[%(asctime)s] %(name)s - %(levelname)s: %(message)s', datefmt='%d/%m/%Y %H:%M:%S')
stream_h.setFormatter(formatter)
file_h.setFormatter(formatter)

logger.addHandler(stream_h)
logger.addHandler(file_h)

# Macros
HOST = '127.0.0.1'
PORT = 7777
BROKER = HOST + ":" + str(PORT)


class Server:
    host: str = None
    port: int = None
    context: zmq.Context = None
    socket: zmq.Context.socket = None

    def __init__(self, host=HOST, port=PORT):
        self.hostname = None
        self.host = host
        self.port = int(port)
        self.context = zmq.Context()

    def start(self):
        hostname = f"{self.host}:{self.port}"
        self.hostname = hostname
        self.socket = self.context.socket(zmq.REQ)
        self.socket.identity = u"Server@{}".format(hostname).encode("ascii")
        self.socket.connect(f'tcp://{BROKER}')
        logger.info(f'Server connected to Broker at {BROKER}')

        self.send_message("Initial Setup", "CONNECT")

        while True:
            request = self.receive_message()
            if request is not None:
                self.send_message_response(request[0], "RESOURCE 1")

    def send_message(self, body, message_type):
        formatted_message = {
            "identity": str(self.hostname),
            "body": body,
            "type": message_type
        }
        self.socket.send_json(formatted_message)

    def send_message_response(self, client_identity, body):
        formatted_message = {
            "identity": client_identity.decode("utf-8"),
            "body": body,
            "type": "REPLY"
        }
        self.socket.send_json(formatted_message)

    def receive_message(self):
        try:
            # Receive the message as a JSON-encoded string
            identity, _, message = self.socket.recv_multipart()

            logger.info(f"Received message \"{message}\" from {identity}")
            return identity, message
        except zmq.error.ZMQError as e:
            logger.error("Error receiving message:", e)
            return None

    def stop(self):
        self.socket.close()
        self.context.term()


def main():
    server = Server(HOST, int(sys.argv[1]))
    server.start()
    server.stop()


if __name__ == "__main__":
    main()
