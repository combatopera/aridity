from .grammar import Function, Text, Fork, WriteAndFlush, Resolvable
from .util import OrderedSet
from .functions import getfunctions
import os, collections, sys

class NoSuchPathException(Exception): pass

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

    def createchild(self):
        return type(self)(self)

class SuperContext(Context):

    class EmptyContext:

        def namesimpl(self, names):
            pass

        def getresolvable(self, name):
            raise NoSuchPathException(name)

    def __init__(self):
        super().__init__(self.EmptyContext())
        for name, f in getfunctions():
            self[name] = Function(f)
        self['~'] = Text(os.path.expanduser('~'))
        self['LF'] = Text('\n')
        self['EOL'] = Text(os.linesep)
        self['stdout'] = WriteAndFlush(sys.stdout)
        self['/'] = Text(os.sep)

supercontext = SuperContext()
