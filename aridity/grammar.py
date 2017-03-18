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

    def resolve(self, context):
        raise NotImplementedError

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

class SimpleValue(Resolvable):

    serializable = True

    @classmethod
    def pa(cls, s, l, t):
        value, = t
        return cls(value)

    def __init__(self, value):
        self.value = value

    def resolve(self, context):
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

class Text(Cat, Scalar):

    @classmethod
    def pa(cls, s, l, t):
        text, = t
        return Text(text)

    def resolved(self, name):
        import sys
        return getattr(sys.modules['aridity.context'], 'supercontext')[name]

class Number(Scalar):

    def totext(self):
        return Text(str(self.value)) # XXX: Ideally this would unparse?

class Boolean(Scalar):

    pass

class AnyScalar:

    numberpattern = re.compile('^-?(?:[0-9]+|[0-9]*[.][0-9]+)$')
    booleans = dict([str(x).lower(), Boolean(x)] for x in [True, False])

    @classmethod
    def pa(cls, s, l, t):
        text, = t
        if text in cls.booleans:
            return cls.booleans[text]
        else:
            m = cls.numberpattern.search(text)
            return Text(text) if m is None else Number((Decimal if '.' in text else int)(text))

class Call(Resolvable):

    ignorable = False

    @classmethod
    def pa(cls, s, l, t):
        return cls(t[0], t[1:])

    def __init__(self, name, args):
        self.name = name
        self.args = args

    def resolve(self, context):
        return context.resolved(self.name)(*[context] + [a for a in self.args if not a.ignorable])

class List(Resolvable):

    serializable = True

    def __init__(self, objs):
        self.objs = objs

    def resolve(self, context):
        return self

    def modify(self, name, obj):
        self.objs.append(obj)

    def __iter__(self):
        return iter(self.objs)

class Fork(Struct):

    serializable = True

    def __init__(self, parent, objs):
        self.parent = parent
        self.objs = objs

    def modify(self, name, obj):
        self.objs[name] = obj

    def __getitem__(self, name):
        return self.objs[name]

    def resolved(self, name):
        try:
            return self.objs[name]
        except KeyError:
            return self.parent.resolved(name)

class Function(Resolvable):

    serializable = False

    def __init__(self, f):
        self.f = f

    def resolve(self, context):
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

    identifier = Regex('[A-Za-z_](?:[A-Za-z_0-9.#]*[A-Za-z_0-9])?')

    @staticmethod
    def getoptblank(pa, boundarychars):
        return Optional(Regex(r"[^\S%s]+" % re.escape(boundarychars)).leaveWhitespace().setParseAction(pa))

    @staticmethod
    def gettext(pa, boundarychars):
        return Regex(r"[^$\s%s]+" % re.escape(boundarychars)).leaveWhitespace().setParseAction(pa)

    @classmethod
    def getaction(cls):
        action = Forward()
        def clauses():
            for o, c in '()', '[]':
                yield (Suppress('lit') + Suppress(o) + Optional(CharsNotIn(c)) + Suppress(c)).setParseAction(Text.pa)
                def getarg(scalarpa):
                    optargtext = Optional(cls.gettext(Text.pa, c))
                    return (OneOrMore(optargtext + action) + optargtext | cls.gettext(scalarpa, c)).setParseAction(Concat.pa)
                def getbrackets(blankpa, scalarpa):
                    optblank = cls.getoptblank(blankpa, '')
                    return Suppress(o) + ZeroOrMore(optblank + getarg(scalarpa)) + optblank + Suppress(c)
                yield Suppress('pass') + getbrackets(Text.pa, Text.pa)
                yield (cls.identifier + getbrackets(Blank.pa, AnyScalar.pa)).setParseAction(Call.pa)
        action << Suppress('$').leaveWhitespace() + Or(clauses()).leaveWhitespace()
        return action

    @classmethod
    def getarg(cls, scalarpa, boundarychars):
        opttext = Optional(cls.gettext(Text.pa, boundarychars))
        return OneOrMore(opttext + cls.getaction()) + opttext | cls.gettext(scalarpa, boundarychars)

    @classmethod
    def create(cls, scalarpa, boundarychars):
        optblank = cls.getoptblank(Blank.pa, boundarychars)
        return (ZeroOrMore(optblank + cls.getarg(scalarpa, boundarychars)) + optblank)

    def __init__(self, g):
        self.g = g.parseWithTabs()

    def __call__(self, text):
        return self.g.parseString(text, parseAll = True).asList()

expressionparser = Parser(Parser.create(AnyScalar.pa, '\r\n'))
templateparser = Parser(Parser.create(Text.pa, ''))
loader = Parser(ZeroOrMore((Parser.identifier + Suppress(Regex(r'=\s*')) + expressionparser.g).setParseAction(Entry.pa)))
