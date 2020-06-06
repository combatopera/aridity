# Copyright 2017, 2020 Andrzej Cichocki

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
from .directives import lookup
from .functions import getfunctions
from .model import CatNotSupportedException, Directive, Function, Resolvable, Scalar, Stream, Text
from .stacks import IndentStack, SimpleStack, ThreadLocalResolvable
from .util import NoSuchPathException, UnsupportedEntryException, OrderedDict
from collections import defaultdict
import os, sys, threading

class NotAPathException(Exception): pass

class NotAResolvableException(Exception): pass

# XXX: Isn't this Resolved rather than Resolvable?
class AbstractContext(Resolvable): # TODO LATER: Some methods should probably be moved to Context.

    def __init__(self, parent):
        self.resolvables = OrderedDict()
        self.parent = parent

    def __setitem__(self, path, resolvable):
        if not (tuple == type(path) and set(type(name) for name in path) <= set([str, type(None)])):
            raise NotAPathException(path)
        if not isinstance(resolvable, Resolvable):
            raise NotAResolvableException(resolvable)
        self.getorcreatesubcontext(path[:-1]).resolvables[path[-1]] = resolvable

    def getorcreatesubcontext(self, path):
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
        return self._resolved(path, self._findresolvable(path), kwargs) if path else self

    def _resolvedcontextornone(self, path):
        c = self # Assume we are resolved.
        for name in path:
            r = c.resolvables.get(name)
            if r is None:
                return
            c = r.resolve(c)
            if not hasattr(c, 'resolvables'):
                return
        return c

    def _subresolvables(self, path):
        c = self._resolvedcontextornone(path)
        return {} if c is None else c.resolvables

    def _selfandparents(self):
        while True:
            yield self
            self = self.parent
            if self is None:
                break

    def _findresolvable(self, path):
        for i in range(len(path)):
            c = self._resolvedcontextornone(path[:i])
            if c is None:
                break
            r = c._findresolvableshallow(path[i:])
            if r is not None:
                return r
        raise NoSuchPathException(path)

    def _findresolvableshallow(self, path):
        for c in self._selfandparents():
            r = c._subresolvables(path[:-1]).get(path[-1])
            if r is not None:
                return r

    def _resolved(self, path, resolvable, kwargs):
        errortocount = defaultdict(lambda: 0)
        for i in range(len(path)):
            obj = self._resolvedshallow(path[i:], resolvable, kwargs, errortocount)
            if obj is not None:
                return obj
        raise NoSuchPathException(path, dict(errortocount)) # TODO: Ugly.

    def _resolvedshallow(self, path, resolvable, kwargs, errortocount):
        while path:
            path = path[:-1]
            for c in (c._resolvedcontextornone(path) for c in self._selfandparents()):
                if c is not None:
                    try:
                        return resolvable.resolve(c, **kwargs)
                    except NoSuchPathException as e:
                        errortocount[str(e)] += 1

    def unravel(self):
        d = OrderedDict([k, o.unravel()] for k, o in self.itero())
        return list(d) if self.islist else d

    def __iter__(self):
        return iter(self.resolvables)

    def staticcontext(self):
        for c in self._selfandparents():
            pass
        return c

    def source(self, prefix, path):
        from .repl import Repl
        with self.staticcontext().here.push(Text(os.path.dirname(path))), Repl(self, rootprefix = prefix) as repl, open(path) as f:
            for line in f:
                repl(line)

    class Enough(Exception): pass

    def execute(self, entry):
        directives = []
        for i, word in enumerate(entry.words()):
            def append(resolvable):
                directives.append((resolvable.directivevalue, i))
                raise self.Enough
            try:
                self.getresolvables(word.cat(), append) # XXX: Can this be retired?
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

    def itero(self):
        for k, r in self.resolvables.items():
            for t in r.resolve(self).spread(k):
                yield t

    def spread(self, k):
        yield k, self

class StaticContext(AbstractContext):

    stacktypes = dict(here = SimpleStack, indent = IndentStack)

    def __init__(self):
        super(StaticContext, self).__init__(None)
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
        self.threadlocals = threading.local()
        for name in self.stacktypes:
            self[name,] = ThreadLocalResolvable(self.threadlocals, name)

    def __getattr__(self, name):
        threadlocals = self.threadlocals
        try:
            return getattr(threadlocals, name)
        except AttributeError:
            stack = self.stacktypes[name](name)
            setattr(threadlocals, name, stack)
            return stack

class Slash(Text, Function):

    def __init__(self):
        Text.__init__(self, os.sep)
        Function.__init__(self, slashfunction)

def slashfunction(context, *resolvables):
    path = None
    for r in reversed(resolvables):
        component = r.resolve(context).cat()
        path = component if path is None else os.path.join(component, path)
        if os.path.isabs(path):
            break
    return Text(os.path.join() if path is None else path)

StaticContext = StaticContext()

class Context(AbstractContext):

    def __init__(self, parent = StaticContext, islist = False):
        super(Context, self).__init__(parent)
        self.islist = islist

    def resolve(self, context): # TODO: Retire * and then this can go.
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
