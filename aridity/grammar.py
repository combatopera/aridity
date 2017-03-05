from pyparsing import Empty, Forward, OneOrMore, Optional, Or, Regex, Suppress, White, ZeroOrMore
from decimal import Decimal
import re

class Concat:

    ignorable = False

    @classmethod
    def pa(cls, s, l, t):
        parts = t.asList()
        return parts[0] if 1 == len(parts) else cls(parts)

    def __init__(self, parts):
        self.parts = parts

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.parts)

    def resolve(self, config):
        return Text(''.join(part.resolve(config).cat() for part in self.parts))

class SimpleValue:

    @classmethod
    def pa(cls, s, l, t):
        value, = t
        return cls(value)

    def __init__(self, value):
        self.value = value

    def resolve(self, config):
        return self

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.value)

class Blank(SimpleValue):

    ignorable = True

class Scalar(SimpleValue):

    ignorable = False
    numberpattern = re.compile('^(?:[0-9]+|[0-9]*[.][0-9]+)$')

    @classmethod
    def pa(cls, s, l, t):
        text, = t
        if text in cls.booleans:
            return cls.booleans[text]
        m = cls.numberpattern.search(text)
        if m is None:
            return Text(text)
        if '.' in text:
            return Number(Decimal(text))
        return Number(int(text))

class Text(Scalar):

    def cat(self):
        return self.value

class Number(Scalar):

    pass

class Boolean(Scalar):

    pass

Scalar.booleans = dict([str(x).lower(), Boolean(x)] for x in [True, False])

class Call:

    @classmethod
    def pa(cls, functions, s, l, t):
        return cls(functions, t[0], t[1:])

    def __init__(self, functions, name, args):
        self.functions = functions
        self.name = name
        self.args = args

    def __repr__(self):
        return "%s(%r, %r)" % (type(self).__name__, self.name, self.args)

    def resolve(self, config):
        return self.functions[self.name](*[config] + [a.resolve(config) for a in self.args if not a.ignorable])

class Parser:

    def __init__(self, g):
        self.g = g

    def __call__(self, text):
        result, = self.g.parseString(text, parseAll = True)
        return result

def createparser(functions):
    rawtext = Regex('[^$]+').leaveWhitespace().parseWithTabs()
    text = rawtext.setParseAction(Text.pa)
    action = Forward()
    def clauses():
        for o, c in '()', '[]':
            rawargtext = Regex(r'[^$\s\%s]+' % c)
            argtext = rawargtext.setParseAction(Text.pa)
            arg = Optional(White().setParseAction(Blank.pa)) + (OneOrMore(Optional(argtext) + action) + Optional(argtext) | rawargtext.setParseAction(Scalar.pa)).leaveWhitespace().setParseAction(Concat.pa)
            yield Regex('[^%s]+' % o) + Suppress(o) + ZeroOrMore(arg) + Optional(White().setParseAction(Blank.pa)) + Suppress(c)
    action << (Suppress('$') + Or(clauses())).parseWithTabs().setParseAction(lambda s, l, t: Call.pa(functions, s, l, t))
    template = (OneOrMore(Optional(text) + action) + Optional(text) | rawtext.setParseAction(Scalar.pa) | Empty().setParseAction(lambda s, l, t: Text(''))).parseWithTabs().setParseAction(Concat.pa)
    return Parser(template)
