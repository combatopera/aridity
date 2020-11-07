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
from .functions import _tomlquote
from .model import Entry, Function
from .repl import Repl
from .util import ispy2, NoSuchPathException
from tempfile import NamedTemporaryFile
from unittest import TestCase
import os, sys

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
        ae('woo', c.resolved('simplerel').scalar)
        ae('/woo', c.resolved('simpleabs').scalar)
        ae('woo/yay', c.resolved('joinrel').scalar)
        ae('/woo/yay', c.resolved('joinabs').scalar)
        with self.assertRaises(NoSuchPathException):
            c.resolved('lazyfail')
        ae('/woo/yay', c.resolved('lazyok').scalar)

    def test_hereisavailableduringinclude(self):
        with NamedTemporaryFile('w') as f:
            f.write('hereval := $(here)\n')
            f.write('sibpath := $./(sibling)\n')
            f.write('sibpath2 := $./(sib child)\n')
            f.flush()
            c = Context()
            with Repl(c) as repl:
                repl.printf(". %s", f.name)
            self.assertEqual(os.path.dirname(f.name), c.resolved('hereval').scalar)
            self.assertEqual(os.path.join(os.path.dirname(f.name), 'sibling'), c.resolved('sibpath').scalar)
            self.assertEqual(os.path.join(os.path.dirname(f.name), 'sib', 'child'), c.resolved('sibpath2').scalar)

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
            self.assertEqual(expected, c.resolved('text').scalar)
            self.assertEqual(expected, g.read())

    def test_dotslashinresource(self):
        c = Context()
        c.sourceres(Entry([]), __name__, 'test_functions/stream.arid')

    def test_concatinlist(self):
        c = Context()
        with Repl(c) as repl:
            repl('a = x')
            repl('b = y')
            repl('c = z')
            repl('j = $join($list($(a)$(b) $(b)$(c)) -)')
        self.assertEqual('xy-yz', c.resolved('j').scalar)

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
        self.assertEqual("'x' & 'X'; 'y' & 'Y'", c.resolved('sub1', 'duped').scalar)
        self.assertEqual('"x" & "X"; "y" & "Y"', c.resolved('sub2', 'duped').scalar)
        self.assertEqual("'x' & 'X'; 'y' & 'Y'", c.resolved('sub1', 'jlist').scalar)
        self.assertEqual('"x" & "X"; "y" & "Y"', c.resolved('sub2', 'jlist').scalar)
        self.assertEqual("'x' & 'X'; 'y' & 'Y'", c.resolved('sub1', 'map2a').scalar)
        self.assertEqual('"x" & "X"; "y" & "Y"', c.resolved('sub2', 'map2a').scalar)
        self.assertEqual("'x' & 'X'; 'y' & 'Y'", c.resolved('sub1', 'map1a').scalar)
        self.assertEqual('"x" & "X"; "y" & "Y"', c.resolved('sub2', 'map1a').scalar)

    def test_joinlistwithinternalref(self):
        c = Context()
        with Repl(c) as repl:
            repl('v a = x')
            repl('v b = r$(a)')
            repl('j = $join($(v) ,)')
        self.assertEqual('x,rx', c.resolved('j').scalar)

    def test_mapcommafunction(self):
        c = Context()
        with Repl(c) as repl:
            repl('command = git rev-parse --abbrev-ref @{u}')
            repl('" = $(pystr)')
            repl('text = $join($map($,(command) w $"$(w)) $.( ))')
        self.assertEqual("'git' 'rev-parse' '--abbrev-ref' '@{u}'", c.resolved('text').scalar)

    def test_mapreceiver(self):
        c = Context()
        with Repl(c) as repl:
            repl('x = $join($map($(v) $"$()) ,)')
            repl('v += one')
            repl('v += two')
            repl('" = $(jsonquote)')
        try:
            self.assertEqual('"one","two"', c.resolved('x').scalar)
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

    def test_tomlquote(self):
        self.assertEqual('"abc\t \x7e\x80"', _tomlquote('abc\t \x7e\x80'))
        self.assertEqual(r'"\u005C\u0022"', _tomlquote(r'\"'))
        self.assertEqual(r'"\u0000\u0008\u000A\u001F\u007F"', _tomlquote('\x00\x08\x0a\x1f\x7f'))

    def test_urlquote(self):
        if ispy2:
            return
        c = Context()
        with Repl(c) as repl:
            repl('a = $urlquote($.( /?&=_\N{POUND SIGN}))')
        self.assertEqual('%20%2F%3F%26%3D_%C2%A3', c.resolved('a').cat())

    def test_pyref(self):
        c = Context()
        with Repl(c) as repl:
            repl('f = $pyref(sys exc_info)')
        obj = c.resolved('f')
        self.assertIs(Function, type(obj))
        self.assertIs(sys.exc_info, obj.functionvalue)
        self.assertIs(sys.exc_info, obj.scalar)
        self.assertIs(sys.exc_info, obj.unravel())
