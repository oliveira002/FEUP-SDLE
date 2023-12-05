import json
from hashlib import sha256
from sortedcollections import SortedDict
from itertools import islice
import bisect
import sys

HASH_SPACE = sys.maxsize
NUM_VNODES = 4
NUM_REPLICAS = 3


def hash_function(key):
    return sha256(key.encode('utf-8')).hexdigest()


class HashRing:
    def __init__(self, v_nodes=NUM_VNODES, hash_fn=hash_function, num_replicas=NUM_REPLICAS):
        self.nodes = set()
        self.hash_function = hash_fn
        self.v_nodes = v_nodes
        self.num_replicas = num_replicas
        self.ring = SortedDict()


    def add_node(self, key):
        self.nodes.add(key)
        for i in range(self.v_nodes):
            hashed = hash_function(key + '-' + str(i))
            self.ring[hashed] = key


    def remove_node(self, key):
        for i in range(self.v_nodes):
            hashed = hash_function(key + '-' + str(i))
            del self.ring[hashed]
        return
    
    def get_server(self, shopping_list_id, num_keys=NUM_REPLICAS):
        hashed = hash_function(shopping_list_id)
        keys = list(self.ring.keys())
        index = bisect.bisect_left(keys, hashed)

        if index >= len(self.ring):
            index = 0

        coordinator_key = keys[index]
        coordinator_identity = self.ring[coordinator_key]
        neighbours = self.node_range(coordinator_key)

        neighbours = [self.ring[x] for x in neighbours if self.ring[x] != coordinator_identity]
        neighbours = list(set(neighbours))

        return coordinator_identity, neighbours

    def node_range(self, hashed_key, n=NUM_REPLICAS - 1):
        keys = list(self.ring.keys())
        keys.extend(keys[:n])

        index = keys.index(hashed_key)
        next_elements = keys[index + 1:index + 1 + n]

        return next_elements

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



