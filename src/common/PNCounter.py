from src.common.GCounter import GCounter


class PNCounter:
    """
    Simple Positive-Negative Counter CRDT implementation.

    ...

    Attributes
    ----------
    pos : GCounter
        GCounter object to store positive numbers
    neg : GCounter
        GCounter object to store negative numbers

    Methods
    -------
    inc():
        Increments the pos counter's value by 1.
    dec():
        Increments the neg counter's value by 1.
    query():
        Returns the current value of the counter by subtracting neg from pos.
    compare(pnc2 : PNCounter):
        Compares the value of a given PNCounter with the callers' value.
    merge(pnc2 : PNCounter):
        Merges the state of a given PNCounter with the state of the caller by getting the max of both counter values.
    """

    pos: GCounter = None
    neg: GCounter = None

    def __init__(self):
        self.pos = GCounter()
        self.neg = GCounter()

    def inc(self):
        """
        Increments the pos counter's value by 1.
        :return None:
        """
        self.pos.inc()

    def dec(self):
        """
        Increments the neg counter's value by 1.
        :return None:
        """
        self.neg.inc()

    def query(self):
        """
        Returns the current value of the counter by subtracting neg from pos.
        :return The current value of the counter:
        """
        return self.pos.query() - self.neg.query()

    def compare(self, pnc2: "PNCounter"):
        """
        Compares the value of a given PNCounter with the callers' value.
        :param pnc2 : PNCounter:
        :return True, if caller's value > given counter's value, False otherwise:
        """
        return self.pos.compare(pnc2.pos) and self.neg.compare(pnc2.neg)

    def merge(self, pnc2: "PNCounter"):
        """
        Merges the state of a given PNCounter with the state of the caller by getting the max of both counter values.
        :param pnc2 : PNCounter:
        :return None:
        """
        self.pos.merge(pnc2.pos)
        self.neg.merge(pnc2.neg)

    def __str__(self):
        return f"PNCounter(pos: {str(self.pos)}, neg: {str(self.neg)})"
