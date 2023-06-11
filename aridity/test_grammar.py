# Copyright 2017, 2020 Andrzej Cichocki

# This file is part of aridity.
#
# aridity is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# aridity is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with aridity.  If not, see <http://www.gnu.org/licenses/>.

from .config import ConfigCtrl
from .grammar import GFactory, Parser, ZeroOrMore
from .model import Blank, Boolean, Boundary, Call, Concat as ConcatImpl, Entry, nullmonitor, Number, Text
from decimal import Decimal
from functools import partial
from pyparsing import ParseException
from unittest import TestCase

p = expressionparser = Parser(GFactory().create(None), False)
l = loader = Parser(ZeroOrMore(GFactory().create(Entry.pa)), False)
Concat = partial(ConcatImpl, monitor = nullmonitor)

class TestGrammar(TestCase):

    def test_expressionparser(self):
        ae = self.assertEqual
        ae([Text('x')], p('x'))
        ae([Text('yy')], p('yy'))
        ae([Text('x'), Blank('  '), Text('y')], p('x  y'))
        ae([Blank('\t'), Text('x'), Blank('  '), Text('y'), Blank('\t')], p('\tx  y\t'))
        ae([Blank('\t'), Text('x'), Blank('  '), Text('y'), Boundary('\r')], p('\tx  y\r'))
        ae([Call('a', [], '()')], p('$a()'))
        ae([Call('a', [], '[]')], p('$a[]'))
        ae([Call('ac', [Text('x')], '()')], p('$ac(x)'))
        ae([Call('ac', [Text('x')], '[]')], p('$ac[x]'))
        ae([Call('act', [Text('x'), Blank(' '), Text('yy')], '()')], p('$act(x yy)'))
        ae([Call('act', [Text('x'), Blank(' '), Text('yy')], '[]')], p('$act[x yy]'))
        ae([Call('act', [Blank('\r'), Text('x'), Blank('  '), Text('yy'), Blank('\t')], '()')], p('$act(\rx  yy\t)'))
        ae([Call('act', [Blank('\r'), Text('x'), Blank('  '), Text('yy'), Blank('\t')], '[]')], p('$act[\rx  yy\t]'))
        ae([Call('act', [Blank('\r'), Concat([Text('x'), Call('b', [], '()'), Text('z')]), Blank('  '), Text('yy'), Blank('\t')], '()')], p('$act(\rx$b()z  yy\t)'))
        ae([Call('act', [Blank('\r'), Concat([Text('x'), Call('b', [], '[]'), Text('z')]), Blank('  '), Text('yy'), Blank('\t')], '()')], p('$act(\rx$b[]z  yy\t)'))
        ae([Call('act', [Blank('\r'), Concat([Text('x'), Call('b', [], '[]'), Text('z')]), Blank('  '), Text('yy'), Blank('\t')], '[]')], p('$act[\rx$b[]z  yy\t]'))
        ae([Call('act', [Blank('\r'), Concat([Text('x'), Call('b', [], '()'), Text('z')]), Blank('  '), Text('yy'), Blank('\t')], '[]')], p('$act[\rx$b()z  yy\t]'))
        ae([Text('woo')], p('woo'))
        ae([Concat([Text('woo'), Call('get', [Text('yay')], '()'), Text('houpla')])], p('woo$get(yay)houpla'))
        ae([Text('woo'), Blank(' '), Call('get', [Blank('\n '), Text('yay'), Blank('\n')], '()'), Blank('\t'), Text('houpla'), Blank('  ')], p('''woo $get(\n yay\n)\thoupla  '''))
        ae([Number(1)], p('1'))
        ae([Number(-5)], p('-5'))
        ae([Call('id', [Number(Decimal('.1'))], '()')], p('$id(.1)'))
        ae([Call('id', [Number(Decimal('-5.4'))], '()')], p('$id(-5.4)'))
        ae([Call('id', [Text('.1woo')], '()')], p('$id(.1woo)'))
        ae([Text('100woo')], p('100woo'))
        ae([Boolean(False)], p('false'))
        ae([Call('id', [Boolean(True)], '()')], p('$id(true)'))
        ae([Call('id', [Text('falseyay')], '()')], p('$id(falseyay)'))
        ae([Text('truewoo')], p('truewoo'))
        ae([Concat([Text('100'), Call('a', [], '()')])], p('100$a()'))
        ae([Call('aaa', [Call('bbb', [Text('ccc)ddd')], '[]')], '()')], p('$aaa($bbb[ccc)ddd])'))

    def test_lit(self):
        ae = self.assertEqual
        ae([Text('$doesNotExist(]')], p('''$'($doesNotExist(])'''))
        ae([Text('$doesNotExist[)')], p('''$'[$doesNotExist[)]'''))
        ae([Text(' \t')], p('''$'[ \t]'''))
        ae([Text('10')], p('''$'[10]'''))
        ae([Text('true')], p('''$'(true)'''))

    def test_whitespace(self):
        ae = self.assertEqual
        ae([Blank(' '), Text(' x '), Blank(' ')], p(''' $'( x ) '''))
        ae([Blank(' '), Concat([Text(' '), Text('x'), Text(' ')]), Blank(' ')], p(' $.( x ) '))
        for name in "'", '.':
            for text in (' $ %s( x ) ' % name,
                         ' $%s ( x ) ' % name):
                with self.assertRaises(ParseException):
                    p(text)

    def test_pass(self):
        ae = self.assertEqual
        ae([Concat([Text(' '), Text('x'), Text('  '), Text('y'), Text('\t')])], p('$.( x  y\t)'))
        ae([Concat([Text(' '), Text('x'), Text('  '), Text('y'), Text('\t')])], p('$.[ x  y\t]'))
        ae([Call('act', [Text('x'), Blank(' '), Concat([Text(' '), Text('y'), Text('\t')])], '()')], p('$act(x $.[ y\t])'))
        ae([Concat([Text('10')])], p('$.[10]'))
        ae([Concat([Text('x(')]), Blank(' '), Text(')')], p('$.(x() )')) # Gotcha!
        ae([Concat([Text('x()'), Text(' ')])], p('$.[x() ]'))

    def test_loader(self):
        ae = self.assertEqual
        ae([], l(''))
        ae([Entry([Text('x=')])], l('x='))
        ae([Entry([Text('x='), Blank('  ')])], l('x=  '))
        ae([Entry([Text('x'), Blank(' '), Text('='), Blank(' '), Text('y'), Blank('  '), Text('z'), Blank('\t')])], l('x = y  z\t'))
        ae([Entry([Text('x'), Blank(' '), Text('='), Blank(' '), Text('y'), Blank('\t'), Text('z'), Blank('  ')])], l('x = y\tz  '))
        for eol in '\n', '\r', '\r\n':
            ae([Entry([Text('x=y'), Boundary(eol)]), Entry([Text('x2=y2')])], l('x=y%sx2=y2' % eol))
        ae([Entry([Text('x'), Blank(' '), Text('='), Blank(' '), Boolean(True)])], l('x = true'))
        ae([Entry([Text('x'), Blank(' '), Text('=true'), Blank(' ')])], l('x =true '))
        ae([Entry([Text('x'), Blank(' '), Text('='), Blank(' '), Call('a', [Blank('\n'), Text('b'), Blank('\r')], '()')])], l('x = $a(\nb\r)'))

    def test_functionsdot(self):
        ae = self.assertEqual
        ae([Concat([Text('100')])], p('$.(100)'))
        ae([Call('x', [Concat([Text('100')])], ['', ''])], p('$x$.(100)'))
        ae([Call('y', [Call('x', [Concat([Text('100')])], ['', ''])], ['', ''])], p('$y$x$.(100)'))

    def test_functionsquote(self):
        ae = self.assertEqual
        ae([Text('100')], p("$'(100)"))
        ae([Call('x', [Text('100')], ['', ''])], p("$x$'(100)"))
        ae([Call('y', [Call('x', [Text('100')], ['', ''])], ['', ''])], p("$y$x$'(100)"))

    def test_nestedbrackets(self):
        cc = ConfigCtrl()
        cc.execute('E = E')
        cc.execute('a = $lower(ABC(D$(E)F)GHI(JKL)MNO)')
        cc.execute('b = $lower$.( ABC ( D$(E)F ) GHI ( JKL ) MNO )')
        cc.execute('''c = $lower$'( ABC ( D$(E)F ) GHI ( JKL ) MNO )''')
        self.assertEqual('abc(def)ghi(jkl)mno', cc.node.a)
        self.assertEqual(' abc ( def ) ghi ( jkl ) mno ', cc.node.b)
        self.assertEqual(' abc ( d$(e)f ) ghi ( jkl ) mno ', cc.node.c)
