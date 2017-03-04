from pyparsing import *
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

class Scalar:

    ignorable = False

    def __init__(self, value):
        self.value = value

    def resolve(self, config):
        return self

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.value)

class Text(Scalar):

    @classmethod
    def pa(cls, s, l, t):
        text, = t
        return cls(text)

    def cat(self):
        return self.value

class Number(Scalar):

    pass

numberpattern = re.compile('^(?:[0-9]+|[0-9]*[.][0-9]+)$')

def scalar(s, l, t):
    text, = t
    if 'true' == text or 'false' == text: return Number('true'==text)
    m = numberpattern.search(text)
    if m is None: return Text(text)
    if '.' in text: return Number(Decimal(text))
    return Number(int(text))

class Blank:

    ignorable = True

    def __init__(self, s, l, t):
        self.text, = t

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.text)

    def resolve(self, config):
        return self.text

class Functions:

    def get(config, key):
        return config[key.cat()]

    def a(config):
        return Text('A')

    def b(config):
        return Text('B')

    def ac(config, x):
        return Text('ac.' + x.resolve(config).cat())

    def id(config, x):
        return x

    def act(config, x, y):
        return Text('act.' + x.resolve(config).cat() + '.' + y.resolve(config).cat())

class Call:

    def __init__(self, s, l, t):
        self.name = t[0]
        self.args = t[1:]

    def __repr__(self):
        return "%s(%r, %r)" % (type(self).__name__, self.name, self.args)

    def resolve(self, config):
        return getattr(Functions, self.name)(*[config] + [a.resolve(config) for a in self.args if not a.ignorable])

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

rawtext = Regex('[^$]+').leaveWhitespace().parseWithTabs()
text = rawtext.setParseAction(Text.pa)

#for case in textcases:
#    print( case)
#    text.parseString(case, parseAll = True).pprint()

action = Forward()
def clauses():
    for o, c in '()', '[]':
        rawargtext = Regex(r'[^$\s\%s]+' % c)
        argtext = rawargtext.setParseAction(Text.pa)
        arg = Optional(White().setParseAction(Blank)) + (OneOrMore(Optional(argtext) + action) + Optional(argtext) | rawargtext.setParseAction(scalar)).leaveWhitespace().setParseAction(Concat.pa)
        yield Regex('[^%s]+' % o) + Suppress(o) + ZeroOrMore(arg) + Optional(White().setParseAction(Blank)) + Suppress(c)

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
    '$id(.1)',
    '$id(.1woo)',
    '100woo',
    'false',
    '$id(true)',
    '$id(falseyay)',
    'truewoo',
]

template = (OneOrMore(Optional(text) + action) + Optional(text) | rawtext.setParseAction(scalar) | Empty().setParseAction(lambda *args: Text(''))).parseWithTabs().setParseAction(Concat.pa)

config = {'yay': Text('YAY')}
for case in textcases+actioncases+ templatecases:
    print(repr(case))
    expr = Parser(template)(case)
    print(expr)
    print(repr(expr.resolve(config)))

