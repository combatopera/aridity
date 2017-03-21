from .grammar import Function, Text, List, Fork
import os, collections, sys

def screenstr(text):
    return '"%s"' % text.replace('\\', '\\\\').replace('\n', '\\n').replace('"', '\\"')

def scstr(text):
    return '"%s"' % text.replace('\\', '\\\\').replace('\n', '\\n').replace('"', '\\"')

def shstr(text):
    return "'%s'" % text.replace("'", r"'\''")

def mapobjs(context, objs, expr):
    v = []
    for c in objs.resolve(context):
        v.append(expr.resolve(c))
    return List(v)

def join(context, resolvables, separator):
    return Text(separator.resolve(context).cat().join(r.cat() for r in resolvables.resolve(context)))

def get(context, *keys):
    if not keys:
        return context
    for key in keys[:-1]:
        context = context[key.cat()]
    return context.resolved(keys[-1].cat())

class NoSuchPathException(Exception): pass

class SuperContext:

    resolvables = collections.OrderedDict([
        ['get', Function(get)],
        ['str', Function(lambda context, obj: obj.resolve(context).totext())],
        ['~', Text(os.path.expanduser('~'))],
        ['screenstr', Function(lambda context, text: Text(screenstr(text.resolve(context).cat())))],
        ['scstr', Function(lambda context, text: Text(scstr(text.resolve(context).cat())))],
        ['shstr', Function(lambda context, text: Text(shstr(text.cat())))],
        ['env', Function(lambda context, key: Text(os.environ[key.cat()]))],
        ['LF', Text('\n')],
        ['EOL', Text(os.linesep)],
        ['list', Function(lambda context, *objs: List(list(objs)))],
        ['fork', Function(lambda context: Fork(context, collections.OrderedDict()))],
        ['map', Function(mapobjs)],
        ['join', Function(join)],
        ['stdout', Function(sys.stdout.write)],
    ])

    def namesimpl(self, names):
        names.update([name, None] for name in self.resolvables.keys())

    def __getitem__(self, name):
        try:
            return self.resolvables[name]
        except KeyError:
            raise NoSuchPathException(name)

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

    def resolved(self, name):
        prefix = name + '#'
        modnames = collections.OrderedDict()
        for modname in self.names():
            if modname.startswith(prefix):
                nexthash = modname.find('#', len(prefix))
                if -1 == nexthash:
                    nexthash = None
                modnames[modname[:nexthash]] = None
        try:
            resolvable = self[name]
        except NoSuchPathException:
            if not modnames:
                raise
        try:
            obj = resolvable.resolve(self)
        except NameError:
            obj = Fork(self, collections.OrderedDict())
        for modname in modnames:
            obj.modify(modname[len(prefix):], self.resolved(modname))
        return obj
