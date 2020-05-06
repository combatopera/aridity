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
from .repl import Repl
from .util import NoSuchPathException
from unittest import TestCase

class TestFunctions(TestCase):

    def test_slash(self):
        c = Context()
        with Repl(c) as repl:
            repl('empty = $/()')
            repl('simplerel = $/(woo)')
            repl('simpleabs = $/(/woo)')
            repl('joinrel = $/(woo yay)')
            repl('joinabs = $/(/woo yay)')
            repl('lazyfail = $/($(no) woo yay)') # Outcome may depend on first component.
            repl('lazyok = $/($(no) /woo yay)') # Outcome does not depend on first component.
        ae = self.assertEqual
        with self.assertRaises(TypeError):
            c.resolved('empty')
        ae('woo', c.resolved('simplerel').value)
        ae('/woo', c.resolved('simpleabs').value)
        ae('woo/yay', c.resolved('joinrel').value)
        ae('/woo/yay', c.resolved('joinabs').value)
        with self.assertRaises(NoSuchPathException):
            c.resolved('lazyfail')
        ae('/woo/yay', c.resolved('lazyok').value)
