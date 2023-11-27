import zmq
import sys
HOST = '127.0.0.1'

class Client:
    host: str = None
    port: int = None
    context: zmq.Context = None
    socket: zmq.Context.socket = None
    
    def __init__(self, host=HOST, port=5555):
        self.host = host
        self.port = int(port)
        self.context = zmq.Context()
    
    def start(self):
        self.client_socket = self.context.socket(zmq.REQ)
        self.client_socket.connect(f'tcp://{self.host}:{self.port}')

    def send_message(self, message):
        self.client_socket.send_string(message)

        response = self.client_socket.recv_string()
        print(f'Received response: {response}')

    def close(self):
        self.client_socket.close()
        self.context.term()

if len(sys.argv) > 1:
    while(1):
        zmq_client = Client(HOST,sys.argv[1])
        zmq_client.start()
        
else:
    print('Usage: python Client.py <port>')
