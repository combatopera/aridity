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

import itertools

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

    def resolve(self, context):
        raise NotImplementedError

class Resolved(Resolvable):

    def resolve(self, context, aslist = False):
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

    def resolve(self, context, aslist = False):
        if aslist:
            return List([part.resolve(context) for part in self.parts if not part.ignorable])
        def g():
            for part in self.parts:
                text = part.resolve(context).cat()
                yield text
                self.monitor(text)
        return Text(''.join(g()))

    def unparse(self):
        return ''.join(part.unparse() for part in self.parts)

# TODO: Always throw when concatenation within a path component is attempted.
class CatNotSupportedException(Exception): pass

class SimpleValue(Resolved):

    @classmethod
    def pa(cls, s, l, t):
        value, = t
        return cls(value)

    def __init__(self, value):
        self.value = value

    def cat(self):
        raise CatNotSupportedException(self)

    def unravel(self):
        return self.value

class Cat:

    def cat(self):
        return self.value

    def unparse(self):
        return self.value

class Blank(Cat, SimpleValue):

    ignorable = True
    boundary = False

class Boundary(SimpleValue):

    ignorable = True
    boundary = True

class Scalar(SimpleValue):

    ignorable = False

    def __hash__(self):
        return hash(self.value)

class Text(Cat, Scalar):

    @classmethod
    def pa(cls, s, l, t):
        text, = t
        return Text(text)

    def totext(self):
        return self

    def tobash(self):
        return "'%s'" % self.value.replace("'", r"'\''")

    def writeout(self, path):
        with open(path, 'w') as f:
            f.write(self.value)

class Binary(Scalar):

    def writeout(self, path):
        with open(path, 'wb') as f:
            f.write(self.value)

class Number(Scalar):

    def totext(self):
        return Text(self.unparse())

    def tobash(self):
        return str(self.value)

    def unparse(self):
        return str(self.value) # FIXME: Should unparse.

    def cat(self):
        return self.unparse()

class Boolean(Scalar):

    def tobash(self, toplevel):
        return 'true' if self.value else 'false'

class Call(Resolvable):

    ignorable = False

    @classmethod
    def pa(cls, s, l, t):
        return cls(t[0], t[2:-1], t[1]+t[-1])

    def __init__(self, name, args, brackets = None):
        self.name = name
        self.args = args
        self.brackets = brackets

    def resolve(self, context, aslist = False):
        args = [a for a in self.args if not a.ignorable]
        for name in reversed(self.name.split('$')):
            args = [context.resolved(name)(*[context] + args)]
        result, = args
        return List([result]) if aslist else result

    def unparse(self):
        return "$%s%s%s%s" % (self.name, self.brackets[0], ''.join(a.unparse() for a in self.args), self.brackets[1])

    def cat(self):
        return self.unparse()

def List(objs):
    from .context import Context
    c = Context(islist = True)
    c.resolvables.update([object(), obj] for obj in objs)
    return c

class Directive(Resolved):

    def __init__(self, directivevalue):
        self.directivevalue = directivevalue

class Function(Resolved):

    def __init__(self, f):
        self.f = f

    def __call__(self, *args):
        return self.f(*args)

    def unravel(self):
        return self.f

class Stream(Resolved):

    def __init__(self, f):
        self.f = f

    def flush(self, text):
        self.f.write(text)
        self.f.flush()

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

    def topath(self, context):
        return tuple((None if self.wildcard == r else r.resolve(context).totext().cat()) for r in self.resolvables if not r.ignorable)

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

    def phrase(self, i):
        return Concat.unlesssingleton(self.subentry(i, self.size()).resolvables)

    def indent(self):
        indent = []
        for r in self.resolvables:
            if not r.ignorable or r.boundary:
                break
            indent.append(r) # XXX: Can we simply grab its value?
        return Concat.unlesssingleton(indent).resolve(None).cat()
