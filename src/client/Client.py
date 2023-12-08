import json
import os
import sys
import time
from uuid import *
import zmq

from src.common.ClientMsgType import ClientMsgType
from src.common.LoadbalMsgType import LoadbalMsgType
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
REQUEST_TIMEOUT = 1
REQUEST_RETRIES = 3
FAILOVER_DELAY = 2


class Client:

    def __init__(self):
        self.poller = None
        self.retries_left = None
        self.socket = None
        self.id = uuid4()
        self.server_nr = 0
        self.context = zmq.Context()
    
    def init_socket(self):
        self.socket = self.context.socket(zmq.REQ)
        self.socket.identity = u"Client-{}".format(str(self.id)).encode("ascii")
        self.socket.connect(f'tcp://{SERVERS[self.server_nr]}')

        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)
    
    def kill_socket(self):
        self.poller.unregister(self.socket)
        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.close()
    
    def start(self):
        self.init_socket()
        logger.info(f"Connecting to broker at {SERVERS[self.server_nr]}")

        sl = ShoppingList()
        sl.inc_or_add_item("bananas", 1, "1231-31-23123-12-33")
        sl.inc_or_add_item("bananas", 2, "1231-31-23123-12-33")
        sl.inc_or_add_item("cebolas", 3, "1231-31-23123-12-33")
        sl.dec_item("cebolas", 2, "1231-31-23123-12-33")
        self.send_message(str(self.id), str(sl), ClientMsgType.POST)

        self.retries_left = REQUEST_RETRIES
        while True:
            #sockets = dict(self.poller.poll(REQUEST_TIMEOUT * 1000))
            if (self.socket.poll(REQUEST_TIMEOUT * 1000) & zmq.POLLIN) != 0:
            #if self.socket in sockets and sockets.get(self.socket) == zmq.POLLIN:
                message = self.receive_message()
                message = self.handle_message(message)
                if message:
                    break
                print(message)
            else:
                self.retries_left -= 1
                if self.retries_left == 0:
                    logger.warning("Server seems to be offline")
                    logger.warning("Failing over in %0.2fs..." % FAILOVER_DELAY)
                    time.sleep(FAILOVER_DELAY)

                    self.server_nr = (self.server_nr + 1) % 2
                    self.retries_left = REQUEST_RETRIES
                    self.kill_socket()
                    self.init_socket()
                    continue

                self.kill_socket()
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
        if message["type"] == LoadbalMsgType.SV_OFFLINE:
            self.retries_left = REQUEST_RETRIES
            return
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
