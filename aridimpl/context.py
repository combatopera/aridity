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

from __future__ import with_statement
from .model import CatNotSupportedException, Directive, Function, Resolvable, Scalar, Stream, Text
from .util import NoSuchPathException, UnsupportedEntryException, OrderedDict
from .functions import getfunctions
from .directives import lookup
from .repl import Repl
import os, sys

class NotAPathException(Exception): pass

class NotAResolvableException(Exception): pass

class AbstractContext(Resolvable): # TODO LATER: Some methods should probably be moved to Context.

    def __init__(self, parent):
        self.resolvables = OrderedDict()
        self.parent = parent

    def __setitem__(self, path, resolvable):
        if not (tuple == type(path) and set(type(name) for name in path) <= set([str, type(None)])):
            raise NotAPathException(path)
        if not isinstance(resolvable, Resolvable):
            raise NotAResolvableException(resolvable)
        self.subcontext(path[:-1]).resolvables[path[-1]] = resolvable

    def subcontext(self, path):
        for name in path:
            that = self.resolvables.get(name)
            if that is None:
                self.resolvables[name] = that = Context(self)
            self = that
        return self

    def getresolvables(self, name, append):
        r = self.resolvables.get(name)
        if r is not None:
            append(r)
        self.parent.getresolvables(name, append)

    def resolved(self, *path, **kwargs):
        if not path:
            return self
        name, tail = path[0], path[1:]
        resolvables = []
        self.getresolvables(name, resolvables.append)
        if not resolvables:
            raise NoSuchPathException(name)
        for i, resolvable in enumerate(resolvables):
            try:
                return resolvable.resolve(self).resolved(*tail, **kwargs) if tail else resolvable.resolve(self, **kwargs)
            except NoSuchPathException:
                if i + 1 == len(resolvables):
                    raise

    def unravel(self):
        d = OrderedDict([k, v.resolve(self).unravel()] for k, v in self.resolvables.items())
        return list(d) if self.islist else d

    def __iter__(self):
        return iter(self.resolvables)

    def temporarily(self, name, resolvable, block): # FIXME: Retire.
        oldornone = self.resolvables.get(name)
        self.resolvables[name] = resolvable
        try:
            return block()
        finally:
            if oldornone is None:
                del self.resolvables[name]
            else:
                self.resolvables[name] = oldornone

    def source(self, prefix, path):
        def block():
            with Repl(self, rootprefix = prefix) as repl:
                with open(path) as f:
                    for line in f:
                        repl(line)
        self.temporarily('here', Text(os.path.dirname(path)), block)

    class Enough(Exception): pass

    def execute(self, entry):
        directives = []
        for i, word in enumerate(entry.words()):
            def append(resolvable):
                directives.append((resolvable.directivevalue, i))
                raise self.Enough
            try:
                self.getresolvables(word.cat(), append)
            except (AttributeError, CatNotSupportedException, self.Enough):
                pass
        if 1 != len(directives):
            raise UnsupportedEntryException("Expected 1 directive but %s found: %s" % (directives, entry))
        d, i = directives[0]
        d(entry.subentry(0, i), entry.phrase(i + 1), self)

    def __str__(self):
        eol = '\n'
        def g():
            c = self
            while True:
                try: d = c.resolvables
                except AttributeError: break
                yield "%s%s" % (type(c).__name__, ''.join("%s\t%s = %r" % (eol, w, r) for w, r in d.items()))
                c = c.parent
        return eol.join(g())

class SuperContext(AbstractContext):

    class EmptyContext:

        def getresolvables(self, name, append):
            pass

    def __init__(self):
        super(SuperContext, self).__init__(self.EmptyContext())
        for word, d in lookup.items():
            self[word.cat(),] = Directive(d)
        for name, f in getfunctions():
            self[name,] = Function(f)
        self['~',] = Text(os.path.expanduser('~'))
        self['LF',] = Text('\n')
        self['EOL',] = Text(os.linesep)
        self['stdout',] = Stream(sys.stdout)
        self['/',] = Slash()
        self['None',] = Scalar(None)

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

    def resolve(self, context):
        c = Context(self.parent, self.islist)
        for name, r in self.resolvables.items():
            if name is not None:
                c.resolvables[name] = r
        defaults = self.resolvables.get(None)
        if defaults is not None:
            for item in c.resolvables:
                for dn, dr in defaults.resolvables.items():
                    if dn not in item.resolvables.keys():
                        item.resolvables[dn] = dr
        return c

    def createchild(self, **kwargs):
        return type(self)(self, **kwargs)

    def tobash(self, toplevel = False):
        if toplevel:
            return ''.join("%s=%s\n" % (name, obj.resolve(self).tobash()) for name, obj in self.resolvables.items())
        elif self.islist:
            return "(%s)" % ' '.join(x.resolve(self).tobash() for x in self)
        else:
            return Text(self.tobash(True)).tobash()

    def tojava(self):
        return Text(''.join("%s %s\n" % (k, v.resolve(self).unravel()) for k, v in self.resolvables.items())) # TODO: Escaping.
