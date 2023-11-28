import zmq

HOST = '127.0.0.1'
PORT = 7777


class Server:
    host: str = None
    port: int = None
    context: zmq.Context = None
    socket: zmq.Context.socket = None

    def __init__(self, host=HOST, port=PORT):
        self.host = host
        self.port = int(port)
        self.context = zmq.Context()

    def start(self):
        hostname = f"{self.host}:{self.port}"

        self.socket = self.context.socket(zmq.REQ)
        self.socket.identity = u"Server@{}".format(hostname).encode("ascii")
        self.socket.connect(f'tcp://{hostname}')
        print(f'Client connected to {hostname}')

    def server_task(self):
        self.socket.send(b"READY")

        while True:
            address, empty, request = self.socket.recv_multipart()
            print("{}: {}".format(self.socket.identity.decode("ascii"), request.decode("ascii")))
            self.socket.send_multipart([address, b"", b"OK"])

    def stop(self):
        self.socket.close()
        self.context.term()
