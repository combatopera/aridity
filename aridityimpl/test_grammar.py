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

import unittest, pyparsing, tempfile
from .parser import expressionparser as p, loader as l
from .grammar import Text, Call, Blank, Concat, Number, Boolean, Function, Entry, List, Boundary
from decimal import Decimal
from .context import Context, NoSuchPathException
from .directives import execute
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

class TestGrammar(unittest.TestCase):

    def test_parser(self):
        ae = self.assertEqual
        ae([Text('x')], p('x'))
        ae([Text('yy')], p('yy'))
        ae([Text('x'), Blank('  '), Text('y')], p('x  y'))
        ae([Blank('\t'), Text('x'), Blank('  '), Text('y'), Blank('\t')], p('\tx  y\t'))
        ae([Blank('\t'), Text('x'), Blank('  '), Text('y'), Boundary('\r')], p('\tx  y\r'))
        for text in ('$a()',
                     '$a[]'):
            ae([Call('a', [])], p(text))
        for text in ('$ac(x)',
                     '$ac[x]'):
            ae([Call('ac', [Text('x')])], p(text))
        for text in ('$act(x yy)',
                     '$act[x yy]'):
            ae([Call('act', [Text('x'), Blank(' '), Text('yy')])], p(text))
        for text in ('$act(\rx  yy\t)',
                     '$act[\rx  yy\t]'):
            ae([Call('act', [Blank('\r'), Text('x'), Blank('  '), Text('yy'), Blank('\t')])], p(text))
        for text in ('$act(\rx$b()z  yy\t)',
                     '$act(\rx$b[]z  yy\t)',
                     '$act[\rx$b[]z  yy\t]',
                     '$act[\rx$b()z  yy\t]'):
            ae([Call('act', [Blank('\r'), Concat([Text('x'), Call('b', []), Text('z')]), Blank('  '), Text('yy'), Blank('\t')])], p(text))
        ae([Text('woo')], p('woo'))
        ae([Concat([Text('woo'), Call('get', [Text('yay')]), Text('houpla')])], p('woo$get(yay)houpla'))
        ae([Text('woo'), Blank(' '), Call('get', [Blank('\n '), Text('yay'), Blank('\n')]), Blank('\t'), Text('houpla'), Blank('  ')], p('''woo $get(
 yay
)\thoupla  '''))
        ae([Number(1)], p('1'))
        ae([Number(-5)], p('-5'))
        ae([Call('id', [Number(Decimal('.1'))])], p('$id(.1)'))
        ae([Call('id', [Number(Decimal('-5.4'))])], p('$id(-5.4)'))
        ae([Call('id', [Text('.1woo')])], p('$id(.1woo)'))
        ae([Text('100woo')], p('100woo'))
        ae([Boolean(False)], p('false'))
        ae([Call('id', [Boolean(True)])], p('$id(true)'))
        ae([Call('id', [Text('falseyay')])], p('$id(falseyay)'))
        ae([Text('truewoo')], p('truewoo'))
        ae([Concat([Text('100'), Call('a', [])])], p('100$a()'))
        ae([Call('aaa', [Call('bbb', [Text('ccc)ddd')])])], p('$aaa($bbb[ccc)ddd])'))

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
        ae([Entry([Text('x'), Blank(' '), Text('='), Blank(' '), Call('a', [Blank('\n'), Text('b'), Blank('\r')])])], l('x = $a(\nb\r)'))

    def test_resolve(self):
        c = Context()
        for name, f in allfunctions(Functions):
            if name in ('a', 'ac', 'act', 'id'):
                c[name] = Function(f)
        c['minus124'] = Number(-124)
        c['minus124txt'] = Text('minus124')
        c['gett'], = p('$get(get)')
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

    def test_lit(self):
        ae = self.assertEqual
        ae([Text('$doesNotExist(]')], p('$lit($doesNotExist(])'))
        ae([Text('$doesNotExist[)')], p('$lit[$doesNotExist[)]'))
        ae([Text(' \t')], p('$lit[ \t]'))
        ae([Text('10')], p('$lit[10]'))

    def test_pass(self):
        ae = self.assertEqual
        ae([Concat([Text(' '), Text('x'), Text('  '), Text('y'), Text('\t')])], p('$pass( x  y\t)'))
        ae([Concat([Text(' '), Text('x'), Text('  '), Text('y'), Text('\t')])], p('$pass[ x  y\t]'))
        actual = p('$act(x $pass[ y\t])')
        ae([Call('act', [Text('x'), Blank(' '), Concat([Text(' '), Text('y'), Text('\t')])])], actual)
        c = Context()
        for name, f in allfunctions(Functions):
            if name in ('act',):
                c[name] = Function(f)
        ae(Text('act.x. y\t'), Concat(actual).resolve(c))
        ae([Text('10')], p('$pass[10]'))
        ae([Text('x('), Blank(' '), Text(')')], p('$pass(x() )'))
        ae([Concat([Text('x()'), Text(' ')])], p('$pass[x() ]'))
        ae(Text('act.x. '), Concat(p('$act(x $pass( ))')).resolve(c))
        ae(Text(' 100'), Concat(p('$pass( 100)')).resolve(c))

    def test_whitespace(self):
        ae = self.assertEqual
        ae([Blank(' '), Text(' x '), Blank(' ')], p(' $lit( x ) '))
        ae([Blank(' '), Concat([Text(' '), Text('x'), Text(' ')]), Blank(' ')], p(' $pass( x ) '))
        for name in 'lit', 'pass':
            for text in (' $ %s( x ) ' % name,
                         ' $%s ( x ) ' % name):
                with self.assertRaises(pyparsing.ParseException):
                    p(text)

    def test_map(self): # TODO: Also test 2-arg form.
        call, = p('$map($list(a b 0) x $str($get(x))2)')
        self.assertEqual(List([Text('a2'), Text('b2'), Text('02')]), call.resolve(Context()))

    def test_join(self):
        call, = p('$join($list(a bb ccc) -)')
        self.assertEqual(Text('a-bb-ccc'), call.resolve(Context()))

    def test_modifiers(self):
        self.modifiers('v = $list()\nv#one = $list()\nv#one#1 = $list()\nv#one#1#un = uno')

    def test_modifiers2(self):
        self.modifiers('v#one#1#un = uno')

    def modifiers(self, text):
        context = Context()
        for entry in l(text):
            execute(entry, context)
        ae = self.assertEqual
        ae(Text('uno'), context.resolved('v#one#1#un'))
        ae([Text('uno')], list(context.resolved('v#one#1')))
        ae([[Text('uno')]], [list(x) for x in context.resolved('v#one')])
        ae([[[Text('uno')]]], [[list(y) for y in x] for x in context.resolved('v')])

    def test_fork(self):
        self.fork('hmm = woo\nv = $list()\nv#one = $fork()\nv#one#1 = uno\nv#two = $fork()\n\r\r\nv#two#hmm = yay')

    def test_fork2(self):
        self.fork('hmm = woo\nv#one#1 = uno\n\r\r\nv#two#hmm = yay')

    def fork(self, text):
        context = Context()
        for entry in l(text):
            execute(entry, context)
        ae = self.assertEqual
        ae(Text('uno'), context.resolved('v#one#1'))
        ae(OrderedDict([('1', Text('uno'))]), context.resolved('v#one').objs)
        ae(OrderedDict([('hmm', Text('yay'))]), context.resolved('v#two').objs)
        ae(Text('woo'), context.resolved('v#one').resolved('hmm'))
        ae(Text('yay'), context.resolved('v#two').resolved('hmm'))
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

    def test_hmm(self):
        with tempfile.NamedTemporaryFile() as f, tempfile.NamedTemporaryFile() as g:
            f.write('''command = $list($pass($join$map($get(env) k v $get(k)=$get(v)$pass( ))$get(executable)))
programs#sc#executable = sclang
env = $fork()
''')
            f.flush()
            g.write('$join$map($get(programs) $join$map($get(command) w $get(w)))')
            g.flush()
            context = Context()
            with Repl(context) as repl:
                repl = repl.printf
                repl("source %s", f.name)
                repl("cat %s", g.name)
