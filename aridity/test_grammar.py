#!/usr/bin/env python3

import unittest
from grammar import parser as p, Text, Call, Blank, Concat, Number, Boolean
from decimal import Decimal

class Functions:

    def get(config, key):
        return config[key.cat()]

    def a(config):
        return Text('A')

    def ac(config, x):
        return Text('ac.' + x.resolve(config).cat())

    def id(config, x):
        return x

    def act(config, x, y):
        return Text('act.' + x.resolve(config).cat() + '.' + y.resolve(config).cat())

class Context:

    def function(self, name):
        return getattr(Functions, name)

class TestGrammar(unittest.TestCase):

    def test_parser(self):
        ae = self.assertEqual
        ae(Text('x'), p('x'))
        ae(Text('yy'), p('yy'))
        ae(Text('x  y'), p('x  y'))
        ae(Text('\tx  y\r'), p('\tx  y\r'))
        for text in ('$a()',
                     '$a[]'):
            ae(Call('a', []), p(text))
        for text in ('$ac(x)',
                     '$ac[x]'):
            ae(Call('ac', [Text('x')]), p(text))
        for text in ('$act(x yy)',
                     '$act[x yy]'):
            ae(Call('act', [Text('x'), Blank(' '), Text('yy')]), p(text))
        for text in ('$act(\rx  yy\t)',
                     '$act[\rx  yy\t]'):
            ae(Call('act', [Blank('\r'), Text('x'), Blank('  '), Text('yy'), Blank('\t')]), p(text))
        for text in ('$act(\rx$b()z  yy\t)',
                     '$act(\rx$b[]z  yy\t)',
                     '$act[\rx$b[]z  yy\t]',
                     '$act[\rx$b()z  yy\t]'):
            ae(Call('act', [Blank('\r'), Concat([Text('x'), Call('b', []), Text('z')]), Blank('  '), Text('yy'), Blank('\t')]), p(text))
        ae(Text(''), p(''))
        ae(Text('woo'), p('woo'))
        ae(Concat([Text('woo'), Call('get', [Text('yay')]), Text('houpla')]), p('woo$get(yay)houpla'))
        ae(Concat([Text('woo '), Call('get', [Blank('\n '), Text('yay'), Blank('\n')]), Text('\thoupla  ')]), p('''woo $get(
 yay
)\thoupla  '''))
        ae(Number(1), p('1'))
        ae(Call('id', [Number(Decimal('.1'))]), p('$id(.1)'))
        ae(Call('id', [Text('.1woo')]), p('$id(.1woo)'))
        ae(Text('100woo'), p('100woo'))
        ae(Boolean(False), p('false'))
        ae(Call('id', [Boolean(True)]), p('$id(true)'))
        ae(Call('id', [Text('falseyay')]), p('$id(falseyay)'))
        ae(Text('truewoo'), p('truewoo'))

    def test_resolve(self):
        c = Context()
        ae = self.assertEqual
        ae(Text(''), Text('').resolve(None))
        ae(Text('\r\n\t'), Text('\r\n\t').resolve(None))
        ae(Text('A'), Call('a', []).resolve(c))
        ae(Text('A'), Call('a', [Blank('   ')]).resolve(c))
        ae(Text('ac.woo'), Call('ac', [Blank('\t'), Text('woo')]).resolve(c))
        ae(Text('act.woo.yay'), Call('act', [Text('woo'), Blank(' '), Text('yay')]).resolve(c))
        ae(Number(-123), Call('id', [Number(-123)]).resolve(c))

"""

config = {'yay': grammar.Text('YAY')}
for case in textcases+actioncases+ templatecases:
    print(repr(case))
    expr = grammar.createparser(Functions.__dict__)(case)
    print(expr)
    print(repr(expr.resolve(config)))
"""

if '__main__' == __name__:
    unittest.main()
