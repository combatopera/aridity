from .grammar import Function, Text
import os

class SuperContext:

    resolvables = {
        'get': Function(lambda context, key: context[key.cat()]),
        'str': Function(lambda context, obj: obj.totext()),
        '~': Text(os.path.expanduser('~')),
    }

    def namesimpl(self, names):
        names.update(self.resolvables.keys())

    def __getitem__(self, name):
        return self.resolvables[name]

supercontext = SuperContext()

class Context:

    def __init__(self, parent = supercontext):
        self.resolvables = {}
        self.parent = parent

    def __setitem__(self, name, resolvable):
        self.resolvables[name] = resolvable

    def namesimpl(self, names):
        self.parent.namesimpl(names)
        names.update(self.resolvables.keys())

    def names(self):
        names = set()
        self.namesimpl(names)
        return names

    def __getitem__(self, name):
        try:
            return self.resolvables[name]
        except KeyError:
            return self.parent[name]
