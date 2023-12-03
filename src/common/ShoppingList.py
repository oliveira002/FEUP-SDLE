from src.common.ShoppingListItem import ShoppingListItem


class ShoppingList:

    items: dict = None

    def inc_or_add_item(self, name: str, quantity: int, userID: str):
        # Check if item already exists
        if name in self.items:
            item = self.items[name]
            item.add(quantity, userID)
            self.items[name] = item
        else:
            item = ShoppingListItem(name, userID, quantity)
            self.items[name] = item

    def dec_item(self, name: str, quantity: int, userID: str):
        # Check if item exists
        if name in self.items:
            item = self.items[name]
            item.remove(quantity, userID)
            self.items[name] = item




'''
ShoppingList = {
    "banana" : ShoppingListItem
}

ShoppingListItem = {
    quantity: counter.query()
    timestamps : timestampMap
}
'''