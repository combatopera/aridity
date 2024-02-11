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

from . import directives
from .directives import Precedence
from .functions import getfunctions, OpaqueKey
from .model import CatNotSupportedException, Directive, Function, Resolvable, Scalar, star, Stream, Text
from .stacks import IndentStack, SimpleStack, ThreadLocalResolvable
from .util import CycleException, NoSuchPathException, OrderedDict, solo, TreeNoSuchPathException, UnparseNoSuchPathException, UnsupportedEntryException
import collections, os, sys, threading, unicodedata

class NotAPathException(Exception): pass

class NotAResolvableException(Exception): pass

class Resolvables:

    def _proto(self):
        def allparents():
            scopes = [self.scope]
            while scopes:
                nextscopes = []
                for s in scopes:
                    for p in s.parents:
                        yield s, p
                        nextscopes.append(p)
                scopes = nextscopes
        revpath = []
        for s, parent in allparents():
            try:
                protoc = parent.resolvables.d[Star.protokey]
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
                keyobj = s.label
            except AttributeError:
                break
            revpath.append(keyobj.scalar)
        return {}

    def __init__(self, scope):
        self.d = collections.OrderedDict()
        self.scope = scope

    def put(self, key, resolvable):
        self.d[key] = resolvable

    def getornone(self, key):
        try:
            return self.d[key]
        except KeyError:
            pass
        obj = self._proto().get(key)
        # FIXME LATER: Reads should be thread-safe, only create child if we're about to put something in it.
        return self.scope._putchild(key) if hasattr(obj, 'resolvables') else obj

    def items(self):
        for k, v in self.d.items():
            if Star.protokey != k:
                yield k, v
        for k, v in self._proto().items():
            if Star.protokey != k and k not in self.d:
                yield k, v

# XXX: Isn't this Resolved rather than Resolvable?
class AbstractScope(Resolvable): # TODO LATER: Some methods should probably be moved to Scope.

    nametypes = {str, type(None), OpaqueKey} # XXX: Is None still used by anything?
    try:
        nametypes.add(unicode)
    except NameError:
        pass

    def __init__(self, parents):
        self.resolvables = Resolvables(self)
        self.threadlocals = threading.local()
        self.parents = parents

    def __setitem__(self, path, resolvable):
        # TODO: Interpret non-tuple path as singleton.
        if not (tuple == type(path) and {type(name) for name in path} <= self.nametypes):
            raise NotAPathException(path)
        if not isinstance(resolvable, Resolvable):
            raise NotAResolvableException(resolvable)
        self.getorcreatesubscope(path[:-1]).resolvables.put(path[-1], resolvable)

    def getorcreatesubscope(self, path):
        for name in path:
            that = self.resolvables.getornone(name)
            if that is None:
                that = self._putchild(name)
            self = that
        return self

    def _putchild(self, key):
        child = self.createchild()
        # XXX: Deduce label to allow same Scope in multiple trees?
        child.label = Text(key) # TODO: Not necessarily str.
        self.resolvables.put(key, child)
        return child

    def duplicate(self):
        s = solo(self.parents).createchild()
        for k, v in self.resolvables.items():
            try:
                d = v.duplicate
            except AttributeError:
                pass
            else:
                v = d()
                v.label = Text(k)
            s.resolvables.put(k, v)
        return s

    def resolved(self, *path, **kwargs):
        try:
            resolving = self.threadlocals.resolving
        except AttributeError:
            self.threadlocals.resolving = resolving = set()
        if path in resolving:
            raise CycleException(path)
        resolving.add(path)
        try:
            return self._resolved(path, self._findresolvable(path), kwargs) if path else self
        finally:
            resolving.remove(path)

    def resolvedscopeornone(self, path):
        s = self # Assume we are resolved.
        for name in path:
            r = s.resolvables.getornone(name)
            if r is None:
                return
            s = r.resolve(s)
            if not hasattr(s, 'resolvables'):
                return
        return s

    def _selfandparents(self):
        scopes = [self]
        depth = 0
        while scopes:
            nextscopes = []
            for s in scopes:
                yield depth, s
                nextscopes.extend(s.parents)
            scopes = nextscopes
            depth += 1

    def _scoreresolvables(self, path):
        tail = path[1:]
        for k, s in self._selfandparents():
            r = s.resolvables.getornone(path[0])
            if r is not None:
                if tail:
                    obj = r.resolve(s) # XXX: Wise?
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
        pairs = list(self._scoreresolvables(path))
        try:
            return min(pairs, key = lambda t: t[0])[1]
        except ValueError:
            raise UnparseNoSuchPathException(path)

    def _resolved(self, path, resolvable, kwargs): # TODO: Review this algo.
        errors = []
        for start in range(len(path)):
            for end in range(len(path) - 1, start - 1, -1):
                for s in (s.resolvedscopeornone(path[start:end]) for _, s in self._selfandparents()):
                    if s is not None:
                        try:
                            return resolvable.resolve(s, **kwargs)
                        except NoSuchPathException as e:
                            errors.append(e)
        raise TreeNoSuchPathException(path, errors)

    def unravel(self):
        d = OrderedDict([k, o.unravel()] for k, o in self.resolveditems())
        return list(d) if self.islist or (d and all(OpaqueKey.isopaque(k) for k in d.keys())) else d

    def staticscope(self):
        for _, s in self._selfandparents():
            pass
        return s

    def execute(self, entry, lenient = False):
        directives = []
        precedence = Precedence.void
        for i, wordobj in enumerate(entry.words()):
            try:
                word = wordobj.cat()
                if not word:
                    continue
                initialcategory = _categoryornone(word[0])
                if initialcategory is None or initialcategory[0] not in 'PS':
                    continue
                d = self._findresolvable([word]).directivevalue
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
        def g():
            s = self
            while True:
                yield "%s%s" % (type(s).__name__, ''.join("%s\t%s = %r" % (eol, w, r) for w, r in s.resolvables.items()))
                if not s.parents:
                    break
                s, = s.parents # FIXME: Support multiple parents.
        eol = '\n'
        return eol.join(g())

    def resolveditems(self):
        for k, r in self.resolvables.items():
            for t in r.resolvemulti(k, self):
                yield t

    def createchild(self, **kwargs):
        return Scope([self], **kwargs)

def _categoryornone(c):
    try:
        return unicodedata.category(c)
    except TypeError:
        try:
            u = c.decode('ascii')
        except UnicodeDecodeError:
            return
        return unicodedata.category(u)

class StaticScope(AbstractScope):

    stacktypes = dict(here = SimpleStack, indent = IndentStack)

    def __init__(self):
        super(StaticScope, self).__init__(())
        for word, d in directives.lookup.items():
            self[word.cat(),] = Directive(d)
        for name, f in getfunctions():
            self[name,] = Function(f)
        self['keyring_cron',] = Scalar(False)
        self['keyring_force',] = Scalar(False)
        self['~',] = Text(os.path.expanduser('~'))
        self['LF',] = Text('\n')
        self['EOL',] = Text(os.linesep)
        self['stdout',] = Stream(sys.stdout)
        self['/',] = Slash()
        self['*',] = Star()
        self['None',] = Scalar(None)
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

def slashfunction(scope, *resolvables):
    path = None
    for r in reversed(resolvables):
        component = r.resolve(scope).cat()
        path = component if path is None else os.path.join(component, path)
        if os.path.isabs(path):
            break
    return Text(os.path.join() if path is None else path)

class Star(Function, Directive):

    protokey = object()

    def __init__(self):
        Function.__init__(self, star)
        Directive.__init__(self, self.star)

    def star(self, prefix, suffix, scope):
        scope.getorcreatesubscope(prefix.topath(scope) + (self.protokey,)).execute(suffix)

StaticScope = StaticScope()

class Scope(AbstractScope):

    def __init__(self, parents = None, islist = False):
        super(Scope, self).__init__([StaticScope] if parents is None else parents)
        self.islist = islist

    def resolve(self, scope):
        return self

    def tojava(self):
        return Text(''.join("%s %s\n" % (k, v.resolve(self).unravel()) for k, v in self.resolvables.items())) # TODO: Escaping.

class ScalarScope(Scope):

    def __init__(self, parents, scalarobj):
        super(ScalarScope, self).__init__(parents)
        self.scalarobj = scalarobj

    def __getattr__(self, name):
        return getattr(self.scalarobj, name)
