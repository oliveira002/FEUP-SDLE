from uuid import *
import zmq
import sys

HOST = '127.0.0.1'
PORT = 5555


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
        self.socket = self.context.socket(zmq.REQ)
        self.socket.setsockopt_string(zmq.IDENTITY, str(self.uuid))
        self.socket.connect(f'tcp://{self.host}:{self.port}')
        print(f'Client connected to {self.host}:{self.port}')

    def send_message(self, message):
        formatted_message = {
            "uuid": str(self.uuid),
            "message": message
        }
        self.socket.send_string(str(formatted_message))
        self.read_message()

    def read_message(self):
        response = self.socket.recv_string()
        print(f'Received response: {response}')

    def stop(self):
        self.socket.close()
        self.context.term()


if len(sys.argv) > 1:
    client = Client(HOST, int(sys.argv[1]))
    client.start()

    while True:
        message = input("Message: ")
        client.send_message(message)
else:
    print('Usage: python Client.py <port>')
