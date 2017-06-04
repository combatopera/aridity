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
from .util import OrderedSet, NoSuchPathException, allfunctions
from .functions import getfunctions
from .grammar import loader
from .directives import Directives
import os, collections, sys

lookup = {Text(name): d for name, d in allfunctions(Directives)}

class UnsupportedEntryException(Exception): pass

class NotAPathException(Exception): pass

class NotAResolvableException(Exception): pass

class AbstractContext(object):

    def __init__(self, parent):
        self.resolvables = collections.OrderedDict()
        self.parent = parent

    def __setitem__(self, path, resolvable):
        if not (tuple == type(path) and set(type(name) for name in path) <= set([str])):
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

    def resolved(self, *path):
        n = len(path)
        modpaths = OrderedSet()
        for modpath in self.paths():
            if modpath != path and modpath[:n] == path:
                modpaths.add(modpath[:n + 1])
        try:
            resolvable = self.getresolvable(path)
            found = True
        except NoSuchPathException:
            if not modpaths:
                raise
            found = False
        obj = resolvable.resolve(self) if found else Fork(self)
        for modpath in modpaths:
            obj.modify(modpath[n], self.resolved(*modpath))
        return obj

    def source(self, path):
        with open(path) as f:
            for entry in loader(f.read()):
                self.execute(entry)

    def execute(self, entry):
        n = entry.size()
        if not n:
            return
        for i in range(n):
            if Text('=') == entry.word(i):
                self[tuple(entry.word(k).totext().cat() for k in range(i))] = entry.phrase(i + 1)
                return
        word = entry.word(0)
        try:
            d = lookup.get(word)
        except TypeError:
            d = None
        if d is None:
            raise UnsupportedEntryException(entry)
        d(entry.phrase(1), self)

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
