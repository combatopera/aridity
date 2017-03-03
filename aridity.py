from pyparsing import *
from decimal import Decimal

class Concat:

    isarg = True

    @classmethod
    def pa(cls, s, l, t):
        parts = t.asList()
        return parts[0] if 1 == len(parts) else cls(parts)

    def __init__(self, parts):
        self.parts = parts

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.parts)

    def __call__(self, config):
        return Text(''.join(part(config).cat() for part in self.parts))

class Text:

    isarg = True

    @classmethod
    def pa(cls, s, l, t):
        text, = t
        return cls(text)

    def __init__(self, text):
        self.text = text

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.text)

    def __call__(self, config):
        return self

    def cat(self):
        return self.text

class Number:

    isarg = True

    @classmethod
    def pa(cls, s, l, t):
        val, = t
        return cls(Decimal(val))

    def __init__(self, val):
        self.val = val

    def __call__(self, config):
        return self

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.val)

class ArgSep:

    isarg = False

    def __init__(self, s, l, t):
        self.text, = t

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.text)

    def __call__(self, config):
        return self.text

class Functions:

    def get(config, key):
        return config[key.cat()]

    def a(config):
        return Text('A')

    def b(config):
        return Text('B')

    def ac(config, x):
        return Text('ac.' + x(config).cat())

    def id(config, x):
        return x

    def act(config, x, y):
        return Text('act.' + x(config).cat() + '.' + y(config).cat())

class Call:

    def __init__(self, s, l, t):
        self.name = t[0]
        self.args = t[1:]

    def __repr__(self):
        return "%s(%r, %r)" % (type(self).__name__, self.name, self.args)

    def __call__(self, config):
        return getattr(Functions, self.name)(*[config] + [a(config) for a in self.args if a.isarg])

class Parser:

    def __init__(self, g):
        self.g = g

    def __call__(self, text):
        result, = self.g.parseString(text, parseAll = True)
        return result

textcases = [
    'x',
    'yy',
    'x  y',
    '\tx  y\r',
]
actioncases = [
    '$a()',
    '$ac(x)',
    '$act(x yy)',
    '$act(\rx  yy\t)',
    '$act(\rx$b()z  yy\t)',
    '$act(\rx$b[]z  yy\t)',
    '$a[]',
    '$ac[x]',
    '$act[x yy]',
    '$act[\rx  yy\t]',
    '$act[\rx$b[]z  yy\t]',
    '$act[\rx$b()z  yy\t]',
]

text = Regex('[^$]+').leaveWhitespace().parseWithTabs().setParseAction(Text.pa)
number = Regex('[0-9]+|[0-9]*[.][0-9]+').setParseAction(Number.pa)

#for case in textcases:
#    print( case)
#    text.parseString(case, parseAll = True).pprint()

action = Forward()
def clauses():
    for o, c in '()', '[]':
        argtext = Regex(r'[^$\s\%s]+' % c).setParseAction(Text.pa)
        arg = Optional(White().setParseAction(ArgSep)) + (OneOrMore(Optional(argtext) + action) + Optional(argtext) | number | argtext).leaveWhitespace().setParseAction(Concat.pa)
        yield Regex('[^%s]+' % o) + Suppress(o) + ZeroOrMore(arg) + Optional(White().setParseAction(ArgSep)) + Suppress(c)

action << (Suppress('$') + Or(clauses())).parseWithTabs().setParseAction(Call)
#for case in actioncases:
#    print(repr(case), Parser(action)(case))

templatecases = [
    '',
    'woo',
    'woo$get(yay)houpla',
    '''woo $get(
yay
)\thoupla  ''',
    '1',
    '$id(.1)'
]

template = (OneOrMore(Optional(text) + action) + Optional(text) | number | text | Empty()).parseWithTabs().setParseAction(Concat.pa)

config = {'yay': Text('YAY')}
for case in textcases+actioncases+ templatecases:
    print(repr(case))
    expr = Parser(template)(case)
    print(expr)
    print(repr(expr(config)))

