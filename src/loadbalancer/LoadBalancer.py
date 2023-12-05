import json
from HashRing import HashRing
import zmq
import os
import logging
from src.common.ServerMessageType import ServerMessageType
from src.common.ClientMessageType import ClientMessageType

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
        self.workers = set()
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

                self.handle_client_message(identity, message)

            if self.backend in sockets:
                identity, message = self.backend.recv_multipart()
                identity = identity.decode("utf-8")
                message = json.loads(message.decode("utf-8"))
                logger.info(f"Received message \"{message}\" from {identity}")

                self.handle_server_message(identity, message)

    def stop(self):
        self.backend.close()
        self.frontend.close()
        self.context.term()

    def handle_server_message(self, identity, message):
        if message['type'] == "CONNECT":
            self.ring.add_node(identity)
            cur_ring_msg = self.ring.get_routing_table()
            request = [identity.encode("utf-8"), b"", b"", b"", json.dumps(cur_ring_msg).encode("utf-8")]
            self.backend.send_multipart(request)
            self.broadcast_message(identity, "JOIN_RING")
            self.workers.add(identity)

        if message['type'] == "REPLY":
            request = [message['identity'].encode("utf-8"), b"", json.dumps(message).encode("utf-8")]
            self.frontend.send_multipart(request)

        if message['type'] == ServerMessageType.HEARTBEAT:
            pass

    def handle_client_message(self, identity, message):
        if message['type'] == "GET":
            shopping_list = message['body']
            value, _ = self.ring.get_server(shopping_list)
            request = [value.encode("utf-8"), b"", identity.encode("utf-8"), b"",
                       json.dumps(message).encode("utf-8")]
            self.backend.send_multipart(request)

        if message['type'] == "POST":
            shopping_list = message['body']
            shopping_list = json.loads(shopping_list)

            value, neighbours = self.ring.get_server(shopping_list['uuid'])
            request_resource = [value.encode("utf-8"), b"", identity.encode("utf-8"), b"",
                       json.dumps(message).encode("utf-8")]

            #replicate_msg = self.parse_message(shopping_list,neighbours)
            #request_replicate = [value.encode("utf-8"), b"", b"", b"", json.dumps(replicate_msg).encode("utf-8")]

            self.backend.send_multipart(request_resource)
            #self.backend.send_multipart(request_replicate)

    def broadcast_message(self, new_worker, event):

        update_message = {
            "node": new_worker,
            "type": event
        }

        for worker in self.workers:
            request = [worker.encode("utf-8"), b"", b"", b"", json.dumps(update_message).encode("utf-8")]
            self.backend.send_multipart(request)


def main():
    loadbalancer = LoadBalancer()
    loadbalancer.start()
    loadbalancer.stop()


if __name__ == "__main__":
    main()
