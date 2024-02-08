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
from .repl import Repl
from .scope import Scope
from .util import NoSuchPathException, openresource
from tempfile import NamedTemporaryFile
from unittest import TestCase
import os

class TestDirectives(TestCase):

    def test_commentprecedence(self):
        cc = ConfigCtrl()
        with cc.repl() as repl:
            repl('woo = before')
            repl('houpla3 = 3')
            repl(':')
            repl(': woo')
            repl(': woo = during') # Not executed.
            repl('houpla1 = 1 : woo = during') # Only first phrase is executed.
            repl('houpla2 = 2 : houpla3 = 4 : woo = during') # Same, second colon is part of comment.
            repl('yay := $(woo)')
            repl('woo = after')
        c = cc.node
        ae = self.assertEqual
        ae('before', c.yay)
        ae('after', c.woo)
        ae(1, c.houpla1)
        ae(2, c.houpla2)
        ae(3, c.houpla3)

    def test_equalsprecedence(self):
        cc = ConfigCtrl()
        with cc.repl() as repl:
            repl('woo = before')
            repl('woo = and = after') # Apply first equals less astonishing than error or applying second.
        c = cc.node
        ae = self.assertEqual
        ae('and = after', c.woo)

    def test_starprecedence(self):
        cc = ConfigCtrl()
        with cc.repl() as repl:
            repl('woo = yay * houpla') # Would be very confusing for * to have precedence here.
        c = cc.node
        ae = self.assertEqual
        ae('yay * houpla', c.woo)

    def test_sourcecommentwithprefix(self):
        cc = ConfigCtrl()
        with NamedTemporaryFile('w') as f, cc.repl() as repl:
            f.write('woo = yay\n')
            f.write('woo2 = yay2 : with comment\n')
            f.write(': comment only\n')
            f.flush()
            repl.printf("prefix . %s", f.name)
        c = cc.node
        ae = self.assertEqual
        ae('yay', c.prefix.woo)
        ae('yay2', c.prefix.woo2)

    def test_starmultiplechildren(self):
        cc = ConfigCtrl()
        cc.printf('a = A')
        cc.printf('b = B')
        cc.printf('profile * a = $(void)')
        cc.printf('profile * b = $(void)')
        cc.printf('profile p x = y')
        c = cc.node
        with self.assertRaises(AttributeError):
            c.profile.p.a
        with self.assertRaises(AttributeError):
            c.profile.p.b
        self.assertEqual('y', c.profile.p.x)

    def test_starishidden(self):
        c = ConfigCtrl().node
        (-c).printf('x * y = z')
        self.assertEqual({}, (-c.x).scope().unravel())
        self.assertEqual([], list(-c.x))
        (-c).printf('x a = b')
        self.assertEqual(dict(a = 'b'), (-c.x).scope().unravel())
        self.assertEqual([('a', 'b')], list(-c.x))
        (-c).printf('x p q = r')
        self.assertEqual(dict(a = 'b', p = dict(q = 'r', y = 'z')), (-c.x).scope().unravel())

    def test_nesteddynamicinclude(self):
        s = Scope()
        with NamedTemporaryFile('w') as f, Repl(s) as repl:
            f.write('woo = yay')
            f.flush()
            repl.printf("app confpath = %s", f.name)
            repl('app . $(confpath)')
        self.assertEqual('yay', s.resolved('app', 'woo').textvalue)

    def test_merge(self):
        class Ctrl(ConfigCtrl):
            def loadsettings(self):
                with openresource(__name__, 'test_directives/merge/settings.arid') as f:
                    self.load(f)
        c = Ctrl().loadappconfig((__name__, 'app'), 'test_directives/merge/appconf.arid')
        self.assertEqual('default0', c.optional.zero)
        self.assertEqual('appopt1', c.optional.one)
        self.assertEqual('default2', c.optional.two)
        with self.assertRaises(AttributeError):
            c.required.zero
        self.assertEqual('appreq1', c.required.one)
        with self.assertRaises(AttributeError):
            c.required.two
        self.assertEqual('app', (-c).scope().label.scalar)
        self.assertEqual(50, c.relref)
        self.assertEqual(100, c.absref)
        c = (-Ctrl().loadappconfig((__name__, 'app'), 'test_directives/merge/altconf.arid')).reapplysettings('alt')
        self.assertEqual('default0', c.optional.zero)
        self.assertEqual('appopt1', c.optional.one)
        self.assertEqual('altopt2', c.optional.two)
        with self.assertRaises(AttributeError):
            c.required.zero
        self.assertEqual('appreq1', c.required.one)
        self.assertEqual('altreq2', c.required.two)
        self.assertEqual('alt', (-c).scope().label.scalar)
        self.assertEqual(70, c.relref)
        self.assertEqual(110, c.absref)

    def test_cd(self):
        assert '/' == os.sep
        cc = ConfigCtrl()
        with self.assertRaises(NoSuchPathException) as cm:
            cc.execute('!cd woo')
        self.assertEqual((('cwd',),), cm.exception.args)
        cc.execute('!cd /woo')
        c = cc.node
        self.assertEqual('/woo', c.cwd)
        cc.execute('!cd yay')
        self.assertEqual('/woo/yay', c.cwd)
        c.cwd = 'woo'
        cc.execute('!cd yay')
        self.assertEqual('woo/yay', c.cwd)
        cc.execute('!cd /houpla')
        self.assertEqual('/houpla', c.cwd)
