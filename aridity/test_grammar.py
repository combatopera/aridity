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
        for text in '$a()', '$a[]':
            ae(Call('a', []), p(text))
        for text in '$ac(x)', '$ac[x]':
            ae(Call('ac', [Text('x')]), p(text))
        for text in '$act(x yy)', '$act[x yy]':
            ae(Call('act', [Text('x'), Blank(' '), Text('yy')]), p(text))
        for text in '$act(\rx  yy\t)', '$act[\rx  yy\t]':
            ae(Call('act', [Blank('\r'), Text('x'), Blank('  '), Text('yy'), Blank('\t')]), p(text))
        for text in '$act(\rx$b()z  yy\t)', '$act(\rx$b[]z  yy\t)', '$act[\rx$b[]z  yy\t]', '$act[\rx$b()z  yy\t]':
            ae(Call('act', [Blank('\r'), Concat([Text('x'), Call('b', []), Text('z')]), Blank('  '), Text('yy'), Blank('\t')]), p(text))
        ae(Text(''), p(''))
        ae(Text('woo'), p('woo'))
        ae(Concat([Text('woo'), Call('get', [Text('yay')]), Text('houpla')]), p('woo$get(yay)houpla'))

"""

templatecases = [
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
