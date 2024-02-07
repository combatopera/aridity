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

from .test_grammar import loader as l
from .model import Directive, Stream, Text
from .repl import Repl
from .scope import Scope, StaticScope
from .util import CycleException, NoSuchPathException
from collections import namedtuple
from tempfile import NamedTemporaryFile
from unittest import TestCase
import os

class TestScope(TestCase):

    def test_precedence(self):
        s = Scope()
        with Repl(s) as repl:
            repl('x = y')
            repl('x2 = y $.(=) z') # FIXME: Quote should work too.
            repl('blank =')
            repl("$'() = blank")
            repl('!write yo')
            repl('$.(!write) = yo')
        ae = self.assertEqual
        ae('y', s.resolved('x').unravel())
        ae('y = z', s.resolved('x2').unravel())
        ae('', s.resolved('blank').unravel())
        ae('blank', s.resolved('').unravel())
        ae('yo', s.resolved('!write').unravel())

    def test_directivestack(self):
        phrases = []
        def eq(prefix, suffix, scope):
            phrases.append(suffix.tophrase().cat())
        s = Scope()
        self.assertEqual(0, sum(1 for _ in s.resolvables.items()))
        s['=',] = Directive(eq)
        self.assertEqual(1, sum(1 for _ in s.resolvables.items()))
        with Repl(s) as repl:
            repl('woo = yay')
        self.assertEqual(['yay'], phrases)
        with self.assertRaises(NoSuchPathException):
            s.resolved('woo')

    def test_modifiers(self):
        scope = self.modifiers('v := $list()\nv one := $list()\nv one 1 := $list()\nv one 1 un = uno')
        ae = self.assertEqual
        ae(['uno'], scope.resolved('v', 'one', '1').unravel())
        ae([['uno']], scope.resolved('v', 'one').unravel())
        ae([[['uno']]], scope.resolved('v').unravel())

    def test_modifiers2(self):
        scope = self.modifiers('v one 1 un = uno')
        ae = self.assertEqual
        ae({'un': 'uno'}, scope.resolved('v', 'one', '1').unravel())
        ae({'1': {'un': 'uno'}}, scope.resolved('v', 'one').unravel())
        ae({'one': {'1': {'un': 'uno'}}}, scope.resolved('v').unravel())

    def modifiers(self, text):
        scope = Scope()
        for entry in l(text):
            scope.execute(entry)
        self.assertEqual('uno', scope.resolved('v', 'one', '1', 'un').unravel())
        return scope

    def test_fork(self):
        s = self.fork('hmm = woo\nv := $list()\nv one := $fork()\nv one 1 = uno\nv two := $fork()\n\r\r\nv two hmm = yay')
        self.assertEqual([{'1': 'uno'}, {'hmm': 'yay'}], s.resolved('v').unravel())

    def test_fork2(self):
        s = self.fork('hmm = woo\nv one 1 = uno\n\r\r\nv two hmm = yay')
        self.assertEqual({'one': {'1': 'uno'}, 'two': {'hmm': 'yay'}}, s.resolved('v').unravel())

    def fork(self, text):
        scope = Scope()
        for entry in l(text):
            scope.execute(entry)
        ae = self.assertEqual
        ae(Text('uno'), scope.resolved('v', 'one', '1'))
        ae({'1': 'uno'}, scope.resolved('v', 'one').unravel())
        ae({'hmm': 'yay'}, scope.resolved('v', 'two').unravel())
        ae(Text('woo'), scope.resolved('v', 'one').resolved('hmm'))
        ae(Text('yay'), scope.resolved('v', 'two').resolved('hmm'))
        return scope

    def test_absent(self):
        s = Scope()
        with self.assertRaises(NoSuchPathException):
            s.resolved('hmm')

    def test_listsareresolved(self):
        scope = Scope()
        with Repl(scope) as repl:
            repl('l = $list(x $(y))')
            repl('y = $(yy)')
            repl('yy = z')
        l = scope.resolved('l').unravel()
        self.assertEqual(['x', 'z'], l)

    def test_emptytemplate(self):
        scope = Scope()
        chunks = []
        scope['stdout',] = Stream(namedtuple('Chunks', 'write flush')(chunks.append, lambda: None))
        with NamedTemporaryFile() as f, Repl(scope) as repl:
            repl.printf("< %s", f.name)
        self.assertEqual([''], chunks)

    def test_proxy(self):
        scope = Scope()
        with Repl(scope) as repl:
            repl('proxy = $(value)')
            repl('items x value = woo')
            repl('text1 = $map($(items) $(value))')
            repl('text2 = $map($(items) $(proxy))')
        for k in 'text1', 'text2':
            self.assertEqual(['woo'], scope.resolved(k).unravel())

    def test_listargspaces(self):
        scope = Scope()
        with Repl(scope) as repl:
            repl('d = x  y')
            repl('x = $list(a b c=$(d))')
        self.assertEqual(['a', 'b', 'c=x  y'], scope.resolved('x').unravel())

    def test_shortget(self):
        scope = Scope()
        with Repl(scope) as repl:
            repl('woo = yay')
            repl('yay2 = $(woo)')
        self.assertEqual('yay', scope.resolved('yay2').unravel())

    def test_barelist(self):
        scope = Scope()
        with Repl(scope) as repl:
            repl('a = ')
            repl('b = yay')
            repl('c = yay houpla')
            repl('c, = $,(c)')
            repl('d = yay 100')
            repl('d, = $,(d)')
            repl('x y = true false')
            repl('tf = $,(x y)')
        ae = self.assertEqual
        ae([], scope.resolved('a', aslist = True).unravel()) # TODO: Config API equivalent.
        ae(['yay'], scope.resolved('b', aslist = True).unravel())
        ae(['yay', 'houpla'], scope.resolved('c', aslist = True).unravel())
        ae(['yay', 'houpla'], scope.resolved('c,').unravel())
        ae(['yay', 100], scope.resolved('d', aslist = True).unravel())
        ae(['yay', 100], scope.resolved('d,').unravel())
        ae([True, False], scope.resolved('x', 'y', aslist = True).unravel())
        ae([True, False], scope.resolved('tf').unravel())

    def test_aslistemptypath(self):
        s = Scope()
        with Repl(s) as repl:
            repl('x = y z')
        ae = self.assertEqual
        ae('y z', s.resolved('x').unravel())
        ae(['y', 'z'], s.resolved('x', aslist = True).unravel())
        ae({'x': 'y z'}, s.resolved().unravel())
        ae({'x': 'y z'}, s.resolved(aslist = True).unravel()) # XXX: Really?

    def test_donotresolvewholeforktogetonething(self):
        scope = Scope()
        with Repl(scope) as repl:
            repl('namespace')
            repl('  thing = $(namespace other)')
            repl('  other = data')
        self.assertEqual('data', scope.resolved('namespace', 'thing').unravel())

    def test_star(self):
        scope = Scope()
        with Repl(scope) as repl:
            repl('hmm * woo = yay')
            repl('hmm item woo = itemYay')
            repl('hmm item2 x = y')
            repl("hmm $.(*) woo2 = yay2")
        ae = self.assertEqual
        ae({'woo': 'yay', 'x': 'y'}, scope.resolved('hmm', 'item2').unravel())
        ae({'woo': 'yay', 'woo2': 'yay2'}, scope.resolved('hmm', '*').unravel())
        ae({'woo': 'itemYay'}, scope.resolved('hmm', 'item').unravel())
        items = scope.resolved('hmm').unravel()
        ae('itemYay', items['item']['woo'])
        ae('y', items['item2']['x'])
        ae('yay2', items['*']['woo2'])
        ae('yay', items['item2']['woo'])
        ae('yay', items['*']['woo'])

    def _star23(self, update):
        s = Scope()
        with Repl(s) as repl:
            if not update:
                repl('hmm * woo yay = houpla')
            repl('hmm item1 x = y')
            repl('hmm item2 woo = notyay')
            repl('hmm item3 woo yay = override')
            repl('hmm item4 woo Else = other')
            if update:
                repl('hmm * woo yay = houpla')
        ae = self.assertEqual
        ae(dict(woo = dict(yay = 'houpla'), x = 'y'), s.resolved('hmm', 'item1').unravel())
        ae(dict(yay = 'houpla'), s.resolved('hmm', 'item1', 'woo').unravel())
        ae('houpla', s.resolved('hmm', 'item1', 'woo', 'yay').unravel())
        ae(dict(woo = 'notyay'), s.resolved('hmm', 'item2').unravel())
        ae('notyay', s.resolved('hmm', 'item2', 'woo').unravel())
        ae(dict(woo = dict(yay = 'override')), s.resolved('hmm', 'item3').unravel())
        ae(dict(yay = 'override'), s.resolved('hmm', 'item3', 'woo').unravel())
        ae('override', s.resolved('hmm', 'item3', 'woo', 'yay').unravel())
        ae(dict(woo = dict(yay = 'houpla', Else = 'other')), s.resolved('hmm', 'item4').unravel())
        ae(dict(yay = 'houpla', Else = 'other'), s.resolved('hmm', 'item4', 'woo').unravel())
        ae('houpla', s.resolved('hmm', 'item4', 'woo', 'yay').unravel())
        ae('other', s.resolved('hmm', 'item4', 'woo', 'Else').unravel())

    def test_star2(self):
        self._star23(False)

    def test_star3(self):
        self._star23(True)

    def test_longstar(self):
        s = Scope()
        with Repl(s) as repl:
            repl('a * b c d = e')
            repl('a x f = g')
        ae = self.assertEqual
        ae(dict(f = 'g', b = dict(c = dict(d = 'e'))), s.resolved('a', 'x').unravel())
        ae(dict(c = dict(d = 'e')), s.resolved('a', 'x', 'b').unravel())
        ae(dict(d = 'e'), s.resolved('a', 'x', 'b', 'c').unravel())
        ae('e', s.resolved('a', 'x', 'b', 'c', 'd').unravel())

    def test_doublestar(self): # TODO: Lots more to test here.
        s = Scope()
        with Repl(s) as repl:
            repl('a * * b c = d')
            repl('a x f = g')
        ae = self.assertEqual
        ae(dict(f = 'g'), s.resolved('a', 'x').unravel())
        ae('g', s.resolved('a', 'x', 'f').unravel())

    def test_shortstar(self):
        s = Scope()
        with Repl(s) as repl:
            repl('a * b = c')
            repl('a x d e = f')
        ae = self.assertEqual
        ae(dict(b = 'c', d = dict(e = 'f')), s.resolved('a', 'x').unravel())
        ae(dict(e = 'f'), s.resolved('a', 'x', 'd').unravel())
        ae('f', s.resolved('a', 'x', 'd', 'e').unravel())

    def test_relmod(self):
        scope = Scope()
        with Repl(scope) as repl:
            repl('ns * stuff = $(woo) there')
            repl('ns item woo = yay')
        ae = self.assertEqual
        ae({'stuff': 'yay there', 'woo': 'yay'}, scope.resolved('ns', 'item').unravel())
        ae({'item': {'stuff': 'yay there', 'woo': 'yay'}}, scope.resolved('ns').unravel())
        ae('yay there', scope.resolved('ns', 'item', 'stuff').unravel())

    def test_relmod2(self):
        scope = Scope()
        with Repl(scope) as repl:
            repl('ns my.key = value')
            repl('ns item woo = $(my.key)')
        ae = self.assertEqual
        ae({'item': {'woo': 'value'}, 'my.key': 'value'}, scope.resolved('ns').unravel())
        ae({'woo': 'value'}, scope.resolved('ns', 'item').unravel())
        ae('value', scope.resolved('ns', 'item', 'woo').unravel())

    def test_relmod3(self):
        scope = Scope()
        with Repl(scope) as repl:
            repl('ns my key = value')
            repl('ns item woo = $(my key)')
        ae = self.assertEqual
        ae({'item': {'woo': 'value'}, 'my': {'key': 'value'}}, scope.resolved('ns').unravel())
        ae({'woo': 'value'}, scope.resolved('ns', 'item').unravel())
        ae('value', scope.resolved('ns', 'item', 'woo').unravel())

    def test_relmod4(self):
        scope = Scope()
        with Repl(scope) as repl:
            repl('woo port = 102')
            repl('yay * port = 100')
            repl('yay 0 x = 0')
            repl('yay 1 x = 1')
            repl('yay 2 x = 2')
            repl('yay 1 port = 101')
            repl('yay 2 port = $(woo port)')
        ae = self.assertEqual
        ae({'0': {'x': 0, 'port': 100}, '1': {'x': 1, 'port': 101}, '2': {'x': 2, 'port': 102}}, scope.resolved('yay').unravel())
        ae({'x': 2, 'port': 102}, scope.resolved('yay', '2').unravel())
        ae(102, scope.resolved('yay', '2', 'port').unravel())

    def test_nestedinclude(self):
        scope = Scope()
        with NamedTemporaryFile() as f:
            f.write('\t\n\nwoo = yay'.encode()) # Blank lines should be ignored.
            f.flush()
            with Repl(scope) as repl:
                repl.printf("ns . %s", f.name)
        ae = self.assertEqual
        ae({'ns': {'woo': 'yay'}}, scope.resolved().unravel())
        ae({'woo': 'yay'}, scope.resolved('ns').unravel())
        ae('yay', scope.resolved('ns', 'woo').unravel())

    def test_anonymouslistelements(self):
        scope = Scope()
        with Repl(scope) as repl:
            repl('woo += yay')
            repl('woo += $(houpla  )')
            repl('houpla = x')
        ae = self.assertEqual
        ae(['yay', 'x'], scope.resolved('woo').unravel())

    def test_anonymouslistelements2(self):
        scope = Scope()
        with Repl(scope) as repl:
            repl('woo += yay 1')
            repl('woo += yay  $[two]')
            repl('two = 2')
        ae = self.assertEqual
        ae(['yay 1', 'yay  2'], scope.resolved('woo').unravel())

    def test_thisusedtowork(self):
        scope = Scope()
        with Repl(scope) as repl:
            repl('x paths += woo')
            repl('x paths += yay')
            repl('y paths = $(x paths)')
        ae = self.assertEqual
        ae(['woo', 'yay'], scope.resolved('y', 'paths').unravel())

    def test_commandarg(self):
        base = Scope()
        with Repl(base) as repl:
            repl('my command = do $(arg)')
        tmp = base.createchild()
        with Repl(tmp) as repl:
            repl('arg = myval')
        # Doesn't matter where my command was found, it should be resolved against tmp:
        self.assertEqual('do myval', tmp.resolved('my', 'command').unravel())
        self.assertEqual(['do', 'myval'], tmp.resolved('my', 'command', aslist = True).unravel())

    def test_overridetwowordpath(self):
        s = Scope()
        with Repl(s) as repl:
            repl('calc.single = 5')
            repl('calc.double = $mul($(calc.single) 2)')
            repl('X = $fork()')
            repl('A calc.single = 6')
        self.assertEqual(10, s.resolved('X', 'calc.double').scalar)
        self.assertEqual(12, s.resolved('A', 'calc.double').scalar)
        s = Scope()
        with Repl(s) as repl:
            repl('calc single = 5')
            repl('calc double = $mul($(single) 2)')
            repl('X = $fork()')
            repl('A calc single = 6')
        self.assertEqual(10, s.resolved('X', 'calc' ,'double').scalar)
        self.assertEqual(12, s.resolved('A', 'calc', 'double').scalar)
        s = Scope()
        with Repl(s) as repl:
            repl('calc single = 5')
            repl('calc double = $mul($(calc single) 2)') # The calc here is redundant.
            repl('X = $fork()')
            repl('A calc single = 6')
        self.assertEqual(10, s.resolved('X', 'calc' ,'double').scalar)
        self.assertEqual(12, s.resolved('A', 'calc', 'double').scalar)

    def test_resolvepathinscope(self):
        s = Scope()
        with Repl(s) as repl:
            repl('x y = $(z)') # The resolvable.
            repl('z = 0')
            repl('A z = 1')
            repl('B z = 2')
            repl('A B z = 3')
            repl('A B x z = 4')
            repl('B C z = 5')
            repl('C z = 6')
        self.assertEqual(4, s.resolved('A', 'B', 'x', 'y').scalar)
        self.assertEqual(3, s.resolved('A', 'B', 'C', 'x', 'y').scalar)

    def test_blanklines(self):
        scope = Scope()
        with Repl(scope) as repl:
            repl('')
            repl('woo = yay')
            repl('')
            repl('woo2 = yay2')
            repl('')
        self.assertEqual({'woo': 'yay', 'woo2': 'yay2'}, scope.resolved().unravel())

    def test_try(self):
        scope = Scope()
        with Repl(scope) as repl:
            repl('woo = yay1')
            repl('yay1 = $try($(woo) yay2)')
            repl('yay2 = $try($(xxx) yay2)')
        self.assertEqual('yay1', scope.resolved('yay1').unravel())
        self.assertEqual('yay2', scope.resolved('yay2').unravel())

    def test_findpath(self):
        scope = Scope()
        with Repl(scope) as repl:
            repl('root')
            repl('\tparent bar = x')
            repl('\teranu')
            repl('\t\tparent foo = e')
            repl('\tuvavu')
            repl('\t\tparent foo = u')
        self.assertEqual('e', scope.resolved('root', 'eranu', 'parent', 'foo').unravel())
        self.assertEqual('u', scope.resolved('root', 'uvavu', 'parent', 'foo').unravel())
        self.assertEqual('x', scope.resolved('root', 'parent', 'bar').unravel())
        self.assertEqual('x', scope.resolved('root', 'eranu', 'parent', 'bar').unravel())
        self.assertEqual('x', scope.resolved('root', 'uvavu', 'parent', 'bar').unravel())

    def test_moreobviouspath(self):
        s = Scope()
        with Repl(s) as repl:
            repl('reference')
            repl('  myaccount')
            repl('    accountname = YES!')
            repl('  quotedname = "$(accountname)"')
            repl('config')
            repl('  quotedname = "NO!!"')
            repl('  item = $(reference myaccount quotedname)')
        self.assertEqual('"YES!"', s.resolved('config', 'item').scalar)

    def test_hereandindentfailure(self):
        s = Scope()
        for name in StaticScope.stacktypes:
            with self.assertRaises(NoSuchPathException):
                s.resolved(name)

    def test_appendtolistinsubscope(self):
        s = Scope()
        with Repl(s) as repl:
            repl('v := $list(x)')
            repl('v += y')
        d = s.createchild()
        self.assertEqual(['x', 'y'], d.resolved('v').unravel()) # Good, same as parent.
        with Repl(d) as repl:
            repl('v += z')
        self.assertEqual(['x', 'y'], s.resolved('v').unravel()) # Good, we should not modify parent.
        self.assertEqual(['z'], d.resolved('v').unravel()) # Makes sense maybe.

    def test_appendtolistinsubscope2(self):
        s = Scope()
        with Repl(s) as repl:
            repl('u v := $list(x)')
            repl('u v += y')
        d = s.createchild()
        self.assertEqual(['x', 'y'], d.resolved('u', 'v').unravel())
        with Repl(d) as repl:
            repl('u v += z')
        self.assertEqual(['x', 'y'], s.resolved('u', 'v').unravel())
        self.assertEqual(['z'], d.resolved('u', 'v').unravel())

    def test_poison(self):
        s = Scope()
        with Repl(s) as repl:
            repl('woo = yay')
        d = s.createchild()
        self.assertEqual('yay', d.resolved('woo').scalar)
        with Repl(d) as repl:
            repl('woo = $(void)')
        self.assertEqual('yay', s.resolved('woo').scalar)
        with self.assertRaises(NoSuchPathException):
            d.resolved('woo')

    def test_poison2(self):
        s = Scope()
        with Repl(s) as repl:
            repl('u woo = yay')
        d = s.createchild()
        self.assertEqual('yay', d.resolved('u', 'woo').scalar)
        with Repl(d) as repl:
            repl('u woo = $(void)')
        self.assertEqual('yay', s.resolved('u', 'woo').scalar)
        with self.assertRaises(NoSuchPathException):
            d.resolved('u', 'woo')

    def test_fullpathtrick(self):
        s = Scope()
        with Repl(s) as repl:
            repl('full_path = $/($(base path) $(path))')
            repl('base path = opt')
            repl('icon path = icon.png')
        self.assertEqual(os.path.join('opt', 'icon.png'), s.resolved('icon', 'full_path').scalar)

    def test_fullpathtrick2(self):
        s = Scope()
        with Repl(s) as repl:
            repl('full path = $/($(base path) $(path))') # XXX: Surprising that this works?
            repl('base path = opt')
            repl('icon path = icon.png')
        self.assertEqual(os.path.join('opt', 'icon.png'), s.resolved('icon', 'full', 'path').scalar)

    def test_bake(self):
        s = Scope()
        with Repl(s) as repl:
            repl('v += 1')
            repl('v := $(v)')
            repl('a w += 2')
            repl('a w := $(w)')
        self.assertEqual([1], s.resolved('v').unravel())
        self.assertEqual([2], s.resolved('a', 'w').unravel())

    def test_longref(self):
        s = Scope()
        with Repl(s) as repl:
            repl('x dbl = $(name)$(name)')
            repl('x y name = Y')
            repl('ok = $(x y dbl)')
            repl('wtf k = $(x y dbl)')
        self.assertEqual('YY', s.resolved('x', 'y', 'dbl').scalar)
        self.assertEqual('YY', s.resolved('ok').unravel())
        self.assertEqual('YY', s.resolved('wtf', 'k').unravel())
        self.assertEqual({'k': 'YY'}, s.resolved('wtf').unravel())

    def test_detectcycle(self):
        s = Scope()
        with Repl(s) as repl:
            repl('x = $(x)')
            repl('a = $(b)')
            repl('b = $(a)')
            repl('y z = $(y)')
        with self.assertRaises(CycleException) as cm:
            s.resolved('x')
        self.assertEqual((('x',),), cm.exception.args)
        with self.assertRaises(CycleException) as cm:
            s.resolved('a')
        self.assertEqual((('a',),), cm.exception.args)
        with self.assertRaises(CycleException) as cm:
            s.resolved('b')
        self.assertEqual((('b',),), cm.exception.args)
        self.assertIs(s.resolved('y'), s.resolved('y', 'z'))
