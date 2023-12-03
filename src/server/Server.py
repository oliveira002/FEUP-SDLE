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

        self.send_message("Initial Setup", "CONNECT")

        while True:
            request = self.receive_message()
            if request is not None:
                self.send_message_response(request[0], "RESOURCE 1")

    def send_message(self, body, message_type):
        formatted_message = {
            "identity": str(self.hostname),
            "body": body,
            "type": message_type
        }
        self.socket.send_json(formatted_message)

    def send_message_response(self, client_identity, body):
        formatted_message = {
            "identity": client_identity.decode("utf-8"),
            "body": body,
            "type": "REPLY"
        }
        self.socket.send_json(formatted_message)

    def receive_message(self):
        try:
            # Receive the message as a JSON-encoded string
            identity, _, message = self.socket.recv_multipart()
            message = json.loads(message)
            logger.info(f"Received message \"{message}\" from {identity}")
            return identity, message
        except zmq.error.ZMQError as e:
            logger.error("Error receiving message:", e)
            return None

    def persist_shopping_list(self,json_object):
        file_path = f"{self.hostname}.json"

        # Check if the file exists
        if os.path.exists(file_path):
            # If the file exists, check if the JSON object already exists based on the 'uuid' field
            existing_data = self.read_json_file(file_path)
            existing_uuids = [item.get('uuid') for item in existing_data]

            if json_object.get('uuid') in existing_uuids:
                # If the JSON object with the same 'uuid' exists, call the merge function
                #merged_data = self.merge(existing_data, json_object)
                self.write_json_file(file_path, json_object)
            else:
                # If the JSON object with the same 'uuid' does not exist, append to the file
                existing_data.append(json_object)
                self.write_json_file(file_path, existing_data)
        else:
            # If the file doesn't exist, create it and write the JSON object to it
            self.write_json_file(file_path, [json_object])

    def read_json_file(self, file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data

    def write_json_file(self, file_path, data):
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=2)

    def merge(self, existing_data, new_data):
        return


    def stop(self):
        self.socket.close()
        self.context.term()


def main():
    server = Server(HOST, int(sys.argv[1]))
    sl = ShoppingList()
    sl.inc_or_add_item("bananas", 1, "1231-31-23123-12-33")
    sl.inc_or_add_item("bananas", 2, "1231-31-23123-12-33")
    sl.inc_or_add_item("cebolas", 3, "1231-31-23123-12-33")
    sl.dec_item("cebolas", 2, "1231-31-23123-12-33")
    print(sl)
    server.start()
    server.stop()


if __name__ == "__main__":
    main()
