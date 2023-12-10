from src.common.GCounter import GCounter
import os
import sys

# Define module
current_path = os.path.dirname(__file__) + '/../..'
sys.path.append(current_path)


class PNCounter:
    def __init__(self, pos, neg):
        self.pos = pos
        self.neg = neg

    @staticmethod
    def zero():
        return PNCounter(GCounter.zero(), GCounter.zero())

    def value(self):
        return self.pos.value() - self.neg.value()

    def inc(self, replica, value):
        self.pos.inc(replica, value)

    def dec(self, replica, value):
        self.neg.inc(replica, value)

    @staticmethod
    def merge(a, b):
        return PNCounter(GCounter.merge(a.pos, b.pos), GCounter.merge(a.neg, b.neg))

    def __str__(self):
        return f"\"pos\":{str(self.pos)}, \"neg\":{str(self.neg)}".replace("\'", "\"")

    def __repr__(self):
        return str(self)
