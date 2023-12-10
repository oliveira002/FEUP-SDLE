from src.crdt.GCounter import GCounter
from src.crdt.PNCounter import PNCounter
from src.crdt.ShoppingList import ShoppingList


class PropertyTesting:
    pass


def main():
    gc = GCounter.zero()
    gc.inc("5fb2f941-0c40-4aef-b48f-746540e3c723", 5)
    gc.inc("5fb2f941-0c40-4aef-b48f-746540e3c723", 5)
    gc.inc("263bf63c-b5fd-4beb-95c5-396f14167ee0", 2)
    print(gc)

    gc2 = GCounter({"5fb2f941-0c40-4aef-b48f-746540e3c723": 8})
    gc3 = GCounter.merge(gc, gc2)
    gc3 = GCounter.merge(gc3, gc2)
    print(gc3)

    pn = PNCounter(gc, gc2)
    print(pn)

    sl = ShoppingList()
    replica = "5fb2f941-0c40-4aef-b48f-746540e3c723"
    sl.inc_or_add_item("banana", 8, replica)
    sl.inc_or_add_item("cebolas", 4, replica)
    sl.dec_item("banana", 2, replica)
    print(sl)


if __name__ == '__main__':
    main()
