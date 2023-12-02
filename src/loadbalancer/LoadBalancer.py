import json
from HashRing import HashRing
import zmq
import os
import logging

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
FRONTEND_PORT = 6666
BACKEND_PORT = 7777


class LoadBalancer:
    def __init__(self, host=HOST, frontend_port=FRONTEND_PORT, backend_port=BACKEND_PORT):
        self.host = host
        self.frontend_port = int(frontend_port)
        self.backend_port = int(backend_port)
        self.context = zmq.Context.instance()
        self.workers = []
        self.ring = HashRing()

    def start(self):
        self.frontend = self.context.socket(zmq.ROUTER)
        self.frontend.bind(f"tcp://{self.host}:{self.frontend_port}")
        logger.info(f"Frontend listening on {self.host}:{self.frontend_port}")
        self.backend = self.context.socket(zmq.ROUTER)
        self.backend.bind(f"tcp://{self.host}:{self.backend_port}")
        logger.info(f"Backend listening on {self.host}:{self.backend_port}")

        self.poller = zmq.Poller()
        self.poller.register(self.frontend, zmq.POLLIN)
        self.poller.register(self.backend, zmq.POLLIN)

        while True:
            sockets = dict(self.poller.poll())

            identity = None
            message = None

            if self.frontend in sockets:
                identity, _, message = self.frontend.recv_multipart()
                identity = identity.decode("utf-8")
                message = json.loads(message.decode("utf-8"))
                logger.info(f"Received message \"{message}\" from {identity}")

                if message['type'] == "GET" or message['type'] == "POST":
                    shopping_list = message['body']
                    key, value = self.ring.get_server(shopping_list)
                    request = [self.workers[0].encode("utf-8"), b"", identity.encode("utf-8"), b"", json.dumps(message).encode("utf-8")]
                    self.backend.send_multipart(request)

            if self.backend in sockets:
                request = self.backend.recv_multipart()
                identity, _, message = request
                identity = identity.decode("utf-8")

                message = json.loads(message.decode("utf-8"))

                if message['type'] == 'CONNECT':
                    self.ring.add_node(identity)
                    self.workers.append(identity)

                else:
                    request = [message['identity'].encode("utf-8"), b"", json.dumps(message).encode("utf-8")]
                    self.frontend.send_multipart(request)

                logger.info(f"Received message \"{message}\" from {identity}")



            #self.handle_message(message)

    def stop(self):
        self.backend.close()
        self.frontend.close()
        self.context.term()

    def handle_message(self, message):
        # maybe handling the different types of messages here
        if message['type'] == "CONNECT":
            print(2)


def main():
    loadbalancer = LoadBalancer()
    loadbalancer.start()
    loadbalancer.stop()


if __name__ == "__main__":
    main()
