import zmq
import sys
import os
import json
import logging

from src.common.ShoppingList import ShoppingList
from src.common.ShoppingListItem import ShoppingListItem

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
PORT = 7777
BROKER = HOST + ":" + str(PORT)


class Server:
    host: str = None
    port: int = None
    context: zmq.Context = None
    socket: zmq.Context.socket = None

    def __init__(self, host=HOST, port=PORT):
        self.hostname = None
        self.host = host
        self.port = int(port)
        self.context = zmq.Context()

    def start(self):
        hostname = f"{self.host}:{self.port}"
        self.hostname = hostname
        self.socket = self.context.socket(zmq.REQ)
        self.socket.identity = u"Server@{}".format(hostname).encode("ascii")
        self.socket.connect(f'tcp://{BROKER}')
        logger.info(f'Server connected to Broker at {BROKER}')
        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)

        self.send_message("Initial Setup", "CONNECT")

        while True:
            socks = dict(self.poller.poll())
            if self.socket in socks and socks[self.socket] == zmq.POLLIN:
                request = self.receive_message()
                client_id, req = request[0], request[1]
                if req['type'] == 'POST':
                    self.persist_to_json(req['body'])
                    self.send_message_response(client_id, "RESOURCE 1")

    def send_message(self, body, message_type):
        formatted_message = {
            "identity": str(self.hostname),
            "body": body,
            "type": message_type
        }
        self.socket.send_json(formatted_message)

    def send_message_response(self, client_identity, body):
        formatted_message = {
            "identity": client_identity,
            "body": body,
            "type": "REPLY"
        }
        self.socket.send_json(formatted_message)

    def receive_message(self):
        try:
            identity, _, message = self.socket.recv_multipart()
            message = json.loads(message)
            identity = identity.decode("utf-8")
            logger.info(f"Received message \"{message}\" from {identity}")
            return [identity, message]

        except zmq.error.ZMQError as e:
            logger.error("Error receiving message:", e)
            return None

    def persist_to_json(self,new_object):
        file_path = f"{self.hostname}.json"

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

    def read_json_file(self, file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data

    def write_json_file(self, file_path, data):
        json_data = json.loads(data)
        with open(file_path, 'w') as file:
            json_data = json.dumps(json_data, ensure_ascii=False)
            file.write(json_data)
            file.close()

    def merge(self, existing_data, new_data):
        return


    def stop(self):
        self.socket.close()
        self.context.term()


def main():
    server = Server(HOST, int(sys.argv[1]))
    server.start()
    server.stop()


if __name__ == "__main__":
    main()
