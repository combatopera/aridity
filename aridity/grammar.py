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

    def __eq__(self, that):
        return self.parts == that.parts

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.parts)

    def resolve(self, context):
        return Text(''.join(part.resolve(context).cat() for part in self.parts))

class SimpleValue:

    @classmethod
    def pa(cls, s, l, t):
        value, = t
        return cls(value)

    def __init__(self, value):
        self.value = value

    def __eq__(self, that):
        return type(self) == type(that) and self.value == that.value

    def resolve(self, context):
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

    ignorable = False

    def __init__(self, name, args):
        self.name = name
        self.args = args

    def __eq__(self, that):
        return self.name == that.name and self.args == that.args

    def __repr__(self):
        return "%s(%r, %r)" % (type(self).__name__, self.name, self.args)

    def resolve(self, context):
        return context.function(self.name)(*[context] + [a.resolve(context) for a in self.args if not a.ignorable])

class Parser:

    @classmethod
    def create(cls):
        def gettext(pa):
            return Regex('[^$]+').leaveWhitespace().setParseAction(pa)
        opttext = Optional(gettext(Text.pa))
        action = Forward()
        def clauses():
            optblank = Optional(White().setParseAction(Blank.pa))
            for o, c in '()', '[]':
                def getargtext(pa):
                    return Regex(r'[^$\s\%s]+' % c).setParseAction(pa)
                optargtext = Optional(getargtext(Text.pa))
                arg = (OneOrMore(optargtext + action) + optargtext | getargtext(Scalar.pa)).leaveWhitespace().setParseAction(Concat.pa)
                yield Regex('[^%s]+' % o) + Suppress(o) + ZeroOrMore(optblank + arg) + optblank + Suppress(c)
        action << (Suppress('$') + Or(clauses())).setParseAction(lambda s, l, t: Call(t[0], t[1:]))
        template = (OneOrMore(opttext + action) + opttext | gettext(Scalar.pa) | Empty().setParseAction(lambda s, l, t: Text(''))).parseWithTabs().setParseAction(Concat.pa)
        return Parser(template)

    def __init__(self, g):
        self.g = g

    def __call__(self, text):
        result, = self.g.parseString(text, parseAll = True)
        return result

parser = Parser.create()
