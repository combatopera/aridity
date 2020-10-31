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
from .functions import Spread
from .model import Boolean, Function, Number, Scalar, Text
from io import StringIO
from unittest import TestCase
import os

class TestConfig(TestCase):

    def test_listdict(self):
        c = ConfigCtrl().node
        (-c).put('v', 'a', text = 'A')
        self.assertEqual(['A'], list(c.v))
        self.assertEqual(dict(a = 'A'), dict(-c.v))
        (-c).put('v', 'b', text = 'B')
        self.assertEqual(['A', 'B'], list(c.v))
        self.assertEqual(dict(a = 'A', b = 'B'), dict(-c.v))
        (-c).put('v', 'c', 'x', text = 'X')
        l = list(c.v)
        self.assertEqual(3, len(l))
        self.assertEqual('A', l[0])
        self.assertEqual('B', l[1])
        self.assertEqual(['X'], list(l[2]))
        self.assertEqual(dict(x = 'X'), dict(-l[2]))
        d = dict(-c.v)
        self.assertEqual(set('abc'), set(d.keys()))
        self.assertEqual('A', d['a'])
        self.assertEqual('B', d['b'])
        self.assertEqual(['X'], list(d['c']))
        self.assertEqual(dict(x = 'X'), dict(-d['c']))

    def test_printf(self):
        c = ConfigCtrl().node
        (-c).printf('woo a = b')
        (-c.woo).printf('c = d')
        self.assertEqual(['b', 'd'], list(c.woo))
        self.assertEqual(dict(a = 'b', c = 'd'), dict(-c.woo))
        self.assertEqual(dict(a = 'b', c = 'd'), (-c.woo).context().unravel())

    def test_crosschildresolve(self):
        cc = ConfigCtrl()
        cc.printf('app xform = <$(data)>')
        cc.printf('app item data = woo')
        c = cc.node.app
        self.assertEqual(['app'], (-c).prefix)
        self.assertEqual('<woo>', c.item.xform)
        f = (-c).free().node
        self.assertEqual([], (-f).prefix)
        self.assertEqual('<woo>', f.item.xform)
        h = (-c).createchild().node
        self.assertEqual([], (-h).prefix)
        self.assertEqual('<woo>', h.item.xform)

    def test_tailmoresignificant(self):
        cc = ConfigCtrl()
        cc.printf('X Y := $fork()')
        cc.printf('Y Z = woo')
        cc.printf('Z = yay')
        c = cc.node
        self.assertEqual('woo', c.X.Y.Z)
        f = (-c.X.Y).free().node
        self.assertEqual('yay', f.Z)

    def test_multibacktrack(self):
        cc = ConfigCtrl()
        cc.printf('A = woo')
        cc.printf('B C := $fork()')
        cc.printf('D E F := $fork()')
        c = cc.node
        self.assertEqual('woo', c.A)
        self.assertEqual('woo', c.B.A)
        self.assertEqual('woo', c.D.A)
        self.assertEqual('woo', c.B.C.A)
        self.assertEqual('woo', c.D.E.A)
        self.assertEqual('woo', c.D.E.F.A)
        self.assertEqual('woo', c.D.E.F.B.C.A)

    def test_appnamelabel(self):
        c = ConfigCtrl()._loadappconfig('The App', StringIO(u'n := $label()\nx y = $(n)'))
        self.assertEqual('The App', c.n)
        self.assertEqual('The App', c.x.y)

    def test_setattr(self):
        cc = ConfigCtrl()
        cc.node.p = 'yay'
        cc.node.q = 100
        cc.node.r = True
        cc.node.s = False
        cc.node.t = None
        cc.node.u = ord
        obj = cc.context().resolved('p')
        self.assertEqual(Text, type(obj))
        self.assertEqual('yay', obj.unravel())
        obj = cc.context().resolved('q')
        self.assertEqual(Number, type(obj))
        self.assertEqual(100, obj.unravel())
        obj = cc.context().resolved('r')
        self.assertEqual(Boolean, type(obj))
        self.assertIs(True, obj.unravel())
        obj = cc.context().resolved('s')
        self.assertEqual(Boolean, type(obj))
        self.assertIs(False, obj.unravel())
        obj = cc.context().resolved('t')
        self.assertEqual(Scalar, type(obj))
        self.assertIs(None, obj.unravel())
        obj = cc.context().resolved('u')
        self.assertEqual(Function, type(obj))
        self.assertIs(ord, obj.unravel())

    def test_multiscalar(self):
        cc = ConfigCtrl()
        cc.printf('a = $(/)')
        cc.printf('b = $(*)')
        c = cc.node
        self.assertEqual(os.sep, c.a)
        self.assertEqual(os.sep, getattr(c, '/'))
        obj = cc.context().resolved('/')
        self.assertEqual(os.sep, obj.textvalue)
        self.assertEqual(os.sep, obj.value)
        self.assertEqual(os.sep, obj.unravel())
        self.assertNotEqual(os.sep, obj.functionvalue)
        self.assertEqual(Spread.of, c.b)
        self.assertEqual(Spread.of, getattr(c, '*'))
        obj = cc.context().resolved('*')
        self.assertEqual(Spread.of, obj.functionvalue)
        self.assertEqual(Spread.of, obj.value)
        self.assertEqual(Spread.of, obj.unravel())
        self.assertNotEqual(Spread.of, obj.directivevalue)
