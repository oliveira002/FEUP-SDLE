import os
import sys
from uuid import uuid4
from src.crdt.PNCounter import PNCounter

# Define module
current_path = os.path.dirname(__file__) + '/../..'
sys.path.append(current_path)


class ShoppingList:
    def __init__(self, uuid=None):
        self.items = dict()
        self.uuid = uuid4()
        if uuid is not None:
            self.uuid = uuid

    def inc_or_add_item(self, item_name, quantity, replica):
        item = self.items.get(item_name, PNCounter.zero())
        item.inc(replica, quantity)
        self.items[item_name] = item

    def dec_item(self, item_name, quantity, replica):
        item = self.items.get(item_name, PNCounter.zero())
        item.dec(replica, quantity)
        self.items[item_name] = item

    @staticmethod
    def merge(a, b):
        return

    def __str__(self):
        items = ", ".join(f"\"{key}\": {{{str(value)}}}" for key, value in self.items.items())
        return f"{{\"uuid\":\"{self.uuid}\", \"items\":{{{items}}}}}".replace("\'", "\"")

