#!/usr/bin/env python3

import unittest, grammar as g

class Functions:

    def get(config, key):
        return config[key.cat()]

    def a(config):
        return g.Text('A')

    def b(config):
        return g.Text('B')

    def ac(config, x):
        return g.Text('ac.' + x.resolve(config).cat())

    def id(config, x):
        return x

    def act(config, x, y):
        return g.Text('act.' + x.resolve(config).cat() + '.' + y.resolve(config).cat())

class TestGrammar(unittest.TestCase):

    def test_works(self):
        p = g.createparser(Functions.__dict__)
        self.assertEqual(g.Text('x'), p('x'))
        self.assertEqual(g.Text('yy'), p('yy'))
        self.assertEqual(g.Text('x  y'), p('x  y'))
        self.assertEqual(g.Text('\tx  y\r'), p('\tx  y\r'))
        self.assertEqual(g.Call(None, 'a', []), p('$a()'))

"""
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
"""

if '__main__' == __name__:
    unittest.main()
