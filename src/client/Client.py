import json
from uuid import *

import zmq

HOST = '127.0.0.1'
PORT = 6666


class Client:
    host: str = None
    port: int = None
    uuid: UUID = None
    context: zmq.Context = None
    socket: zmq.Context.socket = None

    def __init__(self, host=HOST, port=PORT):
        self.host = host
        self.port = int(port)
        self.uuid = uuid4()
        self.context = zmq.Context()

    def start(self):
        hostname = f"{self.host}:{self.port}"

        self.socket = self.context.socket(zmq.REQ)
        self.socket.identity = u"Client-{}".format(str(self.uuid)).encode("ascii")
        self.socket.connect(f'tcp://{hostname}')
        print(f'Client connected to {hostname}')

        self.send_message("shopping_list_10", "GET")

        while True:
            self.receive_message()

    def send_message(self, body, message_type):
        formatted_message = {
            "identity": str(self.uuid),
            "body": body,
            "type": message_type
        }
        self.socket.send_json(formatted_message)


    """
    def read_message(self):
        response = self.socket.recv()
        print("{}: {}".format(self.socket.identity.decode("ascii"), response.decode("ascii")))
    """

    def receive_message(self):
        try:
            # Check if there are any incoming messages
            if self.socket.poll(timeout=1000, flags=zmq.POLLIN):
                # Receive the message as a JSON-encoded string
                message_json = self.socket.recv_string()

                message = json.loads(message_json)

                print("Received message:", message)
                return message
            else:
                # print("No message received.")
                return None
        except zmq.error.ZMQError as e:
            print("Error receiving message:", e)
            return None

    def stop(self):
        self.socket.close()
        self.context.term()


def main():
    client = Client()
    client.start()
    client.stop()


if __name__ == "__main__":
    main()
