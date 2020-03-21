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

import unittest, tempfile, collections
from .grammar import loader as l
from .model import Directive, Stream, Text
from .context import Context, NoSuchPathException
from .repl import Repl

class TestContext(unittest.TestCase):

    def test_precedence(self):
        c = Context()
        with Repl(c) as repl:
            repl('x = y')
            repl('x2 = y $.(=) z') # FIXME: Quote should work too.
            repl('blank =')
            repl("$'() = blank")
            repl('write yo')
            repl('$.(write) = yo')
        ae = self.assertEqual
        ae('y', c.resolved('x').unravel())
        ae('y = z', c.resolved('x2').unravel())
        ae('', c.resolved('blank').unravel())
        ae('blank', c.resolved('').unravel())
        ae('yo', c.resolved('write').unravel())

    def test_directivestack(self):
        phrases = []
        def eq(prefix, phrase, context):
            phrases.append(phrase.cat())
        c = Context()
        self.assertEqual(0, len(c.resolvables.keys()))
        c['=',] = Directive(eq)
        self.assertEqual(1, len(c.resolvables.keys()))
        with Repl(c) as repl:
            repl('woo = yay')
        self.assertEqual(['yay'], phrases)
        with self.assertRaises(NoSuchPathException):
            c.resolved('woo')

    def test_modifiers(self):
        context = self.modifiers('v := $list()\nv one := $list()\nv one 1 := $list()\nv one 1 un = uno')
        ae = self.assertEqual
        ae(['uno'], context.resolved('v', 'one', '1').unravel())
        ae([['uno']], context.resolved('v', 'one').unravel())
        ae([[['uno']]], context.resolved('v').unravel())

    def test_modifiers2(self):
        context = self.modifiers('v one 1 un = uno')
        ae = self.assertEqual
        ae({'un': 'uno'}, context.resolved('v', 'one', '1').unravel())
        ae({'1': {'un': 'uno'}}, context.resolved('v', 'one').unravel())
        ae({'one': {'1': {'un': 'uno'}}}, context.resolved('v').unravel())

    def modifiers(self, text):
        context = Context()
        for entry in l(text):
            context.execute(entry)
        self.assertEqual('uno', context.resolved('v', 'one', '1', 'un').unravel())
        return context

    def test_fork(self):
        c = self.fork('hmm = woo\nv := $list()\nv one := $fork()\nv one 1 = uno\nv two := $fork()\n\r\r\nv two hmm = yay')
        self.assertEqual([{'1': 'uno'}, {'hmm': 'yay'}], c.resolved('v').unravel())

    def test_fork2(self):
        c = self.fork('hmm = woo\nv one 1 = uno\n\r\r\nv two hmm = yay')
        self.assertEqual({'one': {'1': 'uno'}, 'two': {'hmm': 'yay'}}, c.resolved('v').unravel())

    def fork(self, text):
        context = Context()
        for entry in l(text):
            context.execute(entry)
        ae = self.assertEqual
        ae(Text('uno'), context.resolved('v', 'one', '1'))
        ae({'1': 'uno'}, context.resolved('v', 'one').unravel())
        ae({'hmm': 'yay'}, context.resolved('v', 'two').unravel())
        ae(Text('woo'), context.resolved('v', 'one').resolved('hmm'))
        ae(Text('yay'), context.resolved('v', 'two').resolved('hmm'))
        return context

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
        context = Context()
        chunks = []
        context['stdout',] = Stream(collections.namedtuple('Chunks', 'write flush')(chunks.append, lambda: None))
        with tempfile.NamedTemporaryFile() as f, Repl(context) as repl:
            repl.printf("< %s", f.name)
        self.assertEqual([''], chunks)

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

    def test_aslistemptypath(self):
        c = Context()
        with Repl(c) as repl:
            repl('x = y z')
        ae = self.assertEqual
        ae('y z', c.resolved('x').unravel())
        ae(['y', 'z'], c.resolved('x', aslist = True).unravel())
        ae({'x': 'y z'}, c.resolved().unravel())
        ae({'x': 'y z'}, c.resolved(aslist = True).unravel()) # XXX: Really?

    def test_donotresolvewholeforktogetonething(self):
        context = Context()
        with Repl(context) as repl:
            repl('namespace')
            repl('  thing = $(namespace other)')
            repl('  other = data')
        self.assertEqual('data', context.resolved('namespace', 'thing').unravel())

    def test_star(self):
        context = Context()
        with Repl(context) as repl:
            repl('hmm * woo = yay')
            repl('hmm item woo = itemYay')
            repl('hmm item2 x = y')
            repl("hmm $.(*) woo2 = yay2")
        ae = self.assertEqual
        ae({'woo': 'yay', 'x': 'y'}, context.resolved('hmm', 'item2').unravel())
        ae({'woo': 'yay', 'woo2': 'yay2'}, context.resolved('hmm', '*').unravel())
        ae({'woo': 'itemYay'}, context.resolved('hmm', 'item').unravel())
        items = context.resolved('hmm').unravel()
        ae('itemYay', items['item']['woo'])
        ae('y', items['item2']['x'])
        ae('yay2', items['*']['woo2'])
        ae('yay', items['item2']['woo'])
        ae('yay', items['*']['woo'])

    def test_relmod(self):
        context = Context()
        with Repl(context) as repl:
            repl('ns * stuff = $(woo) there')
            repl('ns item woo = yay')
        ae = self.assertEqual
        ae({'stuff': 'yay there', 'woo': 'yay'}, context.resolved('ns', 'item').unravel())
        ae({'item': {'stuff': 'yay there', 'woo': 'yay'}}, context.resolved('ns').unravel())
        ae('yay there', context.resolved('ns', 'item', 'stuff').unravel())

    def test_relmod2(self):
        context = Context()
        with Repl(context) as repl:
            repl('ns my.key = value')
            repl('ns item woo = $(my.key)')
        ae = self.assertEqual
        ae({'item': {'woo': 'value'}, 'my.key': 'value'}, context.resolved('ns').unravel())
        ae({'woo': 'value'}, context.resolved('ns', 'item').unravel())
        ae('value', context.resolved('ns', 'item', 'woo').unravel())

    def test_relmod3(self):
        context = Context()
        with Repl(context) as repl:
            repl('ns my key = value')
            repl('ns item woo = $(my key)')
        ae = self.assertEqual
        ae({'item': {'woo': 'value'}, 'my': {'key': 'value'}}, context.resolved('ns').unravel())
        ae({'woo': 'value'}, context.resolved('ns', 'item').unravel())
        ae('value', context.resolved('ns', 'item', 'woo').unravel())

    def test_relmod4(self):
        context = Context()
        with Repl(context) as repl:
            repl('woo port = 102')
            repl('yay * port = 100')
            repl('yay 0 x = 0')
            repl('yay 1 x = 1')
            repl('yay 2 x = 2')
            repl('yay 1 port = 101')
            repl('yay 2 port = $(woo port)')
        ae = self.assertEqual
        ae({'0': {'x': 0, 'port': 100}, '1': {'x': 1, 'port': 101}, '2': {'x': 2, 'port': 102}}, context.resolved('yay').unravel())
        ae({'x': 2, 'port': 102}, context.resolved('yay', '2').unravel())
        ae(102, context.resolved('yay', '2', 'port').unravel())

    def test_nestedinclude(self):
        context = Context()
        with tempfile.NamedTemporaryFile() as f:
            f.write('\t\n\nwoo = yay'.encode()) # Blank lines should be ignored.
            f.flush()
            with Repl(context) as repl:
                repl.printf("ns . %s", f.name)
        ae = self.assertEqual
        ae({'ns': {'woo': 'yay'}}, context.resolved().unravel())
        ae({'woo': 'yay'}, context.resolved('ns').unravel())
        ae('yay', context.resolved('ns', 'woo').unravel())

    def test_anonymouslistelements(self):
        context = Context()
        with Repl(context) as repl:
            repl('woo += yay')
            repl('woo += $(houpla  )')
            repl('houpla = x')
        ae = self.assertEqual
        ae({'yay': 'yay', '$(houpla  )': 'x'}, context.resolved('woo').unravel())

    def test_anonymouslistelements2(self):
        context = Context()
        with Repl(context) as repl:
            repl('woo += yay 1')
            repl('woo += yay  $[two]')
            repl('two = 2')
        ae = self.assertEqual
        ae({'yay 1': 'yay 1', 'yay  $[two]': 'yay  2'}, context.resolved('woo').unravel())

    def test_thisusedtowork(self):
        context = Context()
        with Repl(context) as repl:
            repl('x paths += woo')
            repl('x paths += yay')
            repl('y paths = $(x paths)')
        ae = self.assertEqual
        ae({'woo': 'woo', 'yay': 'yay'}, context.resolved('y', 'paths').unravel())

    def test_commandarg(self):
        base = Context()
        with Repl(base) as repl:
            repl('my command = do $(arg)')
        tmp = base.createchild()
        with Repl(tmp) as repl:
            repl('arg = myval')
        # Doesn't matter where my command was found, it should be resolved against tmp:
        try:
            self.assertEqual('do myval', tmp.resolved('my', 'command').unravel())
            self.assertEqual(['do', 'myval'], tmp.resolved('my', 'command', aslist = True).unravel())
            self.fail('You fixed a bug!')
        except NoSuchPathException:
            pass

    def test_blanklines(self):
        context = Context()
        with Repl(context) as repl:
            repl('')
            repl('woo = yay')
            repl('')
            repl('woo2 = yay2')
            repl('')
        self.assertEqual({'woo': 'yay', 'woo2': 'yay2'}, context.resolved().unravel())

    def test_try(self):
        context = Context()
        with Repl(context) as repl:
            repl('woo = yay1')
            repl('yay1 = $try($(woo) yay2)')
            repl('yay2 = $try($(xxx) yay2)')
        self.assertEqual('yay1', context.resolved('yay1').unravel())
        self.assertEqual('yay2', context.resolved('yay2').unravel())

    def test_findpath(self):
        context = Context()
        with Repl(context) as repl:
            repl('root')
            repl('\tparent bar = x')
            repl('\teranu')
            repl('\t\tparent foo = e')
            repl('\tuvavu')
            repl('\t\tparent foo = u')
        self.assertEqual('e', context.resolved('root', 'eranu', 'parent', 'foo').unravel())
        self.assertEqual('u', context.resolved('root', 'uvavu', 'parent', 'foo').unravel())
        self.assertEqual('x', context.resolved('root', 'parent', 'bar').unravel())
        self.assertEqual('x', context.resolved('root', 'eranu', 'parent', 'bar').unravel())
        self.assertEqual('x', context.resolved('root', 'uvavu', 'parent', 'bar').unravel())
