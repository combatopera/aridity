from .grammar import Function, Text, List, Fork, WriteAndFlush, Resolvable
from .util import OrderedSet
import os, collections, sys

def screenstr(context, text):
    text = text.resolve(context).cat()
    return Text('"%s"' % text.replace('\\', '\\\\').replace('\n', '\\n').replace('"', '\\"'))

def scstr(context, text):
    text = text.resolve(context).cat()
    return Text('"%s"' % text.replace('\\', '\\\\').replace('\n', '\\n').replace('"', '\\"'))

def pystr(context, text):
    return Text(repr(text.resolve(context).cat()))

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

def join(context, resolvables, *args):
    if args:
        separator, = args
    else:
        separator = Text('')
    return Text(separator.resolve(context).cat().join(r.cat() for r in resolvables.resolve(context)))

def get(context, *keys):
    for key in keys:
        context = context.resolved(key.cat())
    return context

class NoSuchPathException(Exception): pass

class EmptyContext:

    def namesimpl(self, names):
        pass

    def getresolvable(self, name):
        raise NoSuchPathException(name)

class NotStringException(Exception): pass

class NotResolvableException(Exception): pass

class Context:

    def __init__(self, parent = None):
        self.resolvables = collections.OrderedDict()
        self.parent = supercontext if parent is None else parent

    def __setitem__(self, name, resolvable):
        if str != type(name):
            raise NotStringException(name)
        if not isinstance(resolvable, Resolvable):
            raise NotResolvableException(resolvable)
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

class SuperContext(Context):

    def __init__(self):
        super().__init__(EmptyContext())
        self['get'] = Function(get)
        self['str'] = Function(lambda context, obj: obj.resolve(context).totext())
        self['~'] = Text(os.path.expanduser('~'))
        self['screenstr'] = Function(screenstr)
        self['scstr'] = Function(scstr)
        self['pystr'] = Function(pystr)
        self['LF'] = Text('\n')
        self['EOL'] = Text(os.linesep)
        self['list'] = Function(lambda context, *objs: List(list(objs)))
        self['fork'] = Function(lambda context: Fork(context))
        self['map'] = Function(mapobjs)
        self['join'] = Function(join)
        self['stdout'] = WriteAndFlush(sys.stdout)
        self['/'] = Text(os.sep)

supercontext = SuperContext()
