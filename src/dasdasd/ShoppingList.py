import os
import sys
from uuid import uuid4
from src.dasdasd.ShoppingListItem import ShoppingListItem

# Define module
current_path = os.path.dirname(__file__) + '/../..'
sys.path.append(current_path)


class ShoppingList:

    items: dict = None

    def __init__(self):
        self.items = dict()
        self.uuid = uuid4()

    def inc_or_add_item(self, name: str, quantity: int, userID: str):
        # Check if item already exists
        if name in self.items:
            item = self.items[name]
            item.add(quantity, userID)
            self.items[name] = item
        else:
            item = ShoppingListItem(userID, name, quantity)
            self.items[name] = item

    def dec_item(self, name: str, quantity: int, userID: str):
        # Check if item exists
        if name in self.items:
            item = self.items[name]
            item.remove(quantity, userID)
            self.items[name] = item

    def __str__(self):
        items_str = ','.join(f"\"{key}\": {value}" for key, value in self.items.items())
        return f"{{\"uuid\": \"{self.uuid}\",\"items\": {{{items_str}}}}}"
