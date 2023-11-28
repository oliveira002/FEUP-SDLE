from uuid import *
import zmq
import json

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

    def send_message(self, message):
        formatted_message = {
            "uuid": str(self.uuid),
            "message": message
        }
        self.socket.send_json(formatted_message)

    def read_message(self):
        response = self.socket.recv()
        print("{}: {}".format(self.socket.identity.decode("ascii"), response.decode("ascii")))

    def stop(self):
        self.socket.close()
        self.context.term()


def main():
    client = Client()
    client.start()
    client.send_message("Boas")
    client.stop()

if __name__ == "__main__":
    main()

