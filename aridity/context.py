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
from .directives import lookup, Precedence
from .functions import getfunctions
from .model import CatNotSupportedException, Directive, Function, Resolvable, Scalar, Stream, Text
from .stacks import IndentStack, SimpleStack, ThreadLocalResolvable
from .util import NoSuchPathException, OrderedDict, TreeNoSuchPathException, UnparseNoSuchPathException, UnsupportedEntryException
import collections, os, sys, threading

class NotAPathException(Exception): pass

class NotAResolvableException(Exception): pass

class Resolvables:

    def _proto(self):
        revpath = []
        c = self.context
        while c.parent is not None:
            try:
                protoc = c.parent.resolvables.d[Star.protokey]
            except KeyError:
                pass
            else:
                try:
                    for component in reversed(revpath):
                        protoc = protoc.resolvables.d[component]
                except KeyError:
                    break
                return protoc.resolvables.d
            try:
                keyobj = c.label
            except AttributeError:
                break
            revpath.append(keyobj.value)
            c = c.parent
        return {}

    def __init__(self, context):
        self.d = collections.OrderedDict()
        self.context = context

    def put(self, key, resolvable):
        self.d[key] = resolvable

    def getornone(self, key):
        try:
            return self.d[key]
        except KeyError:
            pass
        obj = self._proto().get(key)
        # FIXME LATER: Reads should be thread-safe, only create child if we're about to put something in it.
        return self.context._putchild(key) if hasattr(obj, 'resolvables') else obj

    def items(self):
        for k, v in self.d.items():
            if Star.protokey != k:
                yield k, v
        for k, v in self._proto().items():
            if Star.protokey != k and k not in self.d:
                yield k, v

# XXX: Isn't this Resolved rather than Resolvable?
class AbstractContext(Resolvable): # TODO LATER: Some methods should probably be moved to Context.

    def __init__(self, parent):
        self.resolvables = Resolvables(self)
        self.parent = parent

    def __setitem__(self, path, resolvable):
        if not (tuple == type(path) and set(type(name) for name in path) <= set([str, type(None)])):
            raise NotAPathException(path)
        if not isinstance(resolvable, Resolvable):
            raise NotAResolvableException(resolvable)
        self.getorcreatesubcontext(path[:-1]).resolvables.put(path[-1], resolvable)

    def getorcreatesubcontext(self, path):
        for name in path:
            that = self.resolvables.getornone(name)
            if that is None:
                that = self._putchild(name)
            self = that
        return self

    def _putchild(self, key):
        child = self.createchild()
        child.label = Text(key) # TODO: Not necessarily str.
        self.resolvables.put(key, child)
        return child

    def resolved(self, *path, **kwargs):
        return self._resolved(path, self._findresolvable(path), kwargs) if path else self

    def _resolvedcontextornone(self, path):
        c = self # Assume we are resolved.
        for name in path:
            r = c.resolvables.getornone(name)
            if r is None:
                return
            c = r.resolve(c)
            if not hasattr(c, 'resolvables'):
                return
        return c

    def _selfandparents(self):
        while True:
            yield self
            self = self.parent
            if self is None:
                break

    def _scoreresolvables(self, path):
        tail = path[1:]
        for k, c in enumerate(self._selfandparents()):
            r = c.resolvables.getornone(path[0])
            if r is not None:
                if tail:
                    obj = r.resolve(c) # XXX: Wise?
                    try:
                        obj_score = obj._scoreresolvables
                    except AttributeError:
                        pass
                    else:
                        for score, rr in obj_score(tail):
                            yield score + [k], rr
                else:
                    yield [k], r

    def _findresolvable(self, path):
        bestscore = [float('inf')]
        for score, resolvable in self._scoreresolvables(path):
            if score < bestscore:
                bestscore = score
                bestresolvable = resolvable
        try:
            return bestresolvable
        except NameError:
            raise UnparseNoSuchPathException(path)

    def _resolved(self, path, resolvable, kwargs):
        errors = []
        for i in range(len(path)):
            obj = self._resolvedshallow(path[i:], resolvable, kwargs, errors)
            if obj is not None:
                return obj
        raise TreeNoSuchPathException(path, errors)

    def _resolvedshallow(self, path, resolvable, kwargs, errors):
        while path:
            path = path[:-1]
            for c in (c._resolvedcontextornone(path) for c in self._selfandparents()):
                if c is not None:
                    try:
                        return resolvable.resolve(c, **kwargs)
                    except NoSuchPathException as e:
                        errors.append(e)

    def unravel(self):
        d = OrderedDict([k, o.unravel()] for k, o in self.itero())
        return list(d) if self.islist else d

    def staticcontext(self):
        for c in self._selfandparents():
            pass
        return c

    def source(self, prefix, path):
        with self.staticcontext().here.push(Text(os.path.dirname(path))), open(path) as f:
            self.sourceimpl(prefix, f)

    def sourceimpl(self, prefix, f):
        from .repl import Repl
        with Repl(self, rootprefix = prefix) as repl:
            for line in f:
                repl(line)

    def execute(self, entry, lenient = False):
        directives = []
        precedence = Precedence.void
        for i, word in enumerate(entry.words()):
            try:
                d = self._findresolvable([word.cat()]).directivevalue
                p = Precedence.ofdirective(d)
                if p > precedence:
                    del directives[:]
                    precedence = p
                directives.append((d, i))
            except (AttributeError, CatNotSupportedException, NoSuchPathException):
                pass
        if directives:
            d, i = directives[0] # XXX: Always use first?
            d(entry.subentry(0, i), entry.subentry(i + 1, entry.size()), self)
        elif not lenient:
            raise UnsupportedEntryException("Expected at least one directive: %s" % entry)

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
        self['*',] = Star()
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

class Star(Function, Directive):

    protokey = object()

    def __init__(self):
        def spread(context, resolvable):
            from .functions import Spread
            return Spread(resolvable.resolve(context))
        Function.__init__(self, spread)
        Directive.__init__(self, self.star)

    def star(self, prefix, suffix, context):
        context.getorcreatesubcontext(prefix.topath(context) + (self.protokey,)).execute(suffix)

StaticContext = StaticContext()

class Context(AbstractContext):

    def __init__(self, parent = StaticContext, islist = False):
        super(Context, self).__init__(parent)
        self.islist = islist

    def resolve(self, context):
        return self

    def createchild(self, **kwargs):
        return type(self)(self, **kwargs)

    def tobash(self, toplevel = False):
        if toplevel:
            return ''.join("%s=%s\n" % (name, obj.resolve(self).tobash()) for name, obj in self.resolvables.items())
        elif self.islist:
            return "(%s)" % ' '.join(x.resolve(self).tobash() for _, x in self.resolvables.items())
        else:
            return Text(self.tobash(True)).tobash()

    def tojava(self):
        return Text(''.join("%s %s\n" % (k, v.resolve(self).unravel()) for k, v in self.resolvables.items())) # TODO: Escaping.
