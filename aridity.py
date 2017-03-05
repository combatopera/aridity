from aridity import grammar

class Functions:

    def get(config, key):
        return config[key.cat()]

    def a(config):
        return grammar.Text('A')

    def b(config):
        return grammar.Text('B')

    def ac(config, x):
        return grammar.Text('ac.' + x.resolve(config).cat())

    def id(config, x):
        return x

    def act(config, x, y):
        return grammar.Text('act.' + x.resolve(config).cat() + '.' + y.resolve(config).cat())

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

config = {'yay': grammar.Text('YAY')}
for case in textcases+actioncases+ templatecases:
    print(repr(case))
    expr = grammar.createparser(Functions.__dict__)(case)
    print(expr)
    print(repr(expr.resolve(config)))

