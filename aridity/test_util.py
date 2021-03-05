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

from .config import ConfigCtrl
from .context import Scope
from .repl import Repl
from .util import ispy2, openresource, OrderedSet, TreeNoSuchPathException
from unittest import TestCase

class TestUtil(TestCase):

    def test_orderedset(self):
        s = OrderedSet()
        self.assertEqual(False, bool(s))
        s.add(2)
        self.assertEqual(True, bool(s))
        s.add(1)
        s.add(0)
        self.assertEqual([2, 1, 0], list(s)) # Order preserved.
        s.add(1)
        self.assertEqual([2, 1, 0], list(s)) # Order unchanged.

    def test_treeexceptionstr(self):
        s = Scope()
        with Repl(s) as repl:
            repl.printf('broken = $(void)')
            repl.printf('woo = $(broken)')
        with self.assertRaises(TreeNoSuchPathException) as cm:
            s.resolved('broken')
        self.assertEqual('broken\n2x void', str(cm.exception))
        with self.assertRaises(TreeNoSuchPathException) as cm:
            s.resolved('woo')
        self.assertEqual('woo\n1x broken\n    2x void\n1x broken', str(cm.exception))

    def test_treeexceptionstr2(self):
        if ispy2:
            return
        cc = ConfigCtrl()
        cc.printf('broken = $(void)')
        cc.printf('woo = $(broken)')
        c = cc.node
        with self.assertRaises(AttributeError) as cm:
            c.broken
        self.assertEqual('broken\n2x void', str(cm.exception.__context__))
        with self.assertRaises(AttributeError) as cm:
            c.woo
        self.assertEqual('woo\n1x broken\n    2x void\n1x broken', str(cm.exception.__context__))

    def test_openresource(self):
        with openresource(__name__, 'test_util/resource.utf8', 'utf-8') as f:
            self.assertEqual(u'\N{POUND SIGN}\n', f.read())
        with openresource(__name__, 'test_util/resource.utf8') as f, self.assertRaises(UnicodeDecodeError):
            f.read()
