from pyparsing import Forward, OneOrMore, Optional, Or, Regex, Suppress, ZeroOrMore, CharsNotIn
from decimal import Decimal
import re

class Struct:

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

    def resolveimpl(self, context):
        raise NotImplementedError

    def resolve(self, context, name):
        obj = self.resolveimpl(context)
        if name is not None:
            prefix = name + '#'
            for modname in context.names():
                if modname.startswith(prefix):
                    obj.modify(context[modname].resolve(context, modname))
        return obj

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

    def resolveimpl(self, context):
        return Text(''.join(part.resolve(context, None).cat() for part in self.parts))

class CatNotSupportedException(Exception): pass

class SimpleValue(Resolvable):

    serializable = True

    @classmethod
    def pa(cls, s, l, t):
        value, = t
        return cls(value)

    def __init__(self, value):
        self.value = value

    def resolveimpl(self, context):
        return self

    def cat(self):
        raise CatNotSupportedException(self)

class Cat:

    def cat(self):
        return self.value

class Blank(Cat, SimpleValue):

    ignorable = True

class Scalar(SimpleValue):

    ignorable = False
    numberpattern = re.compile('^-?(?:[0-9]+|[0-9]*[.][0-9]+)$')

    @classmethod
    def pa(cls, s, l, t):
        text, = t
        if text in cls.booleans:
            return cls.booleans[text]
        else:
            m = cls.numberpattern.search(text)
            return Text(text) if m is None else Number((Decimal if '.' in text else int)(text))

class Text(Cat, Scalar):

    @classmethod
    def pa(cls, s, l, t): # TODO: Refactor to avoid override.
        text, = t
        return Text(text)

class Number(Scalar):

    def totext(self):
        return Text(str(self.value)) # XXX: Ideally this would unparse?

class Boolean(Scalar):

    pass

Scalar.booleans = dict([str(x).lower(), Boolean(x)] for x in [True, False])

class Call(Resolvable):

    ignorable = False

    @classmethod
    def pa(cls, s, l, t):
        return cls(t[0], t[1:])

    def __init__(self, name, args):
        self.name = name
        self.args = args

    def resolveimpl(self, context):
        return context[self.name](*[context] + [a for a in self.args if not a.ignorable])

class List(Resolvable):

    serializable = True

    def __init__(self, objs):
        self.objs = objs

    def resolveimpl(self, context):
        return self

    def modify(self, obj):
        self.objs.append(obj)

    def __iter__(self):
        return iter(self.objs)

class Function(Resolvable):

    serializable = False

    def __init__(self, f):
        self.f = f

    def resolveimpl(self, context):
        return self

    def __call__(self, *args):
        return self.f(*args)

class Entry(Struct):

    @classmethod
    def pa(cls, s, l, t):
        resolvables = t[1:]
        if resolvables and resolvables[-1].ignorable:
            del resolvables[-1]
        return cls(t[0], resolvables)

    def __init__(self, name, resolvables):
        self.name = name
        self.resolvables = resolvables

class Parser:

    identifier = Regex('[A-Za-z_](?:[A-Za-z_0-9.]*[A-Za-z_0-9])?')

    @classmethod
    def create(cls, boundarycharornone = None):
        def gettext(pa, boundarycharornone):
            boundaryregex = '' if boundarycharornone is None else r"\%s" % boundarycharornone
            return Regex(r"[^$\s%s]+" % boundaryregex).leaveWhitespace().setParseAction(pa)
        action = Forward()
        boundaryregex = '' if boundarycharornone is None else r"\%s" % boundarycharornone
        def getoptblank(pa):
            return Optional(Regex(r"[^\S%s]+" % boundaryregex).leaveWhitespace().setParseAction(pa))
        def clauses():
            for o, c in '()', '[]':
                yield (Suppress('lit') + Suppress(o) + Optional(CharsNotIn(c)) + Suppress(c)).setParseAction(Text.pa)
                optargtext = Optional(gettext(Text.pa, c))
                arg = (OneOrMore(optargtext + action) + optargtext | gettext(Scalar.pa, c)).setParseAction(Concat.pa)
                def getbrackets(pa):
                    optblank = getoptblank(pa)
                    return Suppress(o) + ZeroOrMore(optblank + arg) + optblank + Suppress(c)
                yield Suppress('pass') + getbrackets(Text.pa)
                yield (cls.identifier + getbrackets(Blank.pa)).setParseAction(Call.pa)
        action << Suppress('$').leaveWhitespace() + Or(clauses()).leaveWhitespace()
        opttext = Optional(gettext(Text.pa, boundarycharornone))
        chunk = OneOrMore(opttext + action) + opttext | gettext(Scalar.pa, boundarycharornone)
        optblank = getoptblank(Blank.pa)
        return (ZeroOrMore(optblank + chunk) + optblank).parseWithTabs()

    def __init__(self, g):
        self.g = g

    def __call__(self, text):
        return self.g.parseString(text, parseAll = True).asList()

parser = Parser(Parser.create())
loader = Parser(ZeroOrMore((Parser.identifier + Suppress(Regex(r'=\s*')) + Parser.create('\n')).setParseAction(Entry.pa)))
