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
from unittest import TestCase

class TestDirectives(TestCase):

    def test_commentpriority(self):
        c = Config.blank()
        with c.repl() as repl:
            repl('woo = before')
            repl('houpla3 = 3')
            repl(':')
            repl(': woo')
            repl(': woo = during') # Not executed.
            repl('houpla1 = 1 : woo = during') # Only first phrase is executed.
            repl('houpla2 = 2 : houpla3 = 4 : woo = during') # Same.
            repl('yay := $(woo)')
            repl('woo = after')
        ae = self.assertEqual
        ae('before', c.yay)
        ae('after', c.woo)
        ae(1, c.houpla1)
        ae(2, c.houpla2)
        ae(3, c.houpla3)
