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

from .test_grammar import expressionparser as p
from .model import Blank, Call, Concat, Function, Number, Text
from .scope import Scope
from .util import allfunctions
from unittest import TestCase

class Functions:

    def a(scope):
        return Text('A')

    def ac(scope, x):
        return Text('ac.' + x.resolve(scope).cat())

    def id(scope, x):
        return x

    def act(scope, x, y):
        return Text('act.' + x.resolve(scope).cat() + '.' + y.resolve(scope).cat())

class TestModel(TestCase):

    def test_resolve(self):
        s = Scope()
        for name, f in allfunctions(Functions):
            if name in ('a', 'ac', 'act', 'id'):
                s[name,] = Function(f)
        s['minus124',] = Number(-124)
        s['minus124txt',] = Text('minus124')
        s['gett',], = p('$($.())')
        ae = self.assertEqual
        ae(Text(''), Text('').resolve(None))
        ae(Text('\r\n\t'), Text('\r\n\t').resolve(None))
        ae(Text('A'), Call('a', [], None).resolve(s))
        ae(Text('A'), Call('a', [Blank('   ')], None).resolve(s))
        ae(Text('ac.woo'), Call('ac', [Blank('\t'), Text('woo')], None).resolve(s))
        ae(Text('act.woo.yay'), Call('act', [Text('woo'), Blank(' '), Text('yay')], None).resolve(s))
        ae(Number(-123), Call('id', [Number(-123)], None).resolve(s))
        ae(Number(-124), Call('', [Text('minus124')], None).resolve(s))
        ae(Number(-124), Call('gett', [Text('minus124')], None).resolve(s))
        ae(Text('ac.A'), Call('ac', [Call('a', [], None)], None).resolve(s))
        ae(Text('xy'), Concat([Text('x'), Text('y')]).resolve(s))
        ae(Number(-124), Call('', [Call('', [Text('minus124txt')], None)], None).resolve(s))

    def test_emptyliteral(self):
        self.assertEqual([Text('')], p("$'()"))
        self.assertEqual([Call('', [Text('')], '()')], p("$($'())"))

    def test_passresolve(self):
        ae = self.assertEqual
        s = Scope()
        for name, f in allfunctions(Functions):
            if name in ('act',):
                s[name,] = Function(f)
        ae(Text('act.x. y\t'), Concat(p('$act(x $.[ y\t])')).resolve(s))
        ae(Text('act.x. '), Concat(p('$act(x $.( ))')).resolve(s))
        ae(Text(' 100'), Concat(p('$.( 100)')).resolve(s))

    def test_map(self): # TODO: Also test 2-arg form.
        call, = p('$map($list(a b 0) x $(x)2)')
        self.assertEqual([Text('a2'), Text('b2'), Text('02')], [v for _, v in call.resolve(Scope()).resolvables.items()])

    def test_join(self):
        call, = p('$join($list(a bb ccc) -)')
        self.assertEqual(Text('a-bb-ccc'), call.resolve(Scope()))
