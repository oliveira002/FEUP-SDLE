import time
import zmq
import sys
import os
import json
from uuid import *
import hashlib

from src.common.ClientMsgType import ClientMsgType
from src.common.LoadbalMsgType import LoadbalMsgType
from src.common.ServerMsgType import ServerMsgType
from src.common.ShoppingList import ShoppingList
from src.common.ShoppingListItem import ShoppingListItem
from src.common.utils import setup_logger, format_msg

# Logger setup
script_filename = os.path.splitext(os.path.basename(__file__))[0] + ".py"
logger = setup_logger(script_filename)

# Macros
BROKER_ENDPOINT_1 = '127.0.0.1:6666'
BROKER_ENDPOINT_2 = '127.0.0.1:6667'
HEARTBEAT_LIVENESS = 3
HEARTBEAT_INTERVAL = 1
INTERVAL_INIT = 1
INTERVAL_MAX = 32


class Server:

    def __init__(self):
        self.loadbalLiveness = HEARTBEAT_LIVENESS
        self.socket = None
        self.id = None
        self.poller = None
        self.generate_id()
        self.context = zmq.Context()

    def init_socket(self):
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.identity = u"Client-{}".format(str(self.id)).encode("ascii")

        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)

        self.socket.connect(f'tcp://{BROKER_ENDPOINT_1}')

    def kill_socket(self):
        self.poller.unregister(self.socket)
        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.close()

    def start(self):
        self.init_socket()
        logger.info(f"Connecting to broker at {BROKER_ENDPOINT_1}")

        self.send_message(str(self.id), "Connecting", ServerMsgType.CONNECT)

        interval = INTERVAL_INIT
        heartbeat_at = time.time() + HEARTBEAT_INTERVAL
        while True:
            sockets = dict(self.poller.poll(HEARTBEAT_INTERVAL * 1000))

            if self.socket in sockets and sockets.get(self.socket) == zmq.POLLIN:
                identity, message = self.receive_message()
                self.handle_message(message)
                interval = INTERVAL_INIT
            else:
                self.loadbalLiveness -= 1
                if self.loadbalLiveness == 0:
                    logger.warning("Heartbeat failure, can't reach load balancer")
                    logger.warning("Reconnecting in %0.2fs..." % interval)
                    time.sleep(interval)

                    if interval < INTERVAL_MAX:
                        interval *= 2
                    self.kill_socket()
                    self.init_socket()
                    self.loadbalLiveness = HEARTBEAT_LIVENESS
            if time.time() > heartbeat_at:
                heartbeat_at = time.time() + HEARTBEAT_INTERVAL
                logger.info("Sent heartbeat to load balancer")
                self.send_message(str(self.id), "HEARTBEAT", ServerMsgType.HEARTBEAT)

    def generate_id(self):
        unique_id = str(uuid4())
        hashed_id = hashlib.md5(unique_id.encode()).hexdigest()
        self.id = hashed_id[:8]

    def send_message(self, identity, message, msg_type: ServerMsgType):
        formatted_message = format_msg(identity, message, msg_type.value)
        self.socket.send_json(formatted_message)
        logger.info(f"Sent message \"{formatted_message}\"")

    def receive_message(self):
        try:
            _, identity, _, message = self.socket.recv_multipart()
            message = json.loads(message)
            identity = identity.decode("utf-8")
            logger.info(f"Received message \"{message}\" from {identity}")
            return [identity, message]
        except zmq.error.ZMQError as e:
            logger.error("Error receiving message:", e)
            return None

    def handle_message(self, message):
        if not message:
            return None

        client_id, req = message[0], message[1]
        if message["type"] == ClientMsgType.GET:
            pass
        elif message["type"] == ClientMsgType.POST:
            self.persist_to_json(json.loads(req['body']))
            self.send_message(client_id, "RESOURCE 1", ServerMsgType.REPLY)
        elif message["type"] == LoadbalMsgType.HEARTBEAT:
            logger.info("Received load balancer heartbeat")
        else:
            logger.error("Invalid message received: \"%s\"", message)
            self.loadbalLiveness = HEARTBEAT_LIVENESS
            return None

        self.loadbalLiveness = HEARTBEAT_LIVENESS

    def persist_to_json(self, new_object):
        file_path = f"shoppinglists/{self.id}.json"
        try:
            # Load existing data from the file
            with open(file_path, 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            # If the file doesn't exist, create an empty dictionary
            data = {"ShoppingLists": []}

        # Check if the given JSON object exists in the list by uuid
        existing_list = data.get("ShoppingLists", [])
        uuid_to_check = new_object.get("uuid")

        object_exists = any(obj.get("uuid") == uuid_to_check for obj in existing_list)

        if object_exists:
            # If the object exists, call the merge function
            self.merge(new_object, new_object)
        else:
            # If the object doesn't exist, append to the ShoppingLists list
            existing_list.append(new_object)

        # Write the updated data back to the file with indentation
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=2)

    def merge(self, existing_data, new_data):
        return

    def stop(self):
        self.kill_socket()
        self.context.term()


def main():
    server = Server()
    server.start()
    server.stop()


if __name__ == "__main__":
    main()
