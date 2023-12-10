import os
import sys

# Define module
current_path = os.path.dirname(__file__) + '/../..'
sys.path.append(current_path)


class GCounter:
    def __init__(self, counter):
        self.counter = counter

    @staticmethod
    def zero():
        return GCounter({})

    def value(self):
        return sum(self.counter.values(), 0)

    def inc(self, replica, value):
        self.counter[replica] = self.counter.get(replica, 0) + value

    @staticmethod
    def merge(a, b):
        merged_counter = {k: max(a.counter.get(k, 0), b.counter.get(k, 0)) for k in set(a.counter) | set(b.counter)}
        return GCounter(merged_counter)

    def __str__(self):
        return str(self.counter)
