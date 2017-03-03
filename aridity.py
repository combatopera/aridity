from pyparsing import *

class Cat:

    @classmethod
    def pa(cls, s, l, t):
        return cls(t.asList())

    def __init__(self, parts):
        self.parts = parts

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.parts)

class ArgSep:

    @classmethod
    def pa(cls, s, l, t):
        text, = t
        return cls(text)

    def __init__(self, text):
        self.text = text

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.text)

class Call:

    @classmethod
    def pa(cls, s, l, t):
        return cls(t[0], t[1:])

    def __init__(self, name, args):
        self.name = name
        self.args = args

    def __repr__(self):
        return "%s(%r, %r)" % (type(self).__name__, self.name, self.args)

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

text = Regex('[^$]+').leaveWhitespace().parseWithTabs()
for case in textcases:
    print( case)
    text.parseString(case, parseAll = True).pprint()

action = Forward()
def clauses():
    for o, c in '()', '[]':
        argtext = Regex(r'[^$\s\%s]+' % c)
        arg = Optional(White().setParseAction(ArgSep.pa)) + (OneOrMore(Optional(argtext) + action) + Optional(argtext) | argtext).leaveWhitespace().setParseAction(Cat.pa)
        yield Regex('[^%s]+' % o) + Suppress(o) + ZeroOrMore(arg) + Optional(White().setParseAction(ArgSep.pa)) + Suppress(c)

action << (Suppress('$') + Or(clauses())).parseWithTabs().setParseAction(Call.pa)
for case in actioncases:
    print(repr(case), Parser(action)(case))

templatecases = [
    '',
    'woo',
    'woo$get(yay)houpla',
    '''woo $get(
yay
)\thoupla  ''',
]

template = (OneOrMore(Optional(text) + action) + Optional(text) | text | Empty()).parseWithTabs().setParseAction(Cat.pa)

for case in templatecases:
    print(repr(case), Parser(template)(case))

