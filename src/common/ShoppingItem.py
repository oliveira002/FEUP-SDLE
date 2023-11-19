from src.common.PNCounter import PNCounter


class ShoppingItemCRDT:
    name: str = None
    counter: PNCounter = None
    timestampMap: dict = None

    def __int__(self, name: str, userID: str):
        self.name = name
        self.counter = PNCounter()
        self.timestampMap = {userID: 0}

    def add(self, quantity: int, userID: str):

        for _ in range(quantity):
            self.counter.inc()

        self.increaseTimestamp(userID)

    def remove(self, quantity: int, userID: str):

        for _ in range(quantity):
            self.counter.dec()

        self.increaseTimestamp(userID)

    def getValue(self):
        return self.counter.query()

    def increaseTimestamp(self, userID: str):
        timestamp = self.timestampMap.get(userID, 0)
        self.timestampMap[userID] = timestamp + 1
