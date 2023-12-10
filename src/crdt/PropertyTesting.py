from src.common.GCounter import GCounter
from src.common.PNCounter import PNCounter
from src.common.ShoppingList import ShoppingList


def main():
    gc = GCounter.zero()
    gc.inc("5fb2f941-0c40-4aef-b48f-746540e3c723", 5)
    gc.inc("5fb2f941-0c40-4aef-b48f-746540e3c723", 5)
    gc.inc("263bf63c-b5fd-4beb-95c5-396f14167ee0", 2)
    #print(gc)

    gc2 = GCounter({"5fb2f941-0c40-4aef-b48f-746540e3c723": 8})
    gc3 = GCounter.merge(gc, gc2)
    gc3 = GCounter.merge(gc3, gc2)
    #print(gc3)

    pn = PNCounter(gc, gc2)
    #print(pn)

    sl1 = ShoppingList("5fb2f941-0c40-4aef-b48f-746540e3c725")
    replica = "5fb2f941-0c40-4aef-b48f-746540e3c723"
    sl1.inc_or_add_item("banana", 8, replica)
    sl1.inc_or_add_item("cebolas", 4, replica)
    sl1.dec_item("banana", 2, replica)
    sl1.inc_or_add_item("cenouras", 1, replica)
    sl1.inc_or_add_item("banana", 2, replica)
    print("SL1", str(sl1))

    sl2 = ShoppingList("5fb2f941-0c40-4aef-b48f-746540e3c725")
    replica = "263bf63c-b5fd-4beb-95c5-396f14167ee0"
    sl2.inc_or_add_item("banana", 2, replica)
    sl2.inc_or_add_item("pão", 3, replica)
    print("SL2", str(sl2))

    sl3 = ShoppingList.merge(sl1, sl2)
    print("SL3", str(sl3))


if __name__ == '__main__':
    main()
