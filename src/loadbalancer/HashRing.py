import json
import os
from hashlib import sha256
from sortedcollections import SortedDict
import bisect
import sys

# Define module
current_path = os.path.dirname(__file__) + '/../..'
sys.path.append(current_path)

HASH_SPACE = sys.maxsize
NUM_VNODES = 4
NUM_REPLICAS = 3


def hash_function(key):
    hash_value = sha256(key.encode('utf-8')).hexdigest()
    #integer_hash = int(hash_value, 16)
    return hash_value


class HashRing:
    def __init__(self, v_nodes=NUM_VNODES, hash_fn=hash_function, num_replicas=NUM_REPLICAS):
        self.nodes = set()
        self.hash_function = hash_fn
        self.v_nodes = v_nodes
        self.num_replicas = num_replicas
        self.ring = SortedDict()

    def add_node(self, key):
        self.nodes.add(key)
        info = []
        for i in range(self.v_nodes):
            hashed = hash_function(key + '-' + str(i))
            self.ring[hashed] = key
            if len(self.ring) > NUM_VNODES:
                update_info = self.rebalance_ring(hashed)
                if update_info['send'] != update_info['receive']:
                    info.append(update_info)
        return info

    def remove_node(self, key):
        self.nodes.remove(key)
        for i in range(self.v_nodes):
            hashed = hash_function(key + '-' + str(i))
            del self.ring[hashed]
        return

    def get_server(self, shopping_list_id, num_keys=NUM_REPLICAS):

        if len(self.nodes) == 0:
            return None, None

        hashed = hash_function(shopping_list_id)
        keys = list(self.ring.keys())
        index = bisect.bisect_left(keys, hashed)

        if index >= len(self.ring):
            index = 0

        coordinator_key = keys[index]
        coordinator_identity = self.ring[coordinator_key]
        neighbours = self.node_range(coordinator_key)

        neighbours = [self.ring[x] for x in neighbours if self.ring[x] != coordinator_identity]
        neighbours = list(dict.fromkeys(neighbours))

        return coordinator_identity, neighbours

    def build_ring(self, routing_table):
        for x in routing_table:
            self.add_node(x)

    def node_range(self, hashed_key, n=NUM_REPLICAS - 1):
        keys = list(self.ring.keys())
        total_keys = len(keys)

        start_index = keys.index(hashed_key) + 1
        all_neighbours = keys[start_index:] + keys[:start_index]

        all_neighbours.remove(hashed_key)

        return all_neighbours

    def __str__(self):
        serialized_data = {
            "dic": self.ring,
            "nodes": self.nodes
        }
        return json.dumps(serialized_data)

    def get_routing_table(self):
        serialized_data = {
            "nodes": list(self.nodes),
            "type": "RING"
        }

        return serialized_data

    def rebalance_ring(self, hashed):
        neighbours = self.node_range(hashed)

        keys = list(self.ring.keys())

        neigh_before = neighbours[-1]
        neigh_after = neighbours[0]

        if keys[-1] == hashed:
            msg = {'send': self.ring[keys[0]], 'receive': self.ring[hashed], 'content': [neigh_before, hashed]}
            return msg

        elif keys[0] == hashed:
            msg = {'send': self.ring[keys[1]], 'receive': self.ring[hashed], 'content': [neigh_before, -1]}
            return msg

        msg = {'send': self.ring[neigh_after], 'receive': self.ring[hashed], 'content': [neigh_before, hashed]}
        return msg



#hash_ring = HashRing()
#msg_1 = hash_ring.add_node("Server@127.0.0.1:1225")
#msg_1 = hash_ring.add_node("Server@127.0.0.1:1226")
#msg_1 = hash_ring.add_node("Server@127.0.0.1:1227")
#msg_1 = hash_ring.add_node("Server@127.0.0.1:1228")
#msg_1 = hash_ring.add_node("Server@127.0.0.1:1229")
#print(hash_ring.get_server('815bf169-4d4b-455f-a8b1-b9dadeaea9e3'))