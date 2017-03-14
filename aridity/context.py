from .grammar import Function, Text, List
import os, collections

def screenstr(text):
    return '"%s"' % text.replace('\\', '\\\\').replace('\n', '\\n').replace('"', '\\"')

def scstr(text):
    return '"%s"' % text.replace('\\', '\\\\').replace('\n', '\\n').replace('"', '\\"')

def shstr(text):
    return "'%s'" % text.replace("'", r"'\''")

class SuperContext:

    resolvables = {
        'get': Function(lambda context, key: context[key.cat()]),
        'str': Function(lambda context, obj: obj.totext()),
        '~': Text(os.path.expanduser('~')),
        'screenstr': Function(lambda context, text: Text(screenstr(text.cat()))),
        'scstr': Function(lambda context, text: Text(scstr(text.cat()))),
        'shstr': Function(lambda context, text: Text(shstr(text.cat()))),
        'env': Function(lambda context, key: Text(os.environ[key.cat()])),
        'LF': Text('\n'),
        'EOL': Text(os.linesep),
        'list': Function(lambda context, *objs: List(list(objs))),
    }

    def namesimpl(self, names):
        names.update([name, None] for name in self.resolvables.keys())

    def __getitem__(self, name):
        return self.resolvables[name]

supercontext = SuperContext()

class Context:

    def __init__(self, parent = supercontext):
        self.resolvables = collections.OrderedDict()
        self.parent = parent

    def __setitem__(self, name, resolvable):
        self.resolvables[name] = resolvable

    def namesimpl(self, names):
        self.parent.namesimpl(names)
        names.update([name, None] for name in self.resolvables.keys())

    def names(self):
        names = collections.OrderedDict()
        self.namesimpl(names)
        return names.keys()

    def __getitem__(self, name):
        try:
            return self.resolvables[name]
        except KeyError:
            return self.parent[name]
