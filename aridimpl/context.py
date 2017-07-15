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

from .model import Function, Text, Stream, Resolvable, Resolved
from .util import OrderedSet, NoSuchPathException, UnsupportedEntryException, OrderedDict
from .functions import getfunctions
from .directives import lookup
from .repl import Repl
import os, sys

class NotAPathException(Exception): pass

class NotAResolvableException(Exception): pass

class AbstractContext(Resolved): # TODO LATER: Some methods should probably be moved to Context.

    def __init__(self, parent):
        self.resolvables = OrderedDict()
        self.parent = parent

    def __setitem__(self, path, resolvable):
        if not (tuple == type(path) and set(type(name) for name in path) <= set([str, type(None)])):
            raise NotAPathException(path)
        if not isinstance(resolvable, Resolvable):
            raise NotAResolvableException(resolvable)
        for name in path[:-1]:
            that = self.resolvables.get((name,))
            if that is None:
                that = Context(self)
                self.resolvables[name,] = that
            self = that
        self.resolvables[path[-1:]] = resolvable

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
        for name, kwargs in zip(path, [{}] * (len(path) - 1) + [kwargs]):
            self = self.getresolvable((name,)).resolve(self, **kwargs)
        return self

    def unravel(self):
        d = OrderedDict([k[0], v.resolve(self).unravel()] for k, v in self.resolvables.items() if k[0] is not None)
        return list(d) if self.islist else d

    def __iter__(self):
        return iter(self.resolvables)

    def source(self, prefix, path):
        oldhere = self.resolvables.get(('here',))
        self.resolvables['here',] = Text(os.path.dirname(path))
        try:
            with Repl(self, rootprefix = prefix) as repl:
                with open(path) as f:
                    for line in f:
                        repl(line)
        finally:
            if oldhere is None:
                del self.resolvables['here',]
            else:
                self.resolvables['here',] = oldhere

    def execute(self, entry):
        directives = []
        for i, word in enumerate(entry.words()):
            try:
                d = lookup.get(word)
            except TypeError:
                d = None
            if d is not None:
                directives.append((d, i))
        if 1 != len(directives):
            raise UnsupportedEntryException(entry)
        d, i = directives[0]
        d(entry.subentry(0, i), entry.phrase(i + 1), self)

    def __str__(self):
        eol = '\n'
        def g():
            c = self
            while True:
                try: d = c.resolvables
                except AttributeError: break
                yield "%s%s" % (type(c).__name__, ''.join("%s\t%s = %r" % (eol, ' '.join(str(w) for w in path), r) for path, r in d.items()))
                c = c.parent
        return eol.join(g())

    def subcontext(self, path):
        for name in path:
            paths = self.paths()
            self = Context(self)
            for word in None, name:
                for path in paths:
                    if len(path) > 1 and word == path[0]:
                        self[path[1:]] = self.parent.getresolvable(path)
        return self

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

    def __init__(self, parent = supercontext, islist = False):
        super(Context, self).__init__(parent)
        self.islist = islist

    def createchild(self, **kwargs):
        return type(self)(self, **kwargs)
