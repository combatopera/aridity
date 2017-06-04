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
from .grammar import expressionparser as p, loader as l
from .model import Text, Call, Blank, Concat, Number, Function, List
from .context import Context, NoSuchPathException
from collections import OrderedDict
from .util import allfunctions
from .repl import Repl

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
        c['gett',], = p('$($pass())') # FIXME: Using lit does not work.
        ae = self.assertEqual
        ae(Text(''), Text('').resolve(None))
        ae(Text('\r\n\t'), Text('\r\n\t').resolve(None))
        ae(Text('A'), Call('a', []).resolve(c))
        ae(Text('A'), Call('a', [Blank('   ')]).resolve(c))
        ae(Text('ac.woo'), Call('ac', [Blank('\t'), Text('woo')]).resolve(c))
        ae(Text('act.woo.yay'), Call('act', [Text('woo'), Blank(' '), Text('yay')]).resolve(c))
        ae(Number(-123), Call('id', [Number(-123)]).resolve(c))
        ae(Number(-124), Call('get', [Text('minus124')]).resolve(c))
        ae(Number(-124), Call('gett', [Text('minus124')]).resolve(c))
        ae(Text('ac.A'), Call('ac', [Call('a', [])]).resolve(c))
        ae(Text('xy'), Concat([Text('x'), Text('y')]).resolve(c))
        ae(Number(-124), Call('get', [Call('get', [Text('minus124txt')])]).resolve(c))

    def test_pass2(self):
        ae = self.assertEqual
        c = Context()
        for name, f in allfunctions(Functions):
            if name in ('act',):
                c[name,] = Function(f)
        ae(Text('act.x. y\t'), Concat(p('$act(x $pass[ y\t])')).resolve(c))
        ae(Text('act.x. '), Concat(p('$act(x $pass( ))')).resolve(c))
        ae(Text(' 100'), Concat(p('$pass( 100)')).resolve(c))

    def test_map(self): # TODO: Also test 2-arg form.
        call, = p('$map($list(a b 0) x $str($get(x))2)')
        self.assertEqual(List([Text('a2'), Text('b2'), Text('02')]), call.resolve(Context()))

    def test_join(self):
        call, = p('$join($list(a bb ccc) -)')
        self.assertEqual(Text('a-bb-ccc'), call.resolve(Context()))

    def test_modifiers(self):
        self.modifiers('v = $list()\nv one = $list()\nv one 1 = $list()\nv one 1 un = uno')

    def test_modifiers2(self):
        self.modifiers('v one 1 un = uno')

    def modifiers(self, text):
        context = Context()
        for entry in l(text):
            context.execute(entry)
        ae = self.assertEqual
        ae(Text('uno'), context.resolved('v', 'one', '1', 'un'))
        ae([Text('uno')], list(context.resolved('v', 'one', '1')))
        ae([[Text('uno')]], [list(x) for x in context.resolved('v', 'one')])
        ae([[[Text('uno')]]], [[list(y) for y in x] for x in context.resolved('v')])

    def test_fork(self):
        self.fork('hmm = woo\nv = $list()\nv one = $fork()\nv one 1 = uno\nv two = $fork()\n\r\r\nv two hmm = yay')

    def test_fork2(self):
        self.fork('hmm = woo\nv one 1 = uno\n\r\r\nv two hmm = yay')

    def fork(self, text):
        context = Context()
        for entry in l(text):
            context.execute(entry)
        ae = self.assertEqual
        ae(Text('uno'), context.resolved('v', 'one', '1'))
        ae(OrderedDict([('1', Text('uno'))]), context.resolved('v', 'one').objs)
        ae(OrderedDict([('hmm', Text('yay'))]), context.resolved('v', 'two').objs)
        ae(Text('woo'), context.resolved('v', 'one').resolved('hmm'))
        ae(Text('yay'), context.resolved('v', 'two').resolved('hmm'))
        ae([OrderedDict([('1', Text('uno'))]), OrderedDict([('hmm', Text('yay'))])], [f.objs for f in context.resolved('v')])

    def test_absent(self):
        c = Context()
        with self.assertRaises(NoSuchPathException):
            c.resolved('hmm')

    def test_listsareresolved(self):
        context = Context()
        with Repl(context) as repl:
            repl('l = $list(x $get(y))')
            repl('y = $get(yy)')
            repl('yy = z')
        l = context.resolved('l').unravel()
        self.assertEqual(['x', 'z'], l)

    def test_emptytemplate(self):
        pass # TODO: Implement me.

    def test_proxy(self):
        context = Context()
        with Repl(context) as repl:
            repl('proxy = $get(value)')
            repl('items x value = woo')
            repl('text1 = $map($get(items) $get(value))')
            repl('text2 = $map($get(items) $get(proxy))')
        for k in 'text1', 'text2':
            self.assertEqual(['woo'], context.resolved(k).unravel())

    def test_listargspaces(self):
        context = Context()
        with Repl(context) as repl:
            repl('d = x  y')
            repl('x = $list(a b c=$get(d))')
        self.assertEqual(['a', 'b', 'c=x  y'], context.resolved('x').unravel())

    def test_get2(self):
        context = Context()
        with Repl(context) as repl:
            repl('woo = yay')
            repl('yay2 = $(woo)')
        self.assertEqual('yay', context.resolved('yay2').unravel())
