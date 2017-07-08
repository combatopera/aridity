# Copyright 2017 Andrzej Cichocki

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

import unittest
from .grammar import expressionparser as p
from .model import Text, Call, Blank, Concat, Number, Function, List
from .context import Context
from .util import allfunctions

class Functions:

    def a(context):
        return Text('A')

    def ac(context, x):
        return Text('ac.' + x.resolve(context).cat())

    def id(context, x):
        return x

    def act(context, x, y):
        return Text('act.' + x.resolve(context).cat() + '.' + y.resolve(context).cat())

class TestModel(unittest.TestCase):

    def test_resolve(self):
        c = Context()
        for name, f in allfunctions(Functions):
            if name in ('a', 'ac', 'act', 'id'):
                c[name,] = Function(f)
        c['minus124',] = Number(-124)
        c['minus124txt',] = Text('minus124')
        c['gett',], = p('$($.())')
        ae = self.assertEqual
        ae(Text(''), Text('').resolve(None))
        ae(Text('\r\n\t'), Text('\r\n\t').resolve(None))
        ae(Text('A'), Call('a', []).resolve(c))
        ae(Text('A'), Call('a', [Blank('   ')]).resolve(c))
        ae(Text('ac.woo'), Call('ac', [Blank('\t'), Text('woo')]).resolve(c))
        ae(Text('act.woo.yay'), Call('act', [Text('woo'), Blank(' '), Text('yay')]).resolve(c))
        ae(Number(-123), Call('id', [Number(-123)]).resolve(c))
        ae(Number(-124), Call('', [Text('minus124')]).resolve(c))
        ae(Number(-124), Call('gett', [Text('minus124')]).resolve(c))
        ae(Text('ac.A'), Call('ac', [Call('a', [])]).resolve(c))
        ae(Text('xy'), Concat([Text('x'), Text('y')]).resolve(c))
        ae(Number(-124), Call('', [Call('', [Text('minus124txt')])]).resolve(c))

    def test_emptyliteral(self):
        self.assertEqual([Text('')], p("$'()"))
        self.assertEqual([Call('', [Text('')], '()')], p("$($'())"))

    def test_passresolve(self):
        ae = self.assertEqual
        c = Context()
        for name, f in allfunctions(Functions):
            if name in ('act',):
                c[name,] = Function(f)
        ae(Text('act.x. y\t'), Concat(p('$act(x $.[ y\t])')).resolve(c))
        ae(Text('act.x. '), Concat(p('$act(x $.( ))')).resolve(c))
        ae(Text(' 100'), Concat(p('$.( 100)')).resolve(c))

    def test_map(self): # TODO: Also test 2-arg form.
        call, = p('$map($list(a b 0) x $(x)2)')
        self.assertEqual(List([Text('a2'), Text('b2'), Text('02')]), call.resolve(Context()))

    def test_join(self):
        call, = p('$join($list(a bb ccc) -)')
        self.assertEqual(Text('a-bb-ccc'), call.resolve(Context()))
