import time
import zmq
import os
import json
from uuid import *
import sys
import hashlib
from src.loadbalancer.HashRing import HashRing

from src.common.ClientMsgType import ClientMsgType
from src.common.LoadbalMsgType import LoadbalMsgType
from src.common.ServerMsgType import ServerMsgType
from src.common.utils import setup_logger, format_msg

# Logger setup
script_filename = os.path.splitext(os.path.basename(__file__))[0] + ".py"
logger = setup_logger(script_filename)

# Macros
BROKER_ENDPOINT_1 = '127.0.0.1:7777'
BROKER_ENDPOINT_2 = '127.0.0.1:7778'
HEARTBEAT_LIVENESS = 3
HEARTBEAT_INTERVAL = 1
INTERVAL_INIT = 1
INTERVAL_MAX = 32
N_REPLICAS = 3


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
        self.context = zmq.Context()

    def init_sockets(self):
        self.socket = self.context.socket(zmq.DEALER)
        self.socket_neigh = self.context.socket(zmq.DEALER)
        self.socket.identity = u"Server@{}".format(str(self.hostname)).encode("ascii")
        self.socket_neigh.identity = u"Server2@{}".format(str(self.hostname)).encode("ascii")

        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)
        self.poller.register(self.socket_neigh, zmq.POLLIN)

        self.socket.connect(f'tcp://{BROKER_ENDPOINT_1}')
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
        logger.info(f"Connecting to broker at {BROKER_ENDPOINT_1}")

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
                #logger.info(f"Received message \"{message}\" from {identity}")

                self.handle_message(identity, message)
                interval = INTERVAL_INIT
            else:
                self.loadbalLiveness -= 1
                if self.loadbalLiveness == 0:
                    logger.warning("Heartbeat failure, can't reach load balancer")
                    logger.warning("Reconnecting in %0.2fs..." % interval)
                    time.sleep(interval)

                    if interval < INTERVAL_MAX:
                        interval *= 2
                    self.kill_sockets()
                    self.init_sockets()
                    self.loadbalLiveness = HEARTBEAT_LIVENESS
            if time.time() > heartbeat_at:
                heartbeat_at = time.time() + HEARTBEAT_INTERVAL
                # logger.info("Sent heartbeat to load balancer")
                self.send_message(self.socket, "HEARTBEAT", ServerMsgType.HEARTBEAT, str(self.hostname))

    def generate_id(self):
        unique_id = str(uuid4())
        hashed_id = hashlib.md5(unique_id.encode()).hexdigest()
        self.id = hashed_id[:8]

    def replicate_data(self, neighbours, shopping_list):
        neighbours = [x.split('@', 1)[-1] for x in neighbours]
        #print(neighbours)

        for neighbour in neighbours:
            try:
                self.socket_neigh.connect(f'tcp://{neighbour}')
                self.send_message(self.socket_neigh, shopping_list, ServerMsgType.REPLICATE)
            except Exception as e:
                logger.error(f"Failed to connect to {neighbour}: {e}")

    def send_message(self, socket, message, msg_type: ServerMsgType, identity=None):
        formatted_message = format_msg(identity if identity is not None else str(self.hostname), message, msg_type.value)
        socket.send_json(formatted_message)
        #logger.info(f"Sent message \"{formatted_message}\"")

    def receive_message(self):
        try:
            _, identity, _, message = self.socket.recv_multipart()
            message = json.loads(message)
            identity = identity.decode("utf-8")
            #logger.info(f"Received message \"{message}\" from {identity}")
            return [identity, message]
        except zmq.error.ZMQError as e:
            logger.error("Error receiving message:", e)
            return None

    def handle_message(self, identity, message):
        if message["type"] == ClientMsgType.GET:
            #self.send_message(self.socket, "ALIVE", ServerMsgType.ACK, str(self.hostname))
            shopping_list_id = message['body']
            # need to check the json and merge (?) quorum
            self.send_message(self.socket, "Quase", ServerMsgType.REPLY, identity)

        elif message["type"] == ClientMsgType.POST:
            self.send_message(self.socket, "ALIVE", ServerMsgType.ACK, str(self.hostname))
            shopping_list = json.loads(message['body'])
            self.hinted_handoff(shopping_list, identity)

            #merged = self.persist_to_json(shopping_list)
            self.send_message(self.socket, "Modified Shopping List Correctly", ServerMsgType.REPLY, identity)
            #_, neighbours = self.ring.get_server(shopping_list['uuid'])
            #self.replicate_data(neighbours, merged)

        elif message["type"] == LoadbalMsgType.HEARTBEAT:
            # logger.info("Received load balancer heartbeat")
            pass

        elif message['type'] == ServerMsgType.REPLICATE:

            self.send_message(self.socket_neigh, "ACK", ServerMsgType.ACK)

            shopping_list = message['body']
            coordinator, neighbours = self.ring.get_server(shopping_list['uuid'])

            cur_identity = self.socket.identity.decode("utf-8")
            neighbours.insert(0, coordinator)

            cur_index = neighbours.index(cur_identity)

            if cur_index > N_REPLICAS - 1:
                # meaning I need to handoff later
                print(neighbours)
                print(cur_index)
                handoff_recipient = neighbours[cur_index % N_REPLICAS]
                print("HANDOFF:", handoff_recipient)
                pass

            print(shopping_list)
            self.persist_to_json(shopping_list)

        elif message['type'] == "JOIN_RING":
            print(message)
            self.ring.add_node(message['node'])

        elif message['type'] == "RING":
            nodes = list(message['nodes'])
            self.ring = HashRing()
            for server in nodes:
                self.ring.add_node(server)

        elif message['type'] == "LEAVE_RING":
            print(message)

        else:
            logger.error("Invalid message received: \"%s\"", message)

        self.loadbalLiveness = HEARTBEAT_LIVENESS


    def hinted_handoff(self, shopping_list, client_id):
        shopping_id = shopping_list['uuid']
        coordinator, neighbours = self.ring.get_server(shopping_id)
        cur_identity = self.socket.identity.decode("utf-8")
        neighbours.insert(0, coordinator)

        cur_index = neighbours.index(cur_identity)
        new_neighbours = neighbours[cur_index + 1:]
        new_neighbours = [x.split('@', 1)[-1] for x in new_neighbours]


        self.persist_to_json(shopping_list)

        if cur_index > N_REPLICAS - 1:
            #meaning I need to handoff later
            handoff_recipient = neighbours[cur_index % N_REPLICAS]
            print("HANDOFF:", handoff_recipient)
            pass

        counter = 0
        print(new_neighbours)
        acks_response = set()
        for neighbour in new_neighbours:
            try:
                if counter == 2:
                    break
                self.socket_neigh.connect(f'tcp://{neighbour}')
                self.send_message(self.socket_neigh, shopping_list, ServerMsgType.REPLICATE)

                socks = dict(self.poller.poll(2500))

                if self.socket_neigh in socks and socks[self.socket_neigh] == zmq.POLLIN:
                    ack_identity, message = self.receive_message_neighbour()
                    print(ack_identity)
                    print(neighbour)
                    if ack_identity == neighbour:
                        print("Received ACK from", ack_identity)
                        acks_response.add(ack_identity)
                        counter += 1
                    else:
                        print("Invalid ACK received from", ack_identity)
                else:
                    print(f"No ACK received from {neighbour} within 2.5 seconds.")

                print("RECEIVED ACKS:", acks_response)
            except zmq.error.ZMQError as e:
                print(f"Error connecting to {neighbour}: {e}")



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

    def persist_to_json(self, new_object):
        file_path = f"shoppinglists/{self.port}.json"
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


def main():
    server = Server(int(sys.argv[1]))
    server.start()
    server.stop()


if __name__ == "__main__":
    main()
