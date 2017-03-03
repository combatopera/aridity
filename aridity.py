from pyparsing import *

class Cat:

    isarg = True

    def __init__(self, s, l, t):
        self.parts = t.asList()

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.parts)

    def __call__(self, config):
        return ''.join(part(config) for part in self.parts)

class Literal:

    def __init__(self, s, l, t):
        self.text, = t

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.text)

    def __call__(self, config):
        return self.text

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
        return config[key]

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

text = Regex('[^$]+').leaveWhitespace().parseWithTabs().setParseAction(Literal)
for case in textcases:
    print( case)
    text.parseString(case, parseAll = True).pprint()

action = Forward()
def clauses():
    for o, c in '()', '[]':
        argtext = Regex(r'[^$\s\%s]+' % c).setParseAction(Literal)
        arg = Optional(White().setParseAction(ArgSep)) + (OneOrMore(Optional(argtext) + action) + Optional(argtext) | argtext).leaveWhitespace().setParseAction(Cat)
        yield Regex('[^%s]+' % o) + Suppress(o) + ZeroOrMore(arg) + Optional(White().setParseAction(ArgSep)) + Suppress(c)

action << (Suppress('$') + Or(clauses())).parseWithTabs().setParseAction(Call)
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

template = (OneOrMore(Optional(text) + action) + Optional(text) | text | Empty()).parseWithTabs().setParseAction(Cat)

config = {'yay': 'YAY'}
for case in templatecases:
    print(repr(case))
    expr = Parser(template)(case)
    print(expr)
    print(repr(expr(config)))

