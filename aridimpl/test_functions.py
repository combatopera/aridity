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
from tempfile import NamedTemporaryFile
from unittest import TestCase
import os

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

    def test_hereisavailableduringinclude(self):
        with NamedTemporaryFile('w') as f:
            f.write('hereval := $(here)\n')
            f.write('sibpath := $./(sibling)\n')
            f.write('sibpath2 := $./(sib child)\n')
            f.flush()
            c = Context()
            with Repl(c) as repl:
                repl.printf(". %s", f.name)
            self.assertEqual(os.path.dirname(f.name), c.resolved('hereval').value)
            self.assertEqual(os.path.join(os.path.dirname(f.name), 'sibling'), c.resolved('sibpath').value)
            self.assertEqual(os.path.join(os.path.dirname(f.name), 'sib', 'child'), c.resolved('sibpath2').value)

    def test_hereisavailableduringprocesstemplate(self):
        with NamedTemporaryFile('w') as f, NamedTemporaryFile('r') as g:
            f.write('$(here) $./(sibling) $./(sib child)')
            f.flush()
            c = Context()
            with Repl(c) as repl:
                repl.printf("text = $processtemplate(%s)", f.name)
                repl.printf("redirect %s", g.name)
                repl.printf("< %s", f.name)
            d = os.path.dirname(f.name)
            expected = "%s %s %s" % (d, os.path.join(d, 'sibling'), os.path.join(d, 'sib', 'child'))
            self.assertEqual(expected, c.resolved('text').value)
            self.assertEqual(expected, g.read())