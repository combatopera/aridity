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

import itertools, collections

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

    def resolve(self, context):
        return self

class Concat(Resolvable):

    ignorable = False

    @classmethod
    def pa(cls, s, l, t):
        return cls.unlesssingleton(t.asList())

    @classmethod
    def unlesssingleton(cls, v):
        return v[0] if 1 == len(v) else cls(v)

    def __init__(self, parts):
        self.parts = parts

    def resolve(self, context):
        return Text(''.join(part.resolve(context).cat() for part in self.parts))

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

class Blank(Cat, SimpleValue):

    ignorable = True

class Boundary(SimpleValue):

    ignorable = True

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

class Number(Scalar):

    def totext(self):
        return Text(str(self.value)) # XXX: Ideally this would unparse?

class Boolean(Scalar):

    pass

class Call(Resolvable):

    ignorable = False

    @classmethod
    def pa(cls, s, l, t):
        return cls(t[0], t[1:])

    def __init__(self, name, args):
        self.name = name
        self.args = args

    def resolve(self, context):
        args = [a for a in self.args if not a.ignorable]
        for name in reversed(self.name.split('$')):
            args = [context.resolved(name)(*[context] + args)]
        result, = args
        return result

class List(Resolved):

    def __init__(self, objs):
        self.objs = objs

    def modify(self, name, obj):
        self.objs.append(obj)

    def __iter__(self):
        return iter(self.objs)

    def unravel(self):
        return list(x.unravel() for x in self)

class Fork(Resolved):

    def __init__(self, parent):
        self.objs = collections.OrderedDict()
        self.parent = parent

    def modify(self, name, obj):
        self.objs[name] = obj

    def __getitem__(self, name):
        return self.objs[name]

    def getresolvable(self, name):
        try:
            return self.objs[name]
        except KeyError:
            return self.parent.getresolvable(name)

    def resolved(self, *path):
        return self.getresolvable(path).resolve(self)

    def __iter__(self):
        return iter(self.objs.values())

    def createchild(self):
        return type(self)(self)

    def __setitem__(self, name, obj):
        self.objs[name] = obj

    def unravel(self):
        # XXX: Add ancestor items?
        return collections.OrderedDict([k, v.unravel()] for k, v in self.objs.items())

class Function(Resolved):

    def __init__(self, f):
        self.f = f

    def __call__(self, *args):
        return self.f(*args)

class Stream(Resolved):

    def __init__(self, f):
        self.f = f

    def flush(self, text):
        self.f.write(text)
        self.f.flush()

class Entry(Struct):

    @classmethod
    def pa(cls, s, l, t):
        return cls(t.asList())

    def __init__(self, resolvables):
        self.resolvables = resolvables

    def size(self):
        return sum(1 for r in self.resolvables if not r.ignorable)

    def word(self, i):
        word, = itertools.islice((r for r in self.resolvables if not r.ignorable), i, i + 1)
        return word

    def phrase(self, i):
        phrase = list(self.resolvables)
        def trim(end):
            while phrase and phrase[end].ignorable:
                del phrase[end]
        while i:
            trim(0)
            del phrase[0]
            i -= 1
        for end in 0, -1:
            trim(end)
        return Concat.unlesssingleton(phrase)
