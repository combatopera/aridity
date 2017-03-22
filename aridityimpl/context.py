from .grammar import Function, Text, List, Fork, WriteAndFlush
from .util import OrderedSet
import os, collections, sys

def screenstr(context, text):
    text = text.resolve(context).cat()
    return Text('"%s"' % text.replace('\\', '\\\\').replace('\n', '\\n').replace('"', '\\"'))

def scstr(context, text):
    text = text.resolve(context).cat()
    return Text('"%s"' % text.replace('\\', '\\\\').replace('\n', '\\n').replace('"', '\\"'))

def mapobjs(context, objs, *args):
    if 1 == len(args):
        expr, = args
        return List([expr.resolve(c) for c in objs.resolve(context)])
    else:
        name, expr = args
        name = name.resolve(context).cat()
        def g():
            for obj in objs.resolve(context):
                c = Context(context)
                c[name] = obj
                yield expr.resolve(c)
        return List(list(g()))

def join(context, resolvables, separator):
    return Text(separator.resolve(context).cat().join(r.cat() for r in resolvables.resolve(context)))

def get(context, *keys):
    for key in keys:
        context = context.resolved(key.cat())
    return context

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
        ['fork', Function(lambda context: Fork(context))],
        ['map', Function(mapobjs)],
        ['join', Function(join)],
        ['stdout', WriteAndFlush(sys.stdout)],
        ['/', Text(os.sep)],
    ])

    def namesimpl(self, names):
        names.update(self.resolvables.keys())

    def getresolvable(self, name):
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
        names.update(self.resolvables.keys())

    def names(self):
        names = OrderedSet()
        self.namesimpl(names)
        return names

    def getresolvable(self, name):
        try:
            return self.resolvables[name]
        except KeyError:
            return self.parent.getresolvable(name)

    def resolved(self, name):
        prefix = name + '#'
        prefixlen = len(prefix)
        modnames = OrderedSet()
        for modname in self.names():
            if modname.startswith(prefix):
                nexthash = modname.find('#', prefixlen)
                if -1 == nexthash:
                    nexthash = None
                modnames.add(modname[:nexthash])
        try:
            resolvable = self.getresolvable(name)
            found = True
        except NoSuchPathException:
            if not modnames:
                raise
            found = False
        obj = resolvable.resolve(self) if found else Fork(self)
        for modname in modnames:
            obj.modify(modname[prefixlen:], self.resolved(modname))
        return obj
