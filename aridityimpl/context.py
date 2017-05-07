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

from .grammar import Function, Text, Fork, Stream, Resolvable
from .util import OrderedSet, NoSuchPathException
from .functions import getfunctions
import os, collections, sys

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

    def resolved(self, path):
        prefix = path + '#'
        prefixlen = len(prefix)
        modpaths = OrderedSet()
        for modpath in self.paths():
            if modpath.startswith(prefix):
                nexthash = modpath.find('#', prefixlen)
                if -1 == nexthash:
                    nexthash = None
                modpaths.add(modpath[:nexthash])
        try:
            resolvable = self.getresolvable(path)
            found = True
        except NoSuchPathException:
            if not modpaths:
                raise
            found = False
        obj = resolvable.resolve(self) if found else Fork(self)
        for modpath in modpaths:
            obj.modify(modpath[prefixlen:], self.resolved(modpath))
        return obj

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
        self['/',] = Text(os.sep)

supercontext = SuperContext()

class Context(AbstractContext):

    def __init__(self, parent = supercontext):
        super(Context, self).__init__(parent)

    def createchild(self):
        return type(self)(self)
