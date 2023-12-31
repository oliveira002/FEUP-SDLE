import json
import sys
import time
from HashRing import HashRing
import zmq
import os
from src.common.LoadbalMsgType import LoadbalMsgType
from src.common.ServerMsgType import ServerMsgType
from src.common.ClientMsgType import ClientMsgType
from src.common.utils import setup_logger, format_msg
from src.loadbalancer.BinaryLBState import LoadbalancerState, BStarException, lbfsm_state_map, BinaryLBState

# Define module
current_path = os.path.dirname(__file__) + '/../..'
sys.path.append(current_path)

# Logger setup
script_filename = os.path.splitext(os.path.basename(__file__))[0] + ".py"
logger = setup_logger(script_filename)

# Macros
PRIMARY_FRONTEND_ENDPOINT = '127.0.0.1:6000'
PRIMARY_PUBSUB_ENDPOINT = '127.0.0.1:6500'
PRIMARY_BACKEND_ENDPOINT = '127.0.0.1:7000'
BACKUP_FRONTEND_ENDPOINT = '127.0.0.1:6001'
BACKUP_PUBSUB_ENDPOINT = '127.0.0.1:6501'
BACKUP_BACKEND_ENDPOINT = '127.0.0.1:7001'
HEARTBEAT_LIVENESS = 3
HEARTBEAT_INTERVAL = 1


def run_fsm(lb_state: LoadbalancerState):
    # There are some transitional states we do not want to handle
    state_dict = lbfsm_state_map.get(lb_state.state, {})
    res = state_dict.get(lb_state.event)
    if res:
        msg, state = res
    else:
        return

    if state is False:
        logger.critical(msg)
        raise BStarException(msg)
    elif msg == BinaryLBState.CLIENT_REQUEST:
        assert lb_state.peer_expiry > 0
        if time.time() > lb_state.peer_expiry:
            lb_state.state = BinaryLBState.SELF_ACTIVE
        else:
            raise BStarException()
    else:
        logger.info(msg)
        lb_state.state = state


class LoadBalancer:
    def __init__(self, role):
        self.sub = None
        self.pub = None
        self.role = role
        self.server_poller = None
        self.all_poller = None
        self.backend = None
        self.frontend = None
        self.context = zmq.Context.instance()
        self.ring = HashRing()
        self.lb_state = LoadbalancerState(BinaryLBState.NONE, 0, 0)
        self.requests = []

    def init_sockets(self):
        self.pub = self.context.socket(zmq.PUB)
        self.sub = self.context.socket(zmq.SUB)
        self.sub.setsockopt_string(zmq.SUBSCRIBE, u"")
        self.frontend = self.context.socket(zmq.ROUTER)
        self.backend = self.context.socket(zmq.ROUTER)
        
        if self.role == "primary":
            self.frontend.bind(f"tcp://{PRIMARY_FRONTEND_ENDPOINT}")
            self.backend.bind(f"tcp://{PRIMARY_BACKEND_ENDPOINT}")

            self.pub.bind(f"tcp://{PRIMARY_PUBSUB_ENDPOINT}")

            self.sub.connect(f"tcp://{BACKUP_PUBSUB_ENDPOINT}")

            self.lb_state.state = BinaryLBState.SELF_PRIMARY

            logger.info(f"Frontend listening on {PRIMARY_FRONTEND_ENDPOINT}")
            logger.info(f"Backend listening on {PRIMARY_BACKEND_ENDPOINT}")
            logger.info("Primary, waiting for backup")
        elif self.role == "backup":
            self.frontend.bind(f"tcp://{BACKUP_FRONTEND_ENDPOINT}")
            self.backend.bind(f"tcp://{BACKUP_BACKEND_ENDPOINT}")

            self.pub.bind(f"tcp://{BACKUP_PUBSUB_ENDPOINT}")

            self.sub.connect(f"tcp://{PRIMARY_PUBSUB_ENDPOINT}")
            self.sub.setsockopt_string(zmq.SUBSCRIBE, u"")

            self.lb_state.state = BinaryLBState.SELF_BACKUP

            logger.info(f"Frontend listening on {BACKUP_FRONTEND_ENDPOINT}")
            logger.info(f"Backend listening on {BACKUP_BACKEND_ENDPOINT}")
            logger.info("Backup, waiting for primary")

        self.server_poller = zmq.Poller()
        self.server_poller.register(self.backend, zmq.POLLIN)
        self.server_poller.register(self.sub, zmq.POLLIN)
        self.server_poller.register(self.pub, zmq.POLLIN)

        self.all_poller = zmq.Poller()
        self.all_poller.register(self.frontend, zmq.POLLIN)
        self.all_poller.register(self.backend, zmq.POLLIN)
        self.all_poller.register(self.sub, zmq.POLLIN)
        self.all_poller.register(self.pub, zmq.POLLIN)

    def kill_sockets(self):
        self.server_poller.unregister(self.backend)
        self.server_poller.unregister(self.sub)
        self.server_poller.unregister(self.pub)

        self.all_poller.unregister(self.frontend)
        self.all_poller.unregister(self.backend)
        self.all_poller.unregister(self.sub)
        self.all_poller.unregister(self.pub)

        self.frontend.setsockopt(zmq.LINGER, 0)
        self.backend.setsockopt(zmq.LINGER, 0)
        self.sub.setsockopt(zmq.LINGER, 0)
        self.pub.setsockopt(zmq.LINGER, 0)

        self.frontend.close()
        self.backend.close()
        self.pub.close()
        self.sub.close()

    def start(self):
        self.init_sockets()

        heartbeat_at = time.time() + HEARTBEAT_INTERVAL
        send_state_at = time.time() + HEARTBEAT_INTERVAL
        while True:
            #if len(self.ring.nodes) > 0:
            poller = self.all_poller
            #else:
             #   poller = self.server_poller
            sockets = dict(poller.poll(HEARTBEAT_INTERVAL * 1000))
            if self.backend in sockets and sockets.get(self.backend) == zmq.POLLIN:
                rec_time = time.time()
                frames = self.backend.recv_multipart()
                if not frames:
                    break

                identity = frames[0].decode("utf-8")
                message = json.loads(frames[1].decode("utf-8"))
                logger.info(f"Received message \"{message}\" from {identity}")

                self.check_requests(identity, message, rec_time)

                self.lb_state.event = BinaryLBState.CLIENT_REQUEST
                try:
                    run_fsm(self.lb_state)
                    if self.lb_state.state != BinaryLBState.SELF_PASSIVE:
                        self.handle_server_message(identity, message, rec_time)
                except BStarException:
                    del frames, identity, message

                if time.time() >= heartbeat_at:
                    for server in self.ring.nodes:
                        self.send_message(self.backend, server, "Loadbalancer", "HEARTBEAT",
                                          LoadbalMsgType.HEARTBEAT)
                    heartbeat_at = time.time() + HEARTBEAT_INTERVAL

            if self.frontend in sockets and sockets.get(self.frontend) == zmq.POLLIN:
                frames = self.frontend.recv_multipart()
                if not frames:
                    break

                identity = frames[0].decode("utf-8")
                message = json.loads(frames[2].decode("utf-8"))
                if message["type"] != ServerMsgType.HEARTBEAT:
                    logger.info(f"Received message \"{message}\" from {identity}")
                else:
                    logger.debug(f"Received message \"{message}\" from {identity}")

                self.lb_state.event = BinaryLBState.CLIENT_REQUEST
                try:
                    run_fsm(self.lb_state)
                    if self.lb_state.state != BinaryLBState.SELF_PASSIVE:
                        self.handle_client_message(identity, message)
                except BStarException:
                    del frames, identity, message

            if self.sub in sockets and sockets.get(self.sub) == zmq.POLLIN:
                msg = self.sub.recv().decode("utf-8")
                msg = json.loads(msg)

                if msg['type'] == "STATE":
                    self.lb_state.event = msg['state']
                    del msg
                    try:
                        run_fsm(self.lb_state)
                        self.lb_state.peer_expiry = time.time() + (2 * HEARTBEAT_INTERVAL)
                    except BStarException:
                        break
                else:
                    nodes = list(msg['nodes'])
                    if len(nodes) > 0 and nodes != self.ring.nodes:
                        new_ring = HashRing()
                        new_ring.build_ring(nodes)
                        self.ring = new_ring

            if time.time() >= send_state_at:
                msg = {'state': self.lb_state.state, 'type': 'STATE'}
                self.pub.send_json(msg)

                if self.lb_state.state == BinaryLBState.SELF_ACTIVE:
                    self.pub.send_json(self.ring.get_routing_table())

                send_state_at = time.time() + HEARTBEAT_INTERVAL

            # self.ring.nodes.purge()

    def stop(self):
        self.kill_sockets()
        self.context.term()

    def sync_routers(self):
        routing_table = self.ring.get_routing_table()
        self.pub.send_json(routing_table)

    def handle_server_message(self, identity, message, rec_time):
        self.ring.add_node(identity)
        if message['type'] == ServerMsgType.CONNECT:
            cur_ring_msg = self.ring.get_routing_table()
            request = [identity.encode("utf-8"), b"", b"", b"", json.dumps(cur_ring_msg).encode("utf-8")]
            self.backend.send_multipart(request)
            self.broadcast_message(identity, "JOIN_RING")
        elif message['type'] == ServerMsgType.REPLY_GET or message['type'] == ServerMsgType.REPLY_POST or message['type'] == ServerMsgType.REPLY:
            request = [message['identity'].encode("utf-8"), b"", json.dumps(message).encode("utf-8")]
            self.frontend.send_multipart(request)
        elif message['type'] == "ACK":
            #print("RECEIVEDDDD")
            pass
        elif message['type'] == ServerMsgType.HEARTBEAT:
            pass

    def check_requests(self, identity, message, rec_time):
        new_reqs = list(self.requests)
        for x in self.requests:
            #print(x)
            if identity == x['curr_node'] and message['identity'] == x['identity']:
                self.requests.remove(x)
                new_reqs.remove(x)
                continue

            if x['entry_time'] + 2 < rec_time:
                self.requests.remove(x)
                new_reqs.remove(x)
                x['liveness'] -= 1
                x['entry_time'] = time.time()
                shopping_list = x['body']

                if x['type'] == ClientMsgType.POST:
                    shopping_list = json.loads(shopping_list)['uuid']

                value, neighbours = self.ring.get_server(shopping_list)

                neighbours.insert(0, value)

                next_idx = neighbours.index(x['curr_node']) + 1

                if (value is None and neighbours is None) or next_idx >= len(neighbours):
                    message = format_msg("BROKER", "Servers offline", LoadbalMsgType.SV_OFFLINE)
                    self.frontend.send_multipart(
                        [identity.encode("utf-8"), b"", json.dumps(message).encode("utf-8")])
                    return

                x['liveness'] = 1
                x['curr_node'] = neighbours[next_idx]

                new_reqs.append(x)

                original_req = dict(x)

                del original_req['entry_time']
                del original_req['liveness']
                del original_req['curr_node']

                #print(x['identity'])
                request = [x['curr_node'].encode("utf-8"), b"", x['identity'].encode("utf-8"), b"",
                           json.dumps(original_req).encode("utf-8")]

                self.backend.send_multipart(request)

        self.requests = new_reqs

    def handle_client_message(self, identity, message):
        shopping_list = message['body']

        if message['type'] == ClientMsgType.POST:
            shopping_list = json.loads(shopping_list)['uuid']

        value, neighbours = self.ring.get_server(shopping_list)

        if value is None and neighbours is None:
            message = format_msg("BROKER", "Servers offline", LoadbalMsgType.SV_OFFLINE)
            self.frontend.send_multipart([identity.encode("utf-8"), b"", json.dumps(message).encode("utf-8")])
            return

        request = [value.encode("utf-8"), b"", identity.encode("utf-8"), b"", json.dumps(message).encode("utf-8")]
        message['curr_node'] = value
        message['liveness'] = 1
        message['entry_time'] = time.time()

        self.requests.append(message)
        #print(request)
        self.backend.send_multipart(request)


    def send_message(self, socket, recipient_identity, sender_identity, message, msg_type: LoadbalMsgType):
        formatted_message = format_msg(sender_identity, message, msg_type.value)
        request = [recipient_identity.encode("utf-8"), b"", sender_identity.encode("utf-8"), b"",
                   json.dumps(formatted_message).encode("utf-8")]
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
    roles = ["primary", "backup", "p", "b"]
    role = None

    try:
        role = sys.argv[1]
    except:
        while role not in roles:
            role = str(input("Choose a role between \"primary\" and \"backup\": "))

    if role == "p":
        role = "primary"
    elif role == "b":
        role = "backup"

    loadbalancer = LoadBalancer(role)
    loadbalancer.start()
    loadbalancer.stop()


if __name__ == "__main__":
    main()
