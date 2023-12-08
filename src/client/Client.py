import json
import os
import sys
from uuid import *
import zmq

from src.common.ClientMsgType import ClientMsgType
from src.common.ServerMsgType import ServerMsgType
from src.common.ShoppingList import ShoppingList
from src.common.utils import setup_logger, format_msg

# Logger setup
script_filename = os.path.splitext(os.path.basename(__file__))[0] + ".py"
logger = setup_logger(script_filename)

# Macros
PRIMARY_FRONTEND_ENDPOINT = '127.0.0.1:6000'
BACKUP_FRONTEND_ENDPOINT = '127.0.0.1:6001'
SERVERS = [PRIMARY_FRONTEND_ENDPOINT, BACKUP_FRONTEND_ENDPOINT]
REQUEST_TIMEOUT = 2500
REQUEST_RETRIES = sys.maxsize
FAILOVER_DELAY = 5000


class Client:

    def __init__(self):
        self.retries_left = None
        self.socket = None
        self.id = uuid4()
        self.server_nr = 0
        self.context = zmq.Context()
    
    def init_socket(self):
        self.socket = self.context.socket(zmq.REQ)
        self.socket.identity = u"Client-{}".format(str(self.id)).encode("ascii")
        self.socket.connect(f'tcp://{SERVERS[self.server_nr]}')
    
    def kill_socket(self):
        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.close()
    
    def start(self):
        self.init_socket()
        logger.info(f"Connecting to broker at {PRIMARY_FRONTEND_ENDPOINT}")

        sl = ShoppingList()
        sl.inc_or_add_item("bananas", 1, "1231-31-23123-12-33")
        sl.inc_or_add_item("bananas", 2, "1231-31-23123-12-33")
        sl.inc_or_add_item("cebolas", 3, "1231-31-23123-12-33")
        sl.dec_item("cebolas", 2, "1231-31-23123-12-33")
        sl.uuid = '815bf169-4d4b-455f-a8b1-b9dadeaea9e3'
        self.send_message(str(self.id), str(sl), ClientMsgType.POST)

        self.retries_left = REQUEST_RETRIES
        while True:
            if (self.socket.poll(REQUEST_TIMEOUT) & zmq.POLLIN) != 0:
                message = self.receive_message()
                message = self.handle_message(message)
                if message:
                    break

            self.retries_left -= 1
            logger.warning("No response from server")

            self.kill_socket()

            # Rn the client is exiting after all the tries expire, IDK what to do later
            if self.retries_left == 0:
                logger.error("Server seems to be offline")
                sys.exit()

            logger.info("Attempting to reconnect to server")
            self.init_socket()
            self.send_message(str(self.id), str(sl), ClientMsgType.POST)

    def send_message(self, identity, message, msg_type: ClientMsgType):
        formatted_message = format_msg(identity, message, msg_type.value)
        self.socket.send_json(formatted_message)
        logger.info(f"Sent message \"{formatted_message}\"")

    def receive_message(self):
        try:
            message_json = self.socket.recv_string()
            message = json.loads(message_json)
            return message
        except zmq.error.ZMQError as e:
            logger.error("Error receiving message:", e)
            return None

    def handle_message(self, message):
        if not message:
            return None
        if message["type"] == ServerMsgType.REPLY:
            logger.info("Server replied with \"%s\"", message)
            self.retries_left = REQUEST_RETRIES
            return message["body"]
        else:
            logger.error("Invalid message received: \"%s\"", message)
            return None

    def stop(self):
        self.kill_socket()
        self.context.term()


def main():
    client = Client()
    client.start()
    client.stop()


if __name__ == "__main__":
    main()
