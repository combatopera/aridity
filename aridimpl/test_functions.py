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

    def test_concatinlist(self):
        c = Context()
        with Repl(c) as repl:
            repl('a = x')
            repl('b = y')
            repl('c = z')
            repl('j = $join($list($(a)$(b) $(b)$(c)) -)')
        self.assertEqual('xy-yz', c.resolved('j').value)

    def test_listandmapincontext(self):
        c = Context()
        with Repl(c) as repl:
            repl('my a eranu = x')
            repl('my a uvavu = X')
            repl('my b eranu = y')
            repl('my b uvavu = Y')
            repl('duped = $"$(my a eranu) & $"$(my a uvavu); $"$(my b eranu) & $"$(my b uvavu)')
            repl('jlist = $join($list($.($"$(my a eranu) & $"$(my a uvavu)) $.($"$(my b eranu) & $"$(my b uvavu))) $.(; ))')
            repl('map2a = $join($map($(my) it $.($"$(it eranu) & $"$(it uvavu))) $.(; ))')
            repl('map1a = $join($map($(my) $.($"$(eranu) & $"$(uvavu))) $.(; ))')
            repl('sub1 " = $(pystr)')
            repl('sub2 " = $(screenstr)')
        self.assertEqual("'x' & 'X'; 'y' & 'Y'", c.resolved('sub1', 'duped').value)
        self.assertEqual('"x" & "X"; "y" & "Y"', c.resolved('sub2', 'duped').value)
        self.assertEqual("'x' & 'X'; 'y' & 'Y'", c.resolved('sub1', 'jlist').value)
        self.assertEqual('"x" & "X"; "y" & "Y"', c.resolved('sub2', 'jlist').value)
        self.assertEqual("'x' & 'X'; 'y' & 'Y'", c.resolved('sub1', 'map2a').value)
        self.assertEqual('"x" & "X"; "y" & "Y"', c.resolved('sub2', 'map2a').value)
        self.assertEqual("'x' & 'X'; 'y' & 'Y'", c.resolved('sub1', 'map1a').value)
        self.assertEqual('"x" & "X"; "y" & "Y"', c.resolved('sub2', 'map1a').value)

    def test_joinlistwithinternalref(self):
        c = Context()
        with Repl(c) as repl:
            repl('v a = x')
            repl('v b = r$(a)')
            repl('j = $join($(v) ,)')
        self.assertEqual('x,rx', c.resolved('j').value)

    def test_mapcommafunction(self):
        c = Context()
        with Repl(c) as repl:
            repl('command = git rev-parse --abbrev-ref @{u}')
            repl('" = $(pystr)')
            repl('text = $join($map($,(command) w $"$(w)) $.( ))')
        self.assertEqual("'git' 'rev-parse' '--abbrev-ref' '@{u}'", c.resolved('text').value)

    def test_mapreceiver(self):
        c = Context()
        with Repl(c) as repl:
            repl('x = $join($map($(v) $"$()) ,)')
            repl('v += one')
            repl('v += two')
            repl('" = $(jsonquote)')
        try:
            self.assertEqual('"one","two"', c.resolved('x').value)
            self.fail('You fixed a bug!')
        except AttributeError:
            pass

    def test_listref(self):
        c = Context()
        with Repl(c) as repl:
            repl('foo args += yyup=$(yyup)')
            repl('foo args += w/e')
            repl('foo yyup = YYUP')
            repl('foo x = $join($map($(args) it $(it)) .)')
            repl('x = $join($map($(foo args) it $(it)) .)')
        self.assertEqual(['yyup=YYUP', 'w/e'], list(c.resolved('foo', 'args').unravel().values()))
        self.assertEqual('yyup=YYUP.w/e', c.resolved('foo', 'x').unravel())
        try:
            self.assertEqual('yyup=YYUP.w/e', c.resolved('x').unravel())
            self.fail('You fixed a bug!')
        except NoSuchPathException:
            pass

    def test_xmlquoting(self):
        c = Context()
        with Repl(c) as repl:
            repl('" = $(xmlattr)')
            repl('& = $(xmltext)')
            repl('''x = $"(abc<>&"')''')
            repl('''x2 = $"(abc<>&')''')
            repl('''x3 = $"(abc<>&")''')
            repl('''y = $&(abc<>&"')''')
        self.assertEqual('''"abc&lt;&gt;&amp;&quot;'"''', c.resolved('x').cat())
        self.assertEqual('''"abc&lt;&gt;&amp;'"''', c.resolved('x2').cat())
        self.assertEqual("""'abc&lt;&gt;&amp;"'""", c.resolved('x3').cat())
        # Escape all quotes as users may expect to be able to paste into attribute content:
        self.assertEqual('abc&lt;&gt;&amp;&quot;&apos;', c.resolved('y').cat())
