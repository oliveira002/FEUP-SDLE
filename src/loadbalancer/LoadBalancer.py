import json
from HashRing import HashRing
import zmq
import os
import logging
from src.common.ServerMsgType import ServerMsgType
from src.common.ClientMsgType import ClientMsgType
from src.common.utils import setup_logger

# Logger setup
script_filename = os.path.splitext(os.path.basename(__file__))[0] + ".py"
logger = setup_logger(script_filename)

# Macros
FRONTEND_ENDPOINT = '127.0.0.1:6666'
BACKEND_ENDPOINT = '127.0.0.1:7777'


class LoadBalancer:
    def __init__(self):
        self.poller = None
        self.backend = None
        self.frontend = None
        self.context = zmq.Context.instance()
        self.workers = []
        self.ring = HashRing()

    def init_sockets(self):
        self.frontend = self.context.socket(zmq.ROUTER)
        self.frontend.bind(f"tcp://{FRONTEND_ENDPOINT}")
        logger.info(f"Frontend listening on {FRONTEND_ENDPOINT}")

        self.backend = self.context.socket(zmq.ROUTER)
        self.backend.bind(f"tcp://{BACKEND_ENDPOINT}")
        logger.info(f"Backend listening on {BACKEND_ENDPOINT}")

        self.poller = zmq.Poller()
        self.poller.register(self.frontend, zmq.POLLIN)
        self.poller.register(self.backend, zmq.POLLIN)

    def kill_sockets(self):
        self.poller.unregister(self.frontend)
        self.poller.unregister(self.backend)
        self.frontend.setsockopt(zmq.LINGER, 0)
        self.backend.setsockopt(zmq.LINGER, 0)
        self.frontend.close()
        self.backend.close()

    def start(self):

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
            # self.workers.append(identity)
        if message['type'] == "REPLY":
            request = [message['identity'].encode("utf-8"), b"", json.dumps(message).encode("utf-8")]
            self.frontend.send_multipart(request)
        if message['type'] == ServerMsgType.HEARTBEAT:
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
            value, neighbours = self.ring.get_server(shopping_list)
            message['neighbours'] = neighbours
            request_resource = [value.encode("utf-8"), b"", identity.encode("utf-8"), b"",
                       json.dumps(message).encode("utf-8")]

            #replicate_msg = self.parse_message(shopping_list,neighbours)
            #request_replicate = [value.encode("utf-8"), b"", b"", b"", json.dumps(replicate_msg).encode("utf-8")]

            self.backend.send_multipart(request_resource)
            #self.backend.send_multipart(request_replicate)

    def parse_message(self, shopping_list, neighbours):
        formatted_message = {
            "body": shopping_list,
            "destination": neighbours,
            "type": "REPLICATE"
        }

        return formatted_message



def main():
    loadbalancer = LoadBalancer()
    loadbalancer.start()
    loadbalancer.stop()


if __name__ == "__main__":
    main()
