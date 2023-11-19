from src.common.PNCounter import PNCounter


class ShoppingListItem:
    """
    Shopping list item implementation.
    Makes use of vector clocks and PNCounter CRDTs

    ...

    Attributes
    ----------
    name : str
        the name of the shopping list item
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

    def __int__(self, name: str, userID: str):
        self.name = name
        self.counter = PNCounter()
        self.timestampMap = {userID: 0}

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

    def getName(self):
        """
        Returns the name of the item.
        :return The name of the item:
        """
        return self.name

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
