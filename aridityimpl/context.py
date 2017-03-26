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

class NotANameException(Exception): pass

class NotAResolvableException(Exception): pass

class AbstractContext:

    def __init__(self, parent):
        self.resolvables = collections.OrderedDict()
        self.parent = parent

    def __setitem__(self, name, resolvable):
        if str != type(name):
            raise NotANameException(name)
        if not isinstance(resolvable, Resolvable):
            raise NotAResolvableException(resolvable)
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

class SuperContext(AbstractContext):

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
        self['stdout'] = Stream(sys.stdout)
        self['/'] = Text(os.sep)

supercontext = SuperContext()

class Context(AbstractContext):

    def __init__(self, parent = supercontext):
        super().__init__(parent)

    def createchild(self):
        return type(self)(self)
