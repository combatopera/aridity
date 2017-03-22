from .grammar import Function, Text, List, Fork, WriteAndFlush
import os, collections, sys

def screenstr(context, text):
    text = text.resolve(context).cat()
    return Text('"%s"' % text.replace('\\', '\\\\').replace('\n', '\\n').replace('"', '\\"'))

def scstr(context, text):
    text = text.resolve(context).cat()
    return Text('"%s"' % text.replace('\\', '\\\\').replace('\n', '\\n').replace('"', '\\"'))

def mapobjs(context, objs, expr):
    return List([expr.resolve(c) for c in objs.resolve(context)])

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
        ['screenstr', Function(screenstr)],
        ['scstr', Function(scstr)],
        ['LF', Text('\n')],
        ['EOL', Text(os.linesep)],
        ['list', Function(lambda context, *objs: List(list(objs)))],
        ['fork', Function(lambda context: Fork(context, collections.OrderedDict()))],
        ['map', Function(mapobjs)],
        ['join', Function(join)],
        ['stdout', WriteAndFlush(sys.stdout)],
        ['/', Text(os.sep)],
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
