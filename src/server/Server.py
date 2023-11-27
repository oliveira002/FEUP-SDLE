import zmq
import threading
import sys

HOST = '127.0.0.1'
PORT = 5555


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

        self.socket = self.context.socket(zmq.REP)
        self.socket.setsockopt_string(zmq.IDENTITY, hostname)
        self.socket.bind(f'tcp://{hostname}')
        print(f'Server listening on {hostname}')

        try:
            client_handler = threading.Thread(target=self.handle_client)
            client_handler.start()
            client_handler.join()
        except KeyboardInterrupt:
            print('KeyboardInterrupt: Server shutting down...')
        finally:
            self.socket.close()
            self.context.term()

    def handle_client(self):
        while True:
            message = self.socket.recv_string()

            print(f'Received message: "{message}"')

            self.socket.send_string(f'Response to "{message}"')


if len(sys.argv) > 1:
    server = Server(HOST, int(sys.argv[1]))
    server.start()
else:
    print('Usage: python Server.py <port>')
