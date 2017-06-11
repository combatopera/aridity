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
from .grammar import loader as l
from .model import Text
from .context import Context, NoSuchPathException
from collections import OrderedDict
from .repl import Repl

class TestContext(unittest.TestCase):

    def test_precedence(self):
        c = Context()
        with Repl(c) as repl:
            repl('x = y')
            repl('x2 = y = z')
            repl('blank =')
            repl('= blank')
            repl('write = yo')
            repl('write yo')
        ae = self.assertEqual
        ae('y', c.resolved('x').unravel())
        ae('y = z', c.resolved('x2').unravel())
        ae('', c.resolved('blank').unravel())
        ae('blank', c.resolvables[()].unravel())
        ae('yo', c.resolved('write').unravel())

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
            repl('l = $list(x $(y))')
            repl('y = $(yy)')
            repl('yy = z')
        l = context.resolved('l').unravel()
        self.assertEqual(['x', 'z'], l)

    def test_emptytemplate(self):
        pass # TODO: Implement me.

    def test_proxy(self):
        context = Context()
        with Repl(context) as repl:
            repl('proxy = $(value)')
            repl('items x value = woo')
            repl('text1 = $map($(items) $(value))')
            repl('text2 = $map($(items) $(proxy))')
        for k in 'text1', 'text2':
            self.assertEqual(['woo'], context.resolved(k).unravel())

    def test_listargspaces(self):
        context = Context()
        with Repl(context) as repl:
            repl('d = x  y')
            repl('x = $list(a b c=$(d))')
        self.assertEqual(['a', 'b', 'c=x  y'], context.resolved('x').unravel())

    def test_shortget(self):
        context = Context()
        with Repl(context) as repl:
            repl('woo = yay')
            repl('yay2 = $(woo)')
        self.assertEqual('yay', context.resolved('yay2').unravel())

    def test_barelist(self):
        context = Context()
        with Repl(context) as repl:
            repl('a = ')
            repl('b = yay')
            repl('c = yay houpla')
            repl('c, = $,(c)')
            repl('d = yay 100')
            repl('d, = $,(d)')
            repl('x y = true false')
            repl('tf = $,(x y)')
        ae = self.assertEqual
        ae([], context.resolved('a', aslist = True).unravel())
        ae(['yay'], context.resolved('b', aslist = True).unravel())
        ae(['yay', 'houpla'], context.resolved('c', aslist = True).unravel())
        ae(['yay', 'houpla'], context.resolved('c,').unravel())
        ae(['yay', 100], context.resolved('d', aslist = True).unravel())
        ae(['yay', 100], context.resolved('d,').unravel())
        ae([True, False], context.resolved('x', 'y', aslist = True).unravel())
        ae([True, False], context.resolved('tf').unravel())

    def test_donotresolvewholeforktogetonething(self):
        context = Context()
        with Repl(context) as repl:
            repl('namespace')
            repl('  thing = $(namespace other)')
            repl('  other = data')
        self.assertEqual('data', context.resolved('namespace', 'thing').unravel())
