class GCounter:
    """
    Simple Grow Only Counter CRDT implementation.

    ...

    Attributes
    ----------
    value : int
        positive integer counter value

    Methods
    -------
    inc():
        Increments the counter's value by 1.
    query() -> int:
        Returns the current value of the counter.
    compare(gc2 : GCounter) -> bool:
        Compares the value of a given GCounter with the callers' value.
    merge(gc2 : GCounter):
        Merges the state of a given GCounter with the state of the caller by getting the max of both counter values.
    """

    value: int = None

    def __init__(self):
        self.value = 0

    def inc(self):
        """
        Increments the counter's value by 1.
        :return None:
        """
        self.value += 1

    def query(self):
        """
        Returns the current value of the counter.
        :return The current value of the counter:
        """
        return self.value

    def compare(self, gc2: "GCounter"):
        """
        Compares the value of a given GCounter with the callers' value.
        :param gc2 : GCounter:
        :return : True, if caller's value > given counter's value, False otherwise:
        """
        return self.value > gc2.value

    def merge(self, gc2: "GCounter"):
        """
        Merges the state of a given GCounter with the state of the caller by getting the max of both counter values.
        :param gc2 : GCounter:
        :return None:
        """
        self.value = max(self.value, gc2.value)

    def __str__(self):
        return f"{self.value}"
