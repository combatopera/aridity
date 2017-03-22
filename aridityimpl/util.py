import collections

class OrderedSet:

    def __init__(self):
        self.d = collections.OrderedDict()

    def add(self, x):
        self.d[x] = None

    def __iter__(self):
        return iter(self.d.keys())

    def __bool__(self):
        return bool(self.d)
