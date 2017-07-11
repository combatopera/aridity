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
from .context import Context
from .repl import Repl, NoSuchIndentException, MalformedEntryException
from .util import UnsupportedEntryException

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
