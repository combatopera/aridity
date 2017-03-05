#!/usr/bin/env python3

import unittest
from grammar import createparser, Text, Call, Blank, Concat

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

class TestGrammar(unittest.TestCase):

    def test_parser(self):
        p = createparser()
        ae = self.assertEqual
        ae(Text('x'), p('x'))
        ae(Text('yy'), p('yy'))
        ae(Text('x  y'), p('x  y'))
        ae(Text('\tx  y\r'), p('\tx  y\r'))
        ae(Call('a', []), p('$a()'))
        ae(Call('ac', [Text('x')]), p('$ac(x)'))
        ae(Call('act', [Text('x'), Blank(' '), Text('yy')]), p('$act(x yy)'))
        ae(Call('act', [Blank('\r'), Text('x'), Blank('  '), Text('yy'), Blank('\t')]), p('$act(\rx  yy\t)'))
        ae(Call('act', [Blank('\r'), Concat([Text('x'), Call('b', []), Text('z')]), Blank('  '), Text('yy'), Blank('\t')]), p('$act(\rx$b()z  yy\t)'))
        ae(Call('act', []), p('$act(\rx$b[]z  yy\t)'))
        ae(Call('a', []), p('$a[]'))
        ae(Call('ac', []), p('$ac[x]'))
        ae(Call('act', []), p('$act[x yy]'))
        ae(Call('act', []), p('$act[\rx  yy\t]'))
        ae(Call('act', []), p('$act[\rx$b[]z  yy\t]'))
        ae(Call('act', []), p('$act[\rx$b()z  yy\t]'))

"""

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
"""

if '__main__' == __name__:
    unittest.main()
