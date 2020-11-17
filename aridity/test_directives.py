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
from .context import Context
from .repl import Repl
from tempfile import mkdtemp, NamedTemporaryFile
from unittest import TestCase
import os, shutil

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
        self.assertEqual({}, (-c.x).context().unravel())
        self.assertEqual([], list(-c.x))
        (-c).printf('x a = b')
        self.assertEqual(dict(a = 'b'), (-c.x).context().unravel())
        self.assertEqual([('a', 'b')], list(-c.x))
        (-c).printf('x p q = r')
        self.assertEqual(dict(a = 'b', p = dict(q = 'r', y = 'z')), (-c.x).context().unravel())

    def test_nesteddynamicinclude(self):
        c = Context()
        with NamedTemporaryFile('w') as f, Repl(c) as repl:
            f.write('woo = yay')
            f.flush()
            repl.printf("app confpath = %s", f.name)
            repl('app . $(confpath)')
        self.assertEqual('yay', c.resolved('app', 'woo').textvalue)

    def test_merge(self):
        tempdir = mkdtemp()
        try:
            appconfpath = os.path.join(tempdir, 'appconf.arid')
            altconfpath = os.path.join(tempdir, 'altconf.arid')
            settingspath = os.path.join(tempdir, 'settings.arid')
            with open(appconfpath, 'w') as f:
                f.write('optional zero = default0\n')
                f.write('optional one = default1\n')
                f.write('optional two = default2\n')
                f.write('required zero = $(void)\n')
                f.write('required one = $(void)\n')
                f.write('required two = $(void)\n')
            with open(altconfpath, 'w') as f:
                f.write('. $./(appconf.arid)\n')
                # TODO: DRY way to steal app settings.
                f.write('optional one = $(app optional one)\n')
                f.write('optional two = $(app optional two)\n')
                f.write('required one = $(app required one)\n')
                f.write('required two = $(app required two)\n')
            with open(settingspath, 'w') as f:
                f.write('alt optional two = altopt2\n')
                f.write('alt required two = altreq2\n')
                f.write('app optional one = appopt1\n')
                f.write('app required one = appreq1\n')
            cc = ConfigCtrl()
            cc.execute('app := $fork()')
            c = cc.node.app
            (-c).load(appconfpath)
            cc.load(settingspath)
            self.assertEqual('default0', c.optional.zero)
            self.assertEqual('appopt1', c.optional.one)
            self.assertEqual('default2', c.optional.two)
            with self.assertRaises(AttributeError):
                c.required.zero
            self.assertEqual('appreq1', c.required.one)
            with self.assertRaises(AttributeError):
                c.required.two
            cc = ConfigCtrl()
            cc.execute('alt := $fork()')
            c = cc.node.alt
            (-c).load(altconfpath)
            cc.load(settingspath)
            self.assertEqual('default0', c.optional.zero)
            self.assertEqual('appopt1', c.optional.one)
            self.assertEqual('altopt2', c.optional.two)
            with self.assertRaises(AttributeError):
                c.required.zero
            self.assertEqual('appreq1', c.required.one)
            self.assertEqual('altreq2', c.required.two)
        finally:
            shutil.rmtree(tempdir)
