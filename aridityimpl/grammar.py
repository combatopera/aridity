from pyparsing import Forward, OneOrMore, Optional, Or, Regex, Suppress, ZeroOrMore, CharsNotIn, NoMatch
from decimal import Decimal
import re, itertools, os, collections

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

class Boundary(SimpleValue):

    ignorable = True

class Scalar(SimpleValue):

    ignorable = False

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
        args = [a for a in self.args if not a.ignorable]
        for name in reversed(self.name.split('$')):
            args = [context.resolved(name)(*[context] + args)]
        result, = args
        return result

class List(Resolvable):

    def __init__(self, objs):
        self.objs = objs

    def resolve(self, context):
        return self

    def modify(self, name, obj):
        self.objs.append(obj)

    def __iter__(self):
        return iter(self.objs)

class Fork(Struct):

    def __init__(self, parent):
        self.objs = collections.OrderedDict()
        self.parent = parent

    def modify(self, name, obj):
        self.objs[name] = obj

    def __getitem__(self, name):
        return self.objs[name]

    def resolved(self, name):
        try:
            return self.objs[name]
        except KeyError:
            return self.parent.resolved(name)

    def __iter__(self):
        return iter(self.objs.values())

class Function(Resolvable):

    def __init__(self, f):
        self.f = f

    def resolve(self, context):
        return self

    def __call__(self, *args):
        return self.f(*args)

class WriteAndFlush(Resolvable):

    def __init__(self, f):
        self.f = f

    def resolve(self, context):
        return self

    def __call__(self, text):
        self.f.write(text)
        self.f.flush()

class UnsupportedEntryException(Exception): pass

class Entry(Struct):

    @classmethod
    def pa(cls, s, l, t):
        return cls(t.asList())

    def __init__(self, resolvables):
        self.resolvables = resolvables

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

    def execute(self, context):
        def resolvepath(i):
            path = self.phrase(i).resolve(context).cat()
            return path if os.path.isabs(path) else os.path.join(context.resolved('cwd').cat(), path)
        if Text('=') == self.word(1):
            context[self.word(0).cat()] = self.phrase(2)
        elif Text('redirect') == self.word(0):
            context['stdout'] = WriteAndFlush(open(resolvepath(1), 'w'))
        elif Text('echo') == self.word(0):
            template = self.phrase(1).resolve(context).cat()
            context.resolved('stdout')(Concat(templateparser(template)).resolve(context).cat())
        elif Text('cat') == self.word(0):
            with open(resolvepath(1)) as f:
                context.resolved('stdout')(Concat(templateparser(f.read())).resolve(context).cat())
        elif Text('source') == self.word(0):
            with open(resolvepath(1)) as f:
                for entry in loader(f.read()):
                    entry.execute(context)
        elif Text('cd') == self.word(0):
            context['cwd'] = Text(resolvepath(1))
        else:
            raise UnsupportedEntryException(self)

class Parser:

    idregex = '[A-Za-z_](?:[A-Za-z_0-9.#]*[A-Za-z_0-9])?'
    identifier = Regex("%s(?:[$]%s)*" % (idregex, idregex))

    @staticmethod
    def getoptblank(pa, boundarychars):
        return Optional(Regex(r"[^\S%s]+" % re.escape(boundarychars)).leaveWhitespace().setParseAction(pa))

    @staticmethod
    def gettext(pa, boundarychars):
        return Regex(r"[^$\s%s]+" % re.escape(boundarychars)).leaveWhitespace().setParseAction(pa)

    @staticmethod
    def getoptboundary(pa, boundarychars):
        return Optional(Regex("[%s]+" % re.escape(boundarychars)).leaveWhitespace().setParseAction(pa) if boundarychars else NoMatch())

    @classmethod
    def getaction(cls):
        action = Forward()
        def clauses():
            for o, c in '()', '[]':
                yield (Suppress('lit') + Suppress(o) + Optional(CharsNotIn(c)) + Suppress(c)).setParseAction(Text.pa)
                def getbrackets(blankpa, scalarpa):
                    optblank = cls.getoptblank(blankpa, '')
                    return Suppress(o) + ZeroOrMore(optblank + cls.getarg(action, scalarpa, c)) + optblank + Suppress(c)
                yield Suppress('pass') + getbrackets(Text.pa, Text.pa)
                yield (cls.identifier + getbrackets(Blank.pa, AnyScalar.pa)).setParseAction(Call.pa)
        action << Suppress('$').leaveWhitespace() + Or(clauses()).leaveWhitespace()
        return action

    @classmethod
    def getarg(cls, action, scalarpa, boundarychars):
        opttext = Optional(cls.gettext(Text.pa, boundarychars))
        return (OneOrMore(opttext + action) + opttext | cls.gettext(scalarpa, boundarychars)).setParseAction(Concat.pa)

    @classmethod
    def create(cls, scalarpa, boundarychars):
        optboundary = cls.getoptboundary(Boundary.pa, boundarychars)
        optblank = cls.getoptblank(Blank.pa, boundarychars)
        return OneOrMore(optblank + cls.getarg(cls.getaction(), scalarpa, boundarychars)) + optblank + optboundary

    def __init__(self, g):
        self.g = g.parseWithTabs()

    def __call__(self, text):
        return self.g.parseString(text, parseAll = True).asList()

expressionparser = Parser(Parser.create(AnyScalar.pa, '\r\n'))
templateparser = Parser(Parser.create(Text.pa, ''))
loader = Parser(ZeroOrMore(Parser.create(AnyScalar.pa, '\r\n').setParseAction(Entry.pa)))
