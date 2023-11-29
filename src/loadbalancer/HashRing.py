from hashlib import sha256
from sortedcollections import SortedDict
from itertools import islice
import bisect

HASH_SPACE = 2 ** 32
NUM_VNODES = 4
NUM_REPLICAS = 3


def hash_function(key):
    return sha256(key.encode('utf-8')).hexdigest()


class HashRing:
    def __init__(self, nodes=None, v_nodes=NUM_VNODES, hash_fn=hash_function, num_replicas=NUM_REPLICAS):
        if nodes is None:
            self.nodes = []

        self.hash_function = hash_fn
        self.v_nodes = v_nodes
        self.num_replicas = num_replicas
        self.ring = SortedDict()

    def add_node(self, key):
        for i in range(self.v_nodes):
            hashed = hash_function(key + '-' + str(i))
            self.ring[hashed] = key
            
        return

    def remove_node(self, key):
        for i in range(self.v_nodes):
            hashed = hash_function(key + '-' + str(i))
            del self.ring[hashed]
        return
    
    def get_server(self, list_id):
        hashed = hash_function(list_id)
        index = self.ring.bisect(hashed)
        if index < len(self.ring):
            next_key = self.ring.iloc[index]
            next_value = self.ring[next_key]
            return next_key, next_value
        else:
            return None, None
    def node_range(self, hashed_key, n):
        keys_before = list(islice(self.ring.irange(maximum=n, reverse=True), n))
        keys_after = list(islice(self.ring.irange(minimum=n), n))

        return keys_before, keys_after
