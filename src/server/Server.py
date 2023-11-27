import zmq
import threading
import sys

HOST = '127.0.0.1'

class Server:
    def __init__(self, host=HOST, port=5555):
        self.host = host
        self.port = int(port)
        self.context = zmq.Context()
        self.server_socket = self.context.socket(zmq.REP)
        self.server_socket.bind(f'tcp://{self.host}:{self.port}')
        print(f'Server listening on {self.host}:{self.port}')

    def handle_client(self):
        while True:
            message = self.server_socket.recv_string()
            print(f'Received message: {message}')

            self.server_socket.send_string(f'Response to {message}')

    def start(self):
        try:
            client_handler = threading.Thread(target=self.handle_client)
            client_handler.start()
            
            client_handler.join()
        except KeyboardInterrupt:
            print('Server shutting down...')
        finally:
            self.server_socket.close()
            self.context.term()

if len(sys.argv) > 1:
    zmq_server = Server(HOST,sys.argv[1])
    zmq_server.start()
else:
    print('Usage: python Server.py <port>')
