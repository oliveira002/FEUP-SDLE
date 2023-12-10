import time
import zmq
import os
import json
from uuid import *
import sys
import hashlib

# Define module
current_path = os.path.dirname(__file__) + '/../..'
sys.path.append(current_path)

from src.loadbalancer.HashRing import HashRing
from hashlib import sha256
from src.common.ClientMsgType import ClientMsgType
from src.common.LoadbalMsgType import LoadbalMsgType
from src.common.ServerMsgType import ServerMsgType
from src.common.utils import setup_logger, format_msg

# Logger setup
script_filename = os.path.splitext(os.path.basename(__file__))[0] + ".py"
logger = setup_logger(script_filename)

# Macros
PRIMARY_BACKEND_ENDPOINT = '127.0.0.1:7000'
BACKUP_BACKEND_ENDPOINT = '127.0.0.1:7001'
SERVERS = [PRIMARY_BACKEND_ENDPOINT, BACKUP_BACKEND_ENDPOINT]
HEARTBEAT_LIVENESS = 3
HEARTBEAT_INTERVAL = 1
INTERVAL_INIT = 1
INTERVAL_MAX = 32
REQUEST_TIMEOUT = 1
FAILOVER_DELAY = 2


class Server:

    def __init__(self, port):
        self.socket_neigh = None
        self.ring = None
        self.loadbalLiveness = HEARTBEAT_LIVENESS
        self.socket = None
        self.id = None
        self.poller = None
        self.generate_id()
        self.port = int(port)
        self.hostname = f"127.0.0.1:{self.port}"
        self.server_nr = 0
        self.identity = None
        self.context = zmq.Context()

    def init_sockets(self):
        self.socket = self.context.socket(zmq.DEALER)
        self.socket_neigh = self.context.socket(zmq.DEALER)
        self.socket.identity = u"Server@{}".format(str(self.hostname)).encode("ascii")
        self.identity = u"Server@{}".format(str(self.hostname))
        self.socket_neigh.identity = u"Server2@{}".format(str(self.hostname)).encode("ascii")

        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)
        self.poller.register(self.socket_neigh, zmq.POLLIN)

        self.socket.connect(f'tcp://{SERVERS[self.server_nr]}')
        self.socket_neigh.bind(f'tcp://{self.hostname}')

    def kill_sockets(self):
        self.poller.unregister(self.socket)
        self.poller.unregister(self.socket_neigh)

        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket_neigh.setsockopt(zmq.LINGER, 0)

        self.socket.close()
        self.socket_neigh.close()

    def start(self):
        self.init_sockets()
        logger.info(f"Connecting to broker at {SERVERS[self.server_nr]}")

        self.send_message(self.socket, "Connecting", ServerMsgType.CONNECT, str(self.hostname))

        interval = INTERVAL_INIT
        heartbeat_at = time.time() + HEARTBEAT_INTERVAL
        while True:
            sockets = dict(self.poller.poll(HEARTBEAT_INTERVAL * 1000))

            if self.socket_neigh in sockets and sockets.get(self.socket_neigh) == zmq.POLLIN:
                identity, message = self.receive_message_neighbour()
                self.handle_message(identity, message)

            if self.socket in sockets and sockets.get(self.socket) == zmq.POLLIN:

                frames = self.socket.recv_multipart()
                if not frames:
                    break

                identity = frames[1].decode("utf-8")
                message = json.loads(frames[3].decode("utf-8"))
                if message["type"] != LoadbalMsgType.HEARTBEAT:
                    logger.info(f"Received message \"{message}\" from {identity}")
                else:
                    logger.debug(f"Received message \"{message}\" from {identity}")

                self.handle_message(identity, message)
                interval = INTERVAL_INIT
            else:
                self.loadbalLiveness -= 1
                if self.loadbalLiveness == 0:
                    logger.warning("Heartbeat failure, can't reach load balancer")
                    logger.warning("Failing over in %0.2fs..." % FAILOVER_DELAY)
                    time.sleep(FAILOVER_DELAY)

                    self.server_nr = (self.server_nr + 1) % 2
                    self.kill_sockets()
                    self.init_sockets()
                    self.loadbalLiveness = HEARTBEAT_LIVENESS
            '''
            if time.time() > heartbeat_at:
                heartbeat_at = time.time() + HEARTBEAT_INTERVAL
                logger.debug("Sent heartbeat to load balancer")
                self.send_message(self.socket, "HEARTBEAT", ServerMsgType.HEARTBEAT, str(self.hostname))
            '''

    def generate_id(self):
        unique_id = str(uuid4())
        hashed_id = hashlib.md5(unique_id.encode()).hexdigest()
        self.id = hashed_id[:8]

    def replicate_data(self, neighbours, shopping_list):
        neighbours = [x.split('@', 1)[-1] for x in neighbours]
        print(neighbours)

        for neighbour in neighbours:
            try:
                self.socket_neigh.connect(f'tcp://{neighbour}')
                self.send_message(self.socket_neigh, shopping_list, ServerMsgType.REPLICATE)
            except Exception as e:
                logger.error(f"Failed to connect to {neighbour}: {e}")

    def send_message(self, socket, message, msg_type: ServerMsgType, identity=None):
        formatted_message = format_msg(identity if identity is not None else str(self.hostname), message,
                                       msg_type.value)
        socket.send_json(formatted_message)
        if formatted_message["type"] != ServerMsgType.HEARTBEAT:
            logger.info(f"Sent message \"{formatted_message}\"")
        else:
            logger.debug(f"Sent message \"{formatted_message}\"")


    def receive_message(self):
        try:
            _, identity, _, message = self.socket.recv_multipart()
            message = json.loads(message)
            identity = identity.decode("utf-8")
            if message["type"] != ServerMsgType.HEARTBEAT:
                logger.info(f"Received message \"{message}\" from {identity}")
            return [identity, message]
        except zmq.error.ZMQError as e:
            logger.error("Error receiving message:", e)
            return None

    def handle_message(self, identity, message):
        if message["type"] == ClientMsgType.GET:
            # self.send_message(self.socket, "ALIVE", ServerMsgType.ACK, str(self.hostname))
            shopping_list_id = message['body']

            shopping_list = self.read_from_json(shopping_list_id)

            if shopping_list is None:
                self.send_message(self.socket, "Error couldn't find it", ServerMsgType.REPLY, identity)
            # need to check the json and merge (?) quorum
            else:
                self.send_message(self.socket, shopping_list, ServerMsgType.REPLY, identity)

        elif message["type"] == ClientMsgType.POST:
            # self.send_message(self.socket, "ALIVE", ServerMsgType.ACK, str(self.hostname))
            shopping_list = json.loads(message['body'])
            merged = self.persist_to_json(shopping_list)
            self.send_message(self.socket, "Modified Shopping List Correctly", ServerMsgType.REPLY, identity)
            _, neighbours = self.ring.get_server(shopping_list['uuid'])
            # self.replicate_data(neighbours, merged)

        elif message["type"] == LoadbalMsgType.HEARTBEAT:
            logger.debug("Received load balancer heartbeat")
            pass

        elif message['type'] == ServerMsgType.REPLICATE:
            print(message)
            # self.persist_to_json(message['body'])

        elif message['type'] == ServerMsgType.REBALANCE:
            shopping_lists = message['body']

            for sl in shopping_lists:
                self.persist_to_json(sl)

            # self.persist_to_json(message['body'])

        elif message['type'] == "JOIN_RING":
            updates = self.ring.add_node(message['node'])

            # print(list(self.ring.ring.keys()))
            # print(list(self.ring.ring.values()))

            self.send_data_on_join(updates)

        elif message['type'] == "RING":
            nodes = list(message['nodes'])
            self.ring = HashRing()
            self.ring.build_ring(nodes)

        elif message['type'] == "LEAVE_RING":
            print(message)

        else:
            logger.error("Invalid message received: \"%s\"", message)

        self.loadbalLiveness = HEARTBEAT_LIVENESS

    def receive_message_neighbour(self):
        try:
            message = self.socket_neigh.recv_multipart()[0]
            message = json.loads(message)
            identity = message['identity']
            logger.info(f"Received message \"{message}\" from {identity}")
            return [identity, message]

        except zmq.error.ZMQError as e:
            logger.error("Error receiving message:", e)
            return None

    def send_data_on_join(self, update_info):
        update_info = [x for x in update_info if x['send'] == self.identity]
        for update in update_info:
            receiver = update['receive'].split('@', 1)[-1]
            shopping_lists = self.get_shopping_lists_range(update['content'][0], update['content'][1])

            if len(shopping_lists) == 0:
                continue

            try:
                self.socket_neigh.connect(f'tcp://{receiver}')
                self.send_message(self.socket_neigh, shopping_lists, ServerMsgType.REBALANCE)

            except Exception as e:
                logger.error(f"Failed to connect to {receiver}: {e}")
            finally:
                self.socket_neigh.disconnect(f'tcp://{receiver}')

    def get_shopping_lists_range(self, min_hash, max_hash):
        data = self.create_or_load_db_file()
        if max_hash == -1:
            filtered_lists = [shopping_list for shopping_list in data['ShoppingLists']
                              if min_hash < self.hash_function(shopping_list['uuid'])]
            return filtered_lists

        filtered_lists = [shopping_list for shopping_list in data['ShoppingLists']
                          if min_hash < self.hash_function(shopping_list['uuid']) < max_hash]

        return filtered_lists

    def create_or_load_db_file(self):
        file_path = f"shoppinglists\{self.port}.json"
        current_directory = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_directory, file_path)

        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as file:
                    data = json.load(file)
            else:
                data = {"ShoppingLists": []}
                with open(file_path, 'w') as file:
                    json.dump(data, file, indent=2)

            return data
        except Exception as e:
            print(f"Error: {e}")
            return None

    def read_from_json(self, shopping_list):
        data = self.create_or_load_db_file()
        existing_list = data.get("ShoppingLists", [])

        for obj in existing_list:
            if obj.get("uuid") == shopping_list:
                return obj

        return None

    def persist_to_json(self, new_object):
        file_path = f"shoppinglists\{self.port}.json"
        current_directory = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_directory, file_path)

        data = self.create_or_load_db_file()

        # Check if the given JSON object exists in the list by uuid
        existing_list = data.get("ShoppingLists", [])
        uuid_to_check = new_object.get("uuid")

        object_exists = any(obj.get("uuid") == uuid_to_check for obj in existing_list)

        if object_exists:
            for i, obj in enumerate(existing_list):
                if obj.get("uuid") == uuid_to_check:
                    new_object = self.merge(obj, new_object)
                    existing_list[i] = new_object
        else:
            # If the object doesn't exist, append to the ShoppingLists list
            existing_list.append(new_object)

        # Write the updated data back to the file with indentation
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=2)

        return new_object

    def merge(self, existing_data, new_data):
        return new_data

    def stop(self):
        self.kill_sockets()
        self.context.term()

    def hash_function(self, key):
        return sha256(key.encode('utf-8')).hexdigest()


def main():
    server = Server(int(sys.argv[1]))
    #server = Server(1229)
    server.start()
    server.stop()


if __name__ == "__main__":
    main()
