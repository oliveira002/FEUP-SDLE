import json

from src.common.PNCounter import PNCounter


class ShoppingListItem:
    """
    Shopping list item implementation.
    Makes use of vector clocks and PNCounter CRDTs

    ...

    Attributes
    ----------
    counter : PNCounter
        PNCounter object to store the amount of an item
    timestampMap : dict
        vector clock representation for events on the shopping item

    Methods
    -------
    add(quantity: int, userID: str):
        Adds a given quantity of items to the counter, increasing a given user's timestamp.
    remove(quantity: int, userID: str):
        Removes a given quantity of items to the counter, increasing a given user's timestamp.
    getName() -> str:
        Returns the name of the item.
    getQuantity() -> int:
        Returns the quantity of the item.
    increaseTimestamp(userID: str):
        Increases the timestamp of a given user by 1.
    """

    name: str = None
    counter: PNCounter = None
    timestampMap: dict = None

    def __init__(self, userID: str, name: str, quantity: int = 0):
        self.name = name
        self.counter = PNCounter()
        self.timestampMap = dict()
        self.add(quantity, userID)

    def add(self, quantity: int, userID: str):
        """
        Adds a given quantity of items to the counter, increasing a given user's timestamp.
        :param quantity : int:
        :param userID : str:
        :return: None
        """
        for _ in range(quantity):
            self.counter.inc()

        self.increaseTimestamp(userID)

    def remove(self, quantity: int, userID: str):
        """
        Removes a given quantity of items to the counter, increasing a given user's timestamp.
        :param quantity : int:
        :param userID : str:
        :return None:
        """
        for _ in range(quantity):
            self.counter.dec()

        self.increaseTimestamp(userID)

    def getQuantity(self):
        """
        Returns the quantity of the item.
        :return The quantity of the item:
        """
        return self.counter.query()

    def increaseTimestamp(self, userID: str):
        """
        Increases the timestamp of a given user by 1.
        :param userID : str:
        :return None:
        """
        timestamp = self.timestampMap.get(userID, 0)
        self.timestampMap[userID] = timestamp + 1

    def __str__(self):
        timestamps_str = ','.join(f"\"{key}\": {value}" for key, value in self.timestampMap.items())
        return f"{{\"quantity\": {self.counter.query()},\"timestamps\": {{{timestamps_str}}}}}"
