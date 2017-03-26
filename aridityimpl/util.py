import collections, inspect

class NoSuchPathException(Exception): pass

class OrderedSet:

    def __init__(self):
        self.d = collections.OrderedDict()

    def add(self, x):
        self.d[x] = None

    def update(self, g):
        for x in g:
            self.add(x)

    def __iter__(self):
        return iter(self.d.keys())

    def __bool__(self):
        return bool(self.d)

def allfunctions(clazz):
    for name, f in inspect.getmembers(clazz, predicate = inspect.isfunction):
        if name.endswith('_'):
            name = name[:-1]
        yield name, f
