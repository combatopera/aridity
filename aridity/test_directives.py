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

from .config import Config
from tempfile import NamedTemporaryFile
from unittest import TestCase

class TestDirectives(TestCase):

    def test_commentprecedence(self):
        c = Config.blank()
        with c.repl() as repl:
            repl('woo = before')
            repl('houpla3 = 3')
            repl(':')
            repl(': woo')
            repl(': woo = during') # Not executed.
            repl('houpla1 = 1 : woo = during') # Only first phrase is executed.
            repl('houpla2 = 2 : houpla3 = 4 : woo = during') # Same, second colon is part of comment.
            repl('yay := $(woo)')
            repl('woo = after')
        c = c.node
        ae = self.assertEqual
        ae('before', c.yay)
        ae('after', c.woo)
        ae(1, c.houpla1)
        ae(2, c.houpla2)
        ae(3, c.houpla3)

    def test_equalsprecedence(self):
        c = Config.blank()
        with c.repl() as repl:
            repl('woo = before')
            repl('woo = and = after') # Apply first equals less astonishing than error or applying second.
        c = c.node
        ae = self.assertEqual
        ae('and = after', c.woo)

    def test_starprecedence(self):
        c = Config.blank()
        with c.repl() as repl:
            repl('woo = yay * houpla') # Would be very confusing for * to have precedence here.
        c = c.node
        ae = self.assertEqual
        ae('yay * houpla', c.woo)

    def test_sourcecommentwithprefix(self):
        c = Config.blank()
        with NamedTemporaryFile('w') as f, c.repl() as repl:
            f.write('woo = yay\n')
            f.write('woo2 = yay2 : with comment\n')
            f.write(': comment only\n')
            f.flush()
            repl.printf("prefix . %s", f.name)
        c = c.node
        ae = self.assertEqual
        ae('yay', c.prefix.woo)
        ae('yay2', c.prefix.woo2)

    def test_starmultiplechildren(self):
        c = Config.blank()
        c.printf('a = A')
        c.printf('b = B')
        c.printf('profile * a = $(void)')
        c.printf('profile * b = $(void)')
        c.printf('profile p x = y')
        c = c.node
        with self.assertRaises(AttributeError):
            c.profile.p.a
        with self.assertRaises(AttributeError):
            c.profile.p.b
        self.assertEqual('y', c.profile.p.x)

    def test_starishidden(self):
        c = Config.blank().node
        (~c).printf('x * y = z')
        self.assertEqual({}, (~c.x).unravel())
        self.assertEqual([], list(~c.x))
        (~c).printf('x a = b')
        self.assertEqual(dict(a = 'b'), (~c.x).unravel())
        self.assertEqual([('a', 'b')], list(~c.x))
        (~c).printf('x p q = r')
        self.assertEqual(dict(a = 'b', p = dict(q = 'r', y = 'z')), (~c.x).unravel())
