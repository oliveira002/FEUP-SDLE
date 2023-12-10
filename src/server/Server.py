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
NUM_REPLICAS = 3


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
        self.requests = []
        self.context = zmq.Context()
        self.path = f"shoppinglists\{self.port}.json"
        self.h_path = f"shoppinglists\{self.port}h.json"

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
        identity_neigh = None
        message_neigh = None
        while True:
            sockets = dict(self.poller.poll(HEARTBEAT_INTERVAL * 1000))

            if self.socket in sockets and sockets.get(self.socket) == zmq.POLLIN:

                new_reqs = list(self.requests)
                rec_time = time.time()
                for x in self.requests:
                    shopping_list = x['body']['uuid']
                    value, neighbours = self.ring.get_server(shopping_list)
                    if x['entry_time'] + 3 < rec_time:
                        next_idx = neighbours.index('Server@' + x['curr_node']) + 1
                        next_node = neighbours[next_idx]
                        self.requests.remove(x)
                        new_reqs.remove(x)

                        print("REPLICA NR:", x['replica'])
                        x['liveness'] -= 1
                        x['type'] = "HANDOFF"
                        x['entry_time'] = time.time()
                        x['curr_node'] = next_node.split('@', 1)[-1]
                        neigh_ip = x['curr_node']

                        new_reqs.append(x)

                        try:
                            print("Mandou para:", neigh_ip)
                            self.socket_neigh.connect(f'tcp://{neigh_ip}')
                            self.socket_neigh.send_json(x)
                        except Exception as e:
                            logger.error(f"Failed to connect to {neigh_ip}: {e}")
                        finally:
                            self.socket_neigh.disconnect(f'tcp://{neigh_ip}')
                self.requests = new_reqs

                self.check_requests(identity_neigh, message_neigh, rec_time)

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

            if self.socket_neigh in sockets and sockets.get(self.socket_neigh) == zmq.POLLIN:
                identity_neigh, message_neigh = self.receive_message_neighbour()
                self.handle_message(identity_neigh, message_neigh)

            else:
                identity_neigh = None
                message_neigh = None

            if time.time() > heartbeat_at:
                heartbeat_at = time.time() + HEARTBEAT_INTERVAL
                logger.debug("Sent heartbeat to load balancer")
                self.send_message(self.socket, "HEARTBEAT", ServerMsgType.HEARTBEAT, str(self.hostname))

    def generate_id(self):
        unique_id = str(uuid4())
        hashed_id = hashlib.md5(unique_id.encode()).hexdigest()
        self.id = hashed_id[:8]

    def check_requests(self, identity, message, rec_time):
        new_reqs = list(self.requests)
        for x in self.requests:
            #print(self.requests)
            shopping_list = x['body']['uuid']
            value, neighbours = self.ring.get_server(shopping_list)
            print(neighbours)
            neighbours.insert(0, value)

            if x['curr_node'] == identity and x['entry_time'] == message['entry_time']:
                next_idx = neighbours.index('Server@' + x['curr_node']) + 1
                next_node = neighbours[next_idx]
                print("Recebeu a tempo", x['curr_node'])
                message['replica'] += 1
                if message['replica'] == 3:
                    self.requests.remove(x)
                    print("OLAOALOA")
                    new_reqs.remove(x)
                    self.requests = new_reqs
                    continue

                message['entry_time'] = time.time()
                message['curr_node'] = next_node.split('@', 1)[-1]
                message['type'] = "HANDOFF"
                neigh_ip = message['curr_node']

                self.requests.remove(x)
                new_reqs.remove(x)
                new_reqs.append(message)

                try:
                    self.socket_neigh.connect(f'tcp://{neigh_ip}')
                    self.socket_neigh.send_json(message)

                except Exception as e:
                    logger.error(f"Failed to connect to {neigh_ip}: {e}")
                finally:
                    self.socket_neigh.disconnect(f'tcp://{neigh_ip}')

        self.requests = new_reqs

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
            shopping_list_id = message['body']

            shopping_list = self.read_from_json(shopping_list_id, self.path)

            if shopping_list is None:
                self.send_message(self.socket, "Error couldn't find it", ServerMsgType.REPLY, identity)
            else:
                self.send_message(self.socket, shopping_list, ServerMsgType.REPLY, identity)

        elif message["type"] == ClientMsgType.POST:
            shopping_list = json.loads(message['body'])
            merged = self.persist_to_json(shopping_list, self.path)
            self.send_message(self.socket, merged, ServerMsgType.REPLY, identity)

            value, neighbours = self.ring.get_server(shopping_list['uuid'])
            neighbours.insert(0, value)

            self.handoff_replicate(neighbours, shopping_list)

        elif message["type"] == LoadbalMsgType.HEARTBEAT:
            logger.debug("Received load balancer heartbeat")
            pass

        elif message['type'] == ServerMsgType.REPLICATE:
            self.send_message(self.socket_neigh, "ACK", ServerMsgType.ACK)
            self.persist_to_json(message['body'], self.path)

        elif message['type'] == ServerMsgType.REBALANCE:
            shopping_lists = message['body']

            for sl in shopping_lists:
                self.persist_to_json(sl, self.path)

        elif message['type'] == ServerMsgType.HANDOFF_RECV:
            shopping_lists = message['body']

            for sl in shopping_lists:
                self.persist_to_json(sl, self.path)

        elif message['type'] == "JOIN_RING":
            node_ip = message['node'].split('@', 1)[-1]
            updates = self.ring.add_node(message['node'])

            self.send_data_on_join(updates)
            self.send_handoff_stored(message['node'])

        elif message['type'] == "RING":
            nodes = list(message['nodes'])
            self.ring = HashRing()
            self.ring.build_ring(nodes)

        elif message['type'] == "LEAVE_RING":
            print(message)

        elif message['type'] == ServerMsgType.HANDOFF:
            self.persist_to_json(message['body'], self.h_path)

        elif message['type'] == ServerMsgType.ACK:
            print("Received ACK")

        else:
            logger.error("Invalid message received: \"%s\"", message)

        self.loadbalLiveness = HEARTBEAT_LIVENESS

    def handoff_replicate(self, neighbours, shopping_list):
        cur_index = neighbours.index(self.identity)
        supposed_nodes = neighbours[:NUM_REPLICAS]

        max_tries = NUM_REPLICAS
        if self.identity in supposed_nodes:
            max_tries = NUM_REPLICAS - 1

        neighbours.remove(self.identity)
        actual_nodes = [self.identity]
        success_tries = 0

        for neigh in neighbours:
            if success_tries == max_tries:
                break

            print("CUR NEIGHBOURS: ", neigh)
            neigh_ip = neigh.split('@', 1)[-1]

            try:
                self.socket_neigh.connect(f'tcp://{neigh_ip}')

                self.send_message(self.socket_neigh, shopping_list, ServerMsgType.REPLICATE)

                if self.socket_neigh.poll(timeout=5000):
                    ack_res = json.loads(self.socket_neigh.recv().decode("utf-8"))
                    ident = "Server@" + ack_res['identity']

                    if ack_res['type'] == "ACK":
                        actual_nodes.append(neigh)
                        success_tries += 1

                    print(f"Received message: {ack_res}")
                else:
                    print("No message received within 2 seconds.")

            except zmq.error.ZMQError as e:
                print(f"Error connecting or receiving from {neigh}: {e}")
            finally:
                self.socket_neigh.disconnect(f'tcp://{neigh_ip}')

        print("SUPPOSED:", supposed_nodes)
        print("ORIGINAL:", actual_nodes)

        supposed_nodes2 = [item for item in supposed_nodes if item not in actual_nodes]
        actual_nodes2 = [item for item in actual_nodes if item not in supposed_nodes]

        supposed_nodes2 = supposed_nodes2[:len(actual_nodes2)]

        print("SUPPOSED:", supposed_nodes2)
        print("ORIGINAL:", actual_nodes2)

        for i in range(len(supposed_nodes2)):

            if self.identity == actual_nodes2[i]:
                handoff_msg = {'uuid': shopping_list['uuid'], 'destination': supposed_nodes2[i]}
                self.persist_to_json(handoff_msg, self.path)
                continue

            neigh_ip = actual_nodes2[i].split('@', 1)[-1]
            self.socket_neigh = self.context.socket(zmq.DEALER)
            try:
                self.socket_neigh.connect(f'tcp://{neigh_ip}')

                handoff_msg = {'uuid': shopping_list['uuid'], 'destination': supposed_nodes2[i]}

                self.send_message(self.socket_neigh, handoff_msg, ServerMsgType.HANDOFF)

            except zmq.error.ZMQError as e:
                print(f"Error connecting or receiving from {neigh_ip}: {e}")

            finally:
                self.socket_neigh.disconnect(f'tcp://{neigh_ip}')

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
        data = self.create_or_load_db_file(self.path)
        if max_hash == -1:
            filtered_lists = [shopping_list for shopping_list in data['ShoppingLists']
                              if min_hash < self.hash_function(shopping_list['uuid'])]
            return filtered_lists

        filtered_lists = [shopping_list for shopping_list in data['ShoppingLists']
                          if min_hash < self.hash_function(shopping_list['uuid']) < max_hash]

        return filtered_lists

    def create_or_load_db_file(self, file_path):
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

    def read_from_json(self, shopping_list, file_path):
        data = self.create_or_load_db_file(file_path)
        existing_list = data.get("ShoppingLists", [])

        for obj in existing_list:
            if obj.get("uuid") == shopping_list:
                return obj

        return None

    def send_handoff_stored(self, receiver):

        h_data = self.create_or_load_db_file(self.h_path)
        data = self.create_or_load_db_file(self.path)
        hd_list = h_data.get("ShoppingLists", [])
        d_list = data.get("ShoppingLists", [])

        uuids = []
        for item in hd_list:
            if item.get("destination") == receiver:
                uuids.append(item.get("uuid"))

        remaining_hdata = [item for item in hd_list if item.get("uuid") not in uuids]

        data = {"ShoppingLists": remaining_hdata}

        shopping_lists = [obj for obj in d_list if obj["uuid"] in uuids]

        neigh_ip = receiver.split('@', 1)[-1]

        with open(self.h_path, 'w') as file:
            json.dump(data, file, indent=2)

        if len(shopping_lists) == 0:
            return

        try:
            self.socket_neigh.connect(f'tcp://{neigh_ip}')
            self.send_message(self.socket_neigh, shopping_lists, ServerMsgType.HANDOFF_RECV)

        except zmq.error.ZMQError as e:
            print(f"Error connecting or receiving from {neigh_ip}: {e}")

        finally:
            self.socket_neigh.disconnect(f'tcp://{neigh_ip}')

    def persist_to_json(self, new_object, file_path):
        current_directory = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_directory, file_path)

        data = self.create_or_load_db_file(file_path)

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
    #server = Server(int(sys.argv[1]))
    server = Server(1227)
    server.start()
    server.stop()


if __name__ == "__main__":
    main()
