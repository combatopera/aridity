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

import itertools, numbers, os

class Struct(object):

    def __eq__(self, that):
        if type(self) != type(that):
            return False
        if self.__dict__.keys() != that.__dict__.keys():
            return False
        for k, v in self.__dict__.items():
            if v != that.__dict__[k]:
                return False
        return True

    def __repr__(self):
        t = type(self)
        init = t.__init__.__code__
        args = ', '.join(repr(getattr(self, name)) for name in init.co_varnames[1:init.co_argcount])
        return "%s(%s)" % (t.__name__, args)

class Resolvable(Struct):

    def resolve(self, scope):
        raise NotImplementedError

class Resolved(Resolvable):

    def resolve(self, scope, aslist = False):
        return List([self]) if aslist else self

    def spread(self, k): # TODO: Probably makes more sense on SimpleValue, which more things should extend.
        yield k, self

class Concat(Resolvable):

    ignorable = False

    @classmethod
    def strictpa(cls, s, l, t):
        return cls(t[1:-1])

    @classmethod
    def smartpa(cls, s, l, t):
        return cls.unlesssingleton(t.asList())

    @classmethod
    def unlesssingleton(cls, v):
        return v[0] if 1 == len(v) else cls(v)

    def __init__(self, parts, monitor = lambda text: None):
        self.parts = parts
        self.monitor = monitor

    def resolve(self, scope, aslist = False):
        if aslist:
            return List([part.resolve(scope) for part in self.parts if not part.ignorable])
        def g():
            for part in self.parts:
                text = part.resolve(scope).cat()
                yield text
                self.monitor(text)
        return Text(''.join(g()))

    def unparse(self):
        return ''.join(part.unparse() for part in self.parts)

# TODO: Always throw when concatenation within a path component is attempted.
class CatNotSupportedException(Exception): pass

class BaseSimpleValue(Resolved):

    @classmethod
    def pa(cls, s, l, t):
        value, = t
        return cls(value)

    def cat(self):
        raise CatNotSupportedException(self)

    def unravel(self):
        return self.scalar

class SimpleValue(BaseSimpleValue):

    def __init__(self, scalar):
        self.scalar = scalar

class Cat:

    def cat(self):
        return self.scalar

    def unparse(self):
        return self.scalar

class Blank(Cat, SimpleValue):

    ignorable = True
    boundary = False

class Boundary(SimpleValue):

    ignorable = True
    boundary = True

class BaseScalar(BaseSimpleValue):

    ignorable = False

    def __hash__(self):
        return hash(self.scalar)

class Scalar(BaseScalar):

    def __init__(self, scalar):
        self.scalar = scalar

class Text(Cat, BaseScalar):

    @classmethod
    def _of(cls, textvalue):
        return cls(textvalue)

    @property
    def scalar(self):
        return self.textvalue

    def __init__(self, textvalue):
        self.textvalue = textvalue

    def totext(self):
        return self

    def tobash(self):
        return "'%s'" % self.textvalue.replace("'", r"'\''")

    def writeout(self, path):
        with open(path, 'w') as f:
            f.write(self.textvalue)

    def slash(self, words, rstrip):
        return self._of(os.path.join(os.path.dirname(self.textvalue) if rstrip else self.textvalue, *words))

    def pathvalue(self, scope):
        return self.textvalue if os.path.isabs(self.textvalue) else os.path.join(scope.resolved('cwd').cat(), self.textvalue)

    def source(self, scope, prefix):
        if os.path.isabs(self.textvalue):
            scope.source(prefix, self.textvalue)
        else:
            scope.resolved('cwd').slash([self.textvalue], False).source(scope, prefix)

class Binary(BaseScalar):

    @property
    def scalar(self):
        return self.binaryvalue

    def __init__(self, binaryvalue):
        self.binaryvalue = binaryvalue

    def writeout(self, path):
        with open(path, 'wb') as f:
            f.write(self.binaryvalue)

class Number(BaseScalar):

    @property
    def scalar(self):
        return self.numbervalue

    def __init__(self, numbervalue):
        self.numbervalue = numbervalue

    def totext(self):
        return Text(self.unparse())

    def tobash(self):
        return str(self.numbervalue)

    def unparse(self):
        return str(self.numbervalue) # FIXME: Should unparse.

    def cat(self):
        return self.unparse()

class Boolean(BaseScalar):

    @property
    def scalar(self):
        return self.booleanvalue

    def __init__(self, booleanvalue):
        self.booleanvalue = booleanvalue

    def truth(self):
        return self.booleanvalue

    def tobash(self, toplevel):
        return 'true' if self.booleanvalue else 'false'

class Call(Resolvable):

    ignorable = False

    @classmethod
    def pa(cls, s, l, t):
        return cls(t[0], t[2:-1], t[1]+t[-1])

    def __init__(self, name, args, brackets = None):
        self.name = name
        self.args = args
        self.brackets = brackets

    def resolve(self, scope, aslist = False):
        args = [a for a in self.args if not a.ignorable]
        for name in reversed(self.name.split('$')):
            args = [scope.resolved(name)(*[scope] + args)]
        result, = args
        return List([result]) if aslist else result

    def unparse(self):
        return "$%s%s%s%s" % (self.name, self.brackets[0], ''.join(a.unparse() for a in self.args), self.brackets[1])

    def cat(self):
        return self.unparse()

def List(objs):
    from .scope import Scope
    s = Scope(islist = True)
    for obj in objs:
        s.resolvables.put(object(), obj)
    return s

class Directive(Resolved):

    @property
    def scalar(self):
        return self.directivevalue

    def __init__(self, directivevalue):
        self.directivevalue = directivevalue

class Function(Resolved):

    @property
    def scalar(self):
        return self.functionvalue

    def __init__(self, functionvalue):
        self.functionvalue = functionvalue

    def __call__(self, *args):
        return self.functionvalue(*args)

    def unravel(self):
        return self.functionvalue

class Stream(Resolved):

    @property
    def scalar(self):
        return self.streamvalue

    def __init__(self, streamvalue):
        self.streamvalue = streamvalue

    def flush(self, text):
        self.streamvalue.write(text)
        self.streamvalue.flush()

class Entry(Struct):

    wildcard = Text('*')

    @classmethod
    def pa(cls, s, l, t):
        return cls(t.asList())

    def __init__(self, resolvables):
        self.resolvables = resolvables

    def size(self):
        return sum(1 for r in self.resolvables if not r.ignorable)

    def resolve(self):
        return List([r.resolve(None) for r in self.resolvables])

    def word(self, i):
        word, = itertools.islice((r for r in self.resolvables if not r.ignorable), i, i + 1)
        return word

    def words(self):
        return [r for r in self.resolvables if not r.ignorable]

    def topath(self, scope):
        return tuple((None if self.wildcard == r else r.resolve(scope).totext().cat()) for r in self.resolvables if not r.ignorable)

    def subentry(self, i, j):
        v = list(self.resolvables)
        def trim(end):
            while v and v[end].ignorable:
                del v[end]
        n = self.size()
        while j < n:
            trim(-1)
            del v[-1]
            j += 1
        while i:
            trim(0)
            del v[0]
            i -= 1
        for end in 0, -1:
            trim(end)
        return Entry(v)

    def tophrase(self):
        return Concat.unlesssingleton(self.resolvables)

    def indent(self):
        indent = []
        for r in self.resolvables:
            if not r.ignorable or r.boundary:
                break
            indent.append(r) # XXX: Can we simply grab its value?
        return Concat.unlesssingleton(indent).resolve(None).cat()

def wrap(value):
    for b in map(bool, range(2)):
        if value is b:
            return Boolean(value)
    if isinstance(value, numbers.Number):
        return Number(value)
    if callable(value):
        return Function(value)
    if hasattr(value, 'encode'):
        return Text(value)
    return Scalar(value) # XXX: Interpret mappings and sequences?
