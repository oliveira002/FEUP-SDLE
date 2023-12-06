import json
import time
from HashRing import HashRing
import zmq
import os
from src.common.LoadbalMsgType import LoadbalMsgType
from src.common.ServerMsgType import ServerMsgType
from src.common.ClientMsgType import ClientMsgType
from src.common.utils import setup_logger, format_msg

# Logger setup
script_filename = os.path.splitext(os.path.basename(__file__))[0] + ".py"
logger = setup_logger(script_filename)

# Macros
FRONTEND_ENDPOINT = '127.0.0.1:6666'
BACKEND_ENDPOINT = '127.0.0.1:7777'
HEARTBEAT_LIVENESS = 3
HEARTBEAT_INTERVAL = 1.0


class LoadBalancer:
    def __init__(self):
        self.server_poller = None
        self.both_poller = None
        self.backend = None
        self.frontend = None
        self.context = zmq.Context.instance()
        self.ring = HashRing()

    def init_sockets(self):
        self.frontend = self.context.socket(zmq.ROUTER)
        self.frontend.bind(f"tcp://{FRONTEND_ENDPOINT}")

        self.backend = self.context.socket(zmq.ROUTER)
        self.backend.bind(f"tcp://{BACKEND_ENDPOINT}")

        self.server_poller = zmq.Poller()
        self.server_poller.register(self.backend, zmq.POLLIN)

        self.both_poller = zmq.Poller()
        self.both_poller.register(self.frontend, zmq.POLLIN)
        self.both_poller.register(self.backend, zmq.POLLIN)

    def kill_sockets(self):
        self.both_poller.unregister(self.frontend)
        self.both_poller.unregister(self.backend)
        self.server_poller.unregister(self.backend)

        self.frontend.setsockopt(zmq.LINGER, 0)
        self.backend.setsockopt(zmq.LINGER, 0)

        self.frontend.close()
        self.backend.close()

    def start(self):
        self.init_sockets()
        logger.info(f"Frontend listening on {FRONTEND_ENDPOINT}")
        logger.info(f"Backend listening on {BACKEND_ENDPOINT}")

        heartbeat_at = time.time() + HEARTBEAT_INTERVAL
        while True:
            if len(self.ring.nodes) > 0:
                poller = self.both_poller
            else:
                poller = self.server_poller
            sockets = dict(poller.poll(HEARTBEAT_INTERVAL * 1000))

            if self.backend in sockets and sockets.get(self.backend) == zmq.POLLIN:
                frames = self.backend.recv_multipart()
                if not frames:
                    break

                identity = frames[0].decode("utf-8")
                message = json.loads(frames[1].decode("utf-8"))
                logger.info(f"Received message \"{message}\" from {identity}")

                self.handle_server_message(identity, message)

                if time.time() >= heartbeat_at:
                    for server in self.ring.nodes:
                        self.send_message(self.backend, server, "Loadbalancer-PRIMARY", "HEARTBEAT", LoadbalMsgType.HEARTBEAT)
                    heartbeat_at = time.time() + HEARTBEAT_INTERVAL

            if self.frontend in sockets and sockets.get(self.frontend) == zmq.POLLIN:
                frames = self.frontend.recv_multipart()
                if not frames:
                    break

                identity = frames[0].decode("utf-8")
                message = json.loads(frames[2].decode("utf-8"))
                logger.info(f"Received message \"{message}\" from {identity}")

                self.handle_client_message(identity, message)

            # self.ring.nodes.purge()

    def stop(self):
        self.kill_sockets()
        self.context.term()

    def handle_server_message(self, identity, message):
        self.ring.add_node(identity)
        if message['type'] == "CONNECT":
            cur_ring_msg = self.ring.get_routing_table()
            request = [identity.encode("utf-8"), b"", b"", b"", json.dumps(cur_ring_msg).encode("utf-8")]
            self.backend.send_multipart(request)
            self.broadcast_message(identity, "JOIN_RING")
        elif message['type'] == ServerMsgType.REPLY:
            request = [message['identity'].encode("utf-8"), b"", json.dumps(message).encode("utf-8")]
            self.frontend.send_multipart(request)
        elif message['type'] == ServerMsgType.HEARTBEAT:
            pass



    def handle_client_message(self, identity, message):
        shopping_list = message['body']

        if message['type'] == ClientMsgType.POST:
            shopping_list = json.loads(shopping_list)['uuid']

        value, neighbours = self.ring.get_server(shopping_list)

        request = [value.encode("utf-8"), b"", identity.encode("utf-8"), b"", json.dumps(message).encode("utf-8")]

        self.backend.send_multipart(request)

    def send_message(self, socket, recipient_identity, sender_identity, message, msg_type: LoadbalMsgType):
        formatted_message = format_msg(sender_identity, message, msg_type.value)
        request = [recipient_identity.encode("utf-8"), b"", sender_identity.encode("utf-8"), b"", json.dumps(formatted_message).encode("utf-8")]
        socket.send_multipart(request)
        logger.info(f"Sent message \"{formatted_message}\"")

    def broadcast_message(self, new_worker, event):

        update_message = {
            "node": new_worker,
            "type": event
        }

        for worker in self.ring.nodes:
            if worker != new_worker:
                request = [worker.encode("utf-8"), b"", b"", b"", json.dumps(update_message).encode("utf-8")]
                self.backend.send_multipart(request)


def main():
    loadbalancer = LoadBalancer()
    loadbalancer.start()
    loadbalancer.stop()


if __name__ == "__main__":
    main()
