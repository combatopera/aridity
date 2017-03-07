from .grammar import Function

class SuperContext:

    resolvables = {
        'get': Function(lambda context, key: context[key.cat()]),
    }

    def __getitem__(self, name):
        return self.resolvables[name]

supercontext = SuperContext()

class Context:

    def __init__(self, parent = supercontext):
        self.resolvables = {}
        self.parent = parent

    def __setitem__(self, name, resolvable):
        self.resolvables[name] = resolvable

    def __getitem__(self, name):
        try:
            return self.resolvables[name]
        except KeyError:
            return self.parent[name]
