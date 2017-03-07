from .grammar import Function

class SuperContext:

    @staticmethod
    def get(context, key):
        return context[key.cat()]

    def __getitem__(self, name):
        return Function(getattr(self, name))

supercontext = SuperContext()

class Context:

    def __init__(self, parent = supercontext):
        self.values = {}
        self.parent = parent

    def __setitem__(self, name, value):
        self.values[name] = value

    def __getitem__(self, name):
        try:
            return self.values[name]
        except KeyError:
            return self.parent[name]
