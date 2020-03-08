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

from .context import Context
from .repl import MalformedEntryException, NoSuchIndentException, Repl
from .util import UnsupportedEntryException
from decimal import Decimal
import unittest

class TestRepl(unittest.TestCase):

    def test_indent(self):
        context = Context()
        with Repl(context) as repl:
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
        ae({'woo': 1, 'yay': 2}, context.resolved('namespace').unravel())
        ae({'woo': {'yay': 'x'}}, context.resolved('ns2').unravel())
        ae({'yay': 'z'}, context.resolved('ns3', 'woo').unravel())
        ae({'woo': {'yay': 'z'}, 'houpla': 'w'}, context.resolved('ns3').unravel())

    def test_nosuchindent(self):
        context = Context()
        with Repl(context) as repl:
            repl('ns')
            repl('  x')
            repl('    x2 = y2')
            repl('ns2')
            repl('    a = b')
            with self.assertRaises(NoSuchIndentException):
                repl('  uh = oh')

    def test_unusedprefix(self):
        context = Context()
        with self.assertRaises(UnsupportedEntryException):
            with Repl(context) as repl:
                repl('prefix')

    def test_multilineprefix(self):
        context = Context()
        with Repl(context) as repl:
            repl('name$.(\n')
            repl('  space)')
            repl(' woo = yay')
        self.assertEqual({'woo': 'yay'}, context.resolved('name\n  space').unravel())

    def test_badindent(self):
        context = Context()
        with Repl(context) as repl:
            repl('ns')
            repl('  ns2')
            with self.assertRaises(UnsupportedEntryException):
                repl('  woo = yay')
            repl('   woo = yay')

    def test_badindent2(self):
        context = Context()
        with Repl(context) as repl:
            repl('ns')
            repl('\tns2')
            with self.assertRaises(MalformedEntryException):
                repl('  woo = yay')
            repl('\t woo = yay')

    def test_printf(self):
        context = Context()
        with Repl(context) as repl:
            repl.printf("val = %s", 100)
            repl.printf("val2 = %s", .34)
            repl.printf("text = %s", 'hello')
            repl.printf("empty = %s", '')
            repl.printf("dot = %s", '.')
            repl.printf("eq 0 als = %s", '=')
            repl.printf("path = $(eq %s %s)", 0, 'als')
        self.assertEqual(100, context.resolved('val').value)
        self.assertEqual(Decimal('.34'), context.resolved('val2').value)
        self.assertEqual('hello', context.resolved('text').value)
        self.assertEqual('', context.resolved('empty').value)
        self.assertEqual('.', context.resolved('dot').value)
        self.assertEqual('=', context.resolved('eq', '0', 'als').value)
        self.assertEqual('=', context.resolved('path').value)
        self.assertEqual({'val': 100, 'val2': Decimal('.34'), 'text': 'hello', 'empty': '', 'dot': '.', 'eq': {'0': {'als': '='}}, 'path': '='}, context.unravel())

    def test_printfpath(self):
        try:
            from pathlib import Path
        except ImportError:
            return
        context = Context()
        with Repl(context) as repl:
            repl.printf("ddot = %s", Path('..'))
            repl.printf("dot = %s", Path('.'))
        # XXX: Preserve type?
        self.assertEqual('..', context.resolved('ddot').value)
        self.assertEqual('.', context.resolved('dot').value)

    def test_printf2(self):
        a = ' hello\nthere\ragain\t'
        b = ' \nhello\n\rthere\r\nagain \t'
        context = Context()
        with Repl(context) as repl:
            repl.printf("a = %s", a)
            repl.printf("b = %s", b)
        self.assertEqual(a, context.resolved('a').value)
        self.assertEqual(b, context.resolved('b').value)

    def test_printf3(self):
        context = Context()
        with Repl(context) as repl:
            repl.printf("a = %s", 'x)y')
            repl.printf("b = %s", 'x]y')
        self.assertEqual('x)y', context.resolved('a').value)
        self.assertEqual('x]y', context.resolved('b').value)
