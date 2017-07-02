# Copyright 2017 Andrzej Cichocki

# This file is part of aridity.
#
# aridity is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# aridity is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with aridity.  If not, see <http://www.gnu.org/licenses/>.

from .model import Function, Text, Fork, Stream, Resolvable
from .util import OrderedSet, NoSuchPathException, UnsupportedEntryException, OrderedDict
from .functions import getfunctions
from .directives import lookup
from .repl import Repl
import os, sys, itertools

class NotAPathException(Exception): pass

class NotAResolvableException(Exception): pass

class AbstractContext(object): # TODO LATER: Some methods should probably be moved to Context.

    def __init__(self, parent):
        self.resolvables = OrderedDict()
        self.parent = parent

    def __setitem__(self, path, resolvable):
        if not (tuple == type(path) and set(type(name) for name in path) <= set([str, type(None)])):
            raise NotAPathException(path)
        if not isinstance(resolvable, Resolvable):
            raise NotAResolvableException(resolvable)
        self.resolvables[path] = resolvable

    def pathsimpl(self, paths):
        self.parent.pathsimpl(paths)
        paths.update(self.resolvables.keys())

    def paths(self):
        paths = OrderedSet()
        self.pathsimpl(paths)
        return paths

    def getresolvable(self, path):
        try:
            return self.resolvables[path]
        except KeyError:
            return self.parent.getresolvable(path)

    def resolved(self, *path, **kwargs):
        n = len(path)
        modpaths = OrderedSet()
        for modpath in self.paths():
            try: star = modpath.index(None)
            except: star = -1
            if -1 == star:
                if modpath != path and modpath[:n] == path:
                    modpaths.add(modpath[:n + 1])
            elif star < n:
                path2 = tuple((x if i != star else None) for i, x in enumerate(path))
                if modpath != path2 and modpath[:n] == path2:
                    modpaths.add(modpath[:n + 1])
        try:
            resolvable = self.getresolvable(path)
            found = True
        except NoSuchPathException:
            if not modpaths:
                if len(path) > 1:
                    return self.resolved(*path[:-1]).resolved(path[-1], **kwargs)
                raise
            found = False
        obj = resolvable.resolve(self, **kwargs) if found else Fork(self)
        try:
            modify = obj.modify
        except AttributeError:
            return obj
        modcontext = ModContext.create(self, path)
        for modpath in modpaths:
            modify(modpath[n], modcontext.resolved(*modpath))
        return obj

    def source(self, path):
        with Repl(self) as repl:
            with open(path) as f:
                for line in f:
                    repl(line)

    def execute(self, entry):
        n = entry.size()
        if not n:
            return
        # TODO: Blow up if multiple directives found.
        for i in range(n):
            if Text('=') == entry.word(i):
                self[tuple(entry.word(k).resolve(self).totext().cat() for k in range(i))] = entry.phrase(i + 1)
                return
            if Text('+=') == entry.word(i):
                r = itertools.chain(range(i), [i + 1])
                self[tuple(entry.word(k).resolve(self).totext().cat() for k in r)] = entry.phrase(i + 1)
                return
            if Text('*') == entry.word(i):
                for j in range(i + 1, n):
                    if Text('=') == entry.word(j):
                        break
                else:
                    # XXX: Also support += and other directives?
                    raise Exception('Expected equals in same entry after star.')
                # TODO LATER: Support multiple stars in entry.
                t1 = tuple(entry.word(k).resolve(self).totext().cat() for k in range(i))
                t2 = tuple(entry.word(k).resolve(self).totext().cat() for k in range(i + 1, j))
                self[t1 + (None,) + t2] = entry.phrase(j + 1)
                return
        word = entry.word(0)
        try:
            d = lookup.get(word)
        except TypeError:
            d = None
        if d is None:
            raise UnsupportedEntryException(entry)
        d(entry.phrase(1), self)

    def __str__(self):
        eol = '\n'
        def g():
            c = self
            while True:
                try: d = c.resolvables
                except AttributeError: break
                yield "%s%s" % (type(c).__name__, ''.join("%s\t%s = %s" % (eol, ' '.join(path), r) for path, r in d.items()))
                c = c.parent
        return eol.join(g())

class ModContext(AbstractContext):

    @classmethod
    def create(cls, context, path):
        for name in path:
            context = cls(context, (name,))
        return context

    def __init__(self, parent, contextpath):
        super(ModContext, self).__init__(parent)
        k = len(contextpath)
        for path in parent.paths():
            if len(path) > k and contextpath == path[:k]:
                self[path[k:]] = parent.getresolvable(path)

class SuperContext(AbstractContext):

    class EmptyContext:

        def pathsimpl(self, paths):
            pass

        def getresolvable(self, path):
            raise NoSuchPathException(path)

    def __init__(self):
        super(SuperContext, self).__init__(self.EmptyContext())
        for name, f in getfunctions():
            self[name,] = Function(f)
        self['~',] = Text(os.path.expanduser('~'))
        self['LF',] = Text('\n')
        self['EOL',] = Text(os.linesep)
        self['stdout',] = Stream(sys.stdout)
        self['/',] = Slash()

class Slash(Text, Function):

    def __init__(self):
        Text.__init__(self, os.sep)
        Function.__init__(self, slashfunction)

def slashfunction(context, *resolvables):
    return Text(os.path.join(*(r.resolve(context).cat() for r in resolvables)))

supercontext = SuperContext()

class Context(AbstractContext):

    def __init__(self, parent = supercontext):
        super(Context, self).__init__(parent)

    def createchild(self):
        return type(self)(self)
