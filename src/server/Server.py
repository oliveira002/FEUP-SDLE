import json
import time

import zmq
import sys

HOST = '127.0.0.1'
PORT = 7777
BROKER = '127.0.0.1:7777'


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
        print(f'Server connected to {BROKER}')

        self.send_message("Initial Setup", "CONNECT")

        while True:
            request = self.receive_message()
            if request is not None:
                self.send_message_response(request[0], "RESOURCE 1")

    def server_task(self):
        self.socket.send(b"READY")

        while True:
            address, empty, request = self.socket.recv_multipart()
            print("{}: {}".format(self.socket.identity.decode("ascii"), request.decode("ascii")))

            self.socket.send_multipart([address, b"", b"OK"])

    def send_message(self, message, message_type):
        formatted_message = {
            "identity": str(self.hostname),
            "message": message,
            "type": message_type
        }
        self.socket.send_json(formatted_message)

    def send_message_response(self, client_identity, message):
        formatted_message = {
            "identity": client_identity.decode("utf-8"),
            "message": message,
            "type": "RESPONSE"
        }
        self.socket.send_json(formatted_message)

    def receive_message(self):
        try:
            # Receive the message as a JSON-encoded string
            identity, _, message = self.socket.recv_multipart()

            print(identity, message)
            return identity, message
        except zmq.error.ZMQError as e:
            print("Error receiving message:", e)
            return None

    def stop(self):
        self.socket.close()
        self.context.term()


def main():
    server = Server(HOST, sys.argv[1])
    server.start()
    # server.send_message("Boas", "Connect")
    server.stop()


if __name__ == "__main__":
    main()
