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

from .context import Scope
from .repl import MalformedEntryException, NoSuchIndentException, Repl
from .util import UnsupportedEntryException
from decimal import Decimal
from unittest import TestCase

class TestRepl(TestCase):

    def test_indent(self):
        scope = Scope()
        with Repl(scope) as repl:
            repl('namespace')
            repl('  woo = 1')
            repl('  yay = 2')
            repl('ns2 woo')
            repl('\tyay = x')
            repl('ns3')
            repl(' woo')
            repl(' \tyay = z')
            repl(' houpla = w')
        ae = self.assertEqual
        ae({'woo': 1, 'yay': 2}, scope.resolved('namespace').unravel())
        ae({'woo': {'yay': 'x'}}, scope.resolved('ns2').unravel())
        ae({'yay': 'z'}, scope.resolved('ns3', 'woo').unravel())
        ae({'woo': {'yay': 'z'}, 'houpla': 'w'}, scope.resolved('ns3').unravel())

    def test_nosuchindent(self):
        scope = Scope()
        with Repl(scope) as repl:
            repl('ns')
            repl('  x')
            repl('    x2 = y2')
            repl('ns2')
            repl('    a = b')
            with self.assertRaises(NoSuchIndentException):
                repl('  uh = oh')

    def test_unusedprefix(self):
        scope = Scope()
        with self.assertRaises(UnsupportedEntryException):
            with Repl(scope) as repl:
                repl('prefix')

    def test_multilineprefix(self):
        scope = Scope()
        with Repl(scope) as repl:
            repl('name$.(\n')
            repl('  space)')
            repl(' woo = yay')
        self.assertEqual({'woo': 'yay'}, scope.resolved('name\n  space').unravel())

    def test_badindent(self):
        scope = Scope()
        with Repl(scope) as repl:
            repl('ns')
            repl('  ns2')
            with self.assertRaises(UnsupportedEntryException):
                repl('  woo = yay')
            repl('   woo = yay')

    def test_badindent2(self):
        scope = Scope()
        with Repl(scope) as repl:
            repl('ns')
            repl('\tns2')
            with self.assertRaises(MalformedEntryException):
                repl('  woo = yay')
            repl('\t woo = yay')

    def test_printf(self):
        scope = Scope()
        with Repl(scope) as repl:
            repl.printf("val = %s", 100)
            repl.printf("val2 = %s", .34)
            repl.printf("text = %s", 'hello')
            repl.printf("empty = %s", '')
            repl.printf("dot = %s", '.')
            repl.printf("eq 0 als = %s", '=')
            repl.printf("path = $(eq %s %s)", 0, 'als')
        self.assertEqual(100, scope.resolved('val').scalar)
        self.assertEqual(Decimal('.34'), scope.resolved('val2').scalar)
        self.assertEqual('hello', scope.resolved('text').scalar)
        self.assertEqual('', scope.resolved('empty').scalar)
        self.assertEqual('.', scope.resolved('dot').scalar)
        self.assertEqual('=', scope.resolved('eq', '0', 'als').scalar)
        self.assertEqual('=', scope.resolved('path').scalar)
        self.assertEqual({'val': 100, 'val2': Decimal('.34'), 'text': 'hello', 'empty': '', 'dot': '.', 'eq': {'0': {'als': '='}}, 'path': '='}, scope.unravel())

    def test_printfbool(self):
        c = Scope()
        with Repl(c) as repl:
            repl.printf("zero = %s", 0)
            repl.printf("one = %s", 1)
            repl.printf("f = %s", False)
            repl.printf("t = %s", True)
        zero = c.resolved('zero').scalar
        self.assertEqual(0, zero)
        self.assertIsNot(False, zero)
        one =  c.resolved('one').scalar
        self.assertEqual(1, one)
        self.assertIsNot(True, one)
        self.assertIs(False, c.resolved('f').scalar)
        self.assertIs(True, c.resolved('t').scalar)

    def test_printfpath(self):
        try:
            from pathlib import Path
        except ImportError:
            return
        scope = Scope()
        with Repl(scope) as repl:
            repl.printf("ddot = %s", Path('..'))
            repl.printf("dot = %s", Path('.'))
        # XXX: Preserve type?
        self.assertEqual('..', scope.resolved('ddot').scalar)
        self.assertEqual('.', scope.resolved('dot').scalar)

    def test_printf2(self):
        a = ' hello\nthere\ragain\t'
        b = ' \nhello\n\rthere\r\nagain \t'
        scope = Scope()
        with Repl(scope) as repl:
            repl.printf("a = %s", a)
            repl.printf("b = %s", b)
        self.assertEqual(a, scope.resolved('a').scalar)
        self.assertEqual(b, scope.resolved('b').scalar)

    def test_printf3(self):
        scope = Scope()
        with Repl(scope) as repl:
            repl.printf("a = %s", 'x)y')
            repl.printf("b = %s", 'x]y')
        self.assertEqual('x)y', scope.resolved('a').scalar)
        self.assertEqual('x]y', scope.resolved('b').scalar)

    def test_printfbadliteral(self):
        c = Scope()
        with self.assertRaises(TypeError), Repl(c) as repl:
            repl.printf('template = %s')
        with Repl(c) as repl:
            repl.printf('template = %%s')
        self.assertEqual('%s', c.resolved('template').scalar)
