from pyparsing import *

class Cat:

    isarg = True

    @classmethod
    def pa(cls, s, l, t):
        return cls(t.asList())

    def __init__(self, parts):
        self.parts = parts

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.parts)

    def __call__(self, config):
        return ''.join(part(config) for part in self.parts)

class Literal:

    @classmethod
    def pa(cls, s, l, t):
        text, = t
        return cls(text)

    def __init__(self, text):
        self.text = text

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.text)

    def __call__(self, config):
        return self.text

class ArgSep:

    isarg = False

    @classmethod
    def pa(cls, s, l, t):
        text, = t
        return cls(text)

    def __init__(self, text):
        self.text = text

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.text)

    def __call__(self, config):
        return self.text

class Functions:

    def get(config, key):
        return config[key]

class Call:

    @classmethod
    def pa(cls, s, l, t):
        return cls(t[0], t[1:])

    def __init__(self, name, args):
        self.name = name
        self.args = args

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

text = Regex('[^$]+').leaveWhitespace().parseWithTabs().setParseAction(Literal.pa)
for case in textcases:
    print( case)
    text.parseString(case, parseAll = True).pprint()

action = Forward()
def clauses():
    for o, c in '()', '[]':
        argtext = Regex(r'[^$\s\%s]+' % c).setParseAction(Literal.pa)
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

config = {'yay': 'YAY'}
for case in templatecases:
    print(repr(case))
    expr = Parser(template)(case)
    print(expr)
    print(repr(expr(config)))

