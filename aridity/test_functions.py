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

from .context import Scope, Resource
from .functions import _tomlquote
from .model import Entry, Function
from .repl import Repl
from .util import ispy2, NoSuchPathException
from tempfile import NamedTemporaryFile
from unittest import TestCase
import os, sys

class TestFunctions(TestCase):

    def test_slash(self):
        s = Scope()
        with Repl(s) as repl:
            repl('empty = $/()')
            repl('simplerel = $/(woo)')
            repl('simpleabs = $/(/woo)')
            repl('joinrel = $/(woo yay)')
            repl('joinabs = $/(/woo yay)')
            repl('lazyfail = $/($(no) woo yay)') # Outcome may depend on first component.
            repl('lazyok = $/($(no) /woo yay)') # Outcome does not depend on first component.
        ae = self.assertEqual
        with self.assertRaises(TypeError):
            s.resolved('empty')
        ae('woo', s.resolved('simplerel').scalar)
        ae('/woo', s.resolved('simpleabs').scalar)
        ae('woo/yay', s.resolved('joinrel').scalar)
        ae('/woo/yay', s.resolved('joinabs').scalar)
        with self.assertRaises(NoSuchPathException):
            s.resolved('lazyfail')
        ae('/woo/yay', s.resolved('lazyok').scalar)

    def test_hereisavailableduringinclude(self):
        with NamedTemporaryFile('w') as f:
            f.write('hereval := $(here)\n')
            f.write('sibpath := $./(sibling)\n')
            f.write('sibpath2 := $./(sib child)\n')
            f.flush()
            s = Scope()
            with Repl(s) as repl:
                repl.printf(". %s", f.name)
            self.assertEqual(os.path.dirname(f.name), s.resolved('hereval').scalar)
            self.assertEqual(os.path.join(os.path.dirname(f.name), 'sibling'), s.resolved('sibpath').scalar)
            self.assertEqual(os.path.join(os.path.dirname(f.name), 'sib', 'child'), s.resolved('sibpath2').scalar)

    def test_hereisavailableduringprocesstemplate(self):
        with NamedTemporaryFile('w') as f, NamedTemporaryFile('r') as g:
            f.write('$(here) $./(sibling) $./(sib child)')
            f.flush()
            s = Scope()
            with Repl(s) as repl:
                repl.printf("text = $processtemplate(%s)", f.name)
                repl.printf("redirect %s", g.name)
                repl.printf("< %s", f.name)
            d = os.path.dirname(f.name)
            expected = "%s %s %s" % (d, os.path.join(d, 'sibling'), os.path.join(d, 'sib', 'child'))
            self.assertEqual(expected, s.resolved('text').scalar)
            self.assertEqual(expected, g.read())

    def test_dotslashinresource(self):
        s = Scope()
        Resource(__name__, 'test_functions/stream.arid').source(s, Entry([]))
        self.assertEqual('yay', s.resolved('data1', 'woo').textvalue)
        self.assertEqual('yay2', s.resolved('data2', 'woo2').textvalue)
        self.assertEqual('yay3', s.resolved('data2', 'woo3').textvalue)
        self.assertEqual('sibval', s.resolved('data3', 'sibkey').textvalue)

    def test_concatinlist(self):
        s = Scope()
        with Repl(s) as repl:
            repl('a = x')
            repl('b = y')
            repl('c = z')
            repl('j = $join($list($(a)$(b) $(b)$(c)) -)')
        self.assertEqual('xy-yz', s.resolved('j').scalar)

    def test_listandmapincontext(self):
        s = Scope()
        with Repl(s) as repl:
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
        self.assertEqual("'x' & 'X'; 'y' & 'Y'", s.resolved('sub1', 'duped').scalar)
        self.assertEqual('"x" & "X"; "y" & "Y"', s.resolved('sub2', 'duped').scalar)
        self.assertEqual("'x' & 'X'; 'y' & 'Y'", s.resolved('sub1', 'jlist').scalar)
        self.assertEqual('"x" & "X"; "y" & "Y"', s.resolved('sub2', 'jlist').scalar)
        self.assertEqual("'x' & 'X'; 'y' & 'Y'", s.resolved('sub1', 'map2a').scalar)
        self.assertEqual('"x" & "X"; "y" & "Y"', s.resolved('sub2', 'map2a').scalar)
        self.assertEqual("'x' & 'X'; 'y' & 'Y'", s.resolved('sub1', 'map1a').scalar)
        self.assertEqual('"x" & "X"; "y" & "Y"', s.resolved('sub2', 'map1a').scalar)

    def test_joinlistwithinternalref(self):
        s = Scope()
        with Repl(s) as repl:
            repl('v a = x')
            repl('v b = r$(a)')
            repl('j = $join($(v) ,)')
        self.assertEqual('x,rx', s.resolved('j').scalar)

    def test_mapcommafunction(self):
        s = Scope()
        with Repl(s) as repl:
            repl('command = git rev-parse --abbrev-ref @{u}')
            repl('" = $(pystr)')
            repl('text = $join($map($,(command) w $"$(w)) $.( ))')
        self.assertEqual("'git' 'rev-parse' '--abbrev-ref' '@{u}'", s.resolved('text').scalar)

    def test_mapreceiver(self):
        s = Scope()
        with Repl(s) as repl:
            repl('x = $join($map($(v) $"$()) ,)')
            repl('v += one')
            repl('v += two')
            repl('" = $(jsonquote)')
        try:
            self.assertEqual('"one","two"', s.resolved('x').scalar)
            self.fail('You fixed a bug!')
        except AttributeError:
            pass

    def test_listref(self):
        s = Scope()
        with Repl(s) as repl:
            repl('foo args += yyup=$(yyup)')
            repl('foo args += w/e')
            repl('foo yyup = YYUP')
            repl('foo x = $join($map($(args) it $(it)) .)')
            repl('x = $join($map($(foo args) it $(it)) .)')
        self.assertEqual(['yyup=YYUP', 'w/e'], list(s.resolved('foo', 'args').unravel().values()))
        self.assertEqual('yyup=YYUP.w/e', s.resolved('foo', 'x').unravel())
        try:
            self.assertEqual('yyup=YYUP.w/e', s.resolved('x').unravel())
            self.fail('You fixed a bug!')
        except NoSuchPathException:
            pass

    def test_xmlquoting(self):
        s = Scope()
        with Repl(s) as repl:
            repl('" = $(xmlattr)')
            repl('& = $(xmltext)')
            repl('''x = $"(abc<>&"')''')
            repl('''x2 = $"(abc<>&')''')
            repl('''x3 = $"(abc<>&")''')
            repl('''y = $&(abc<>&"')''')
        self.assertEqual('''"abc&lt;&gt;&amp;&quot;'"''', s.resolved('x').cat())
        self.assertEqual('''"abc&lt;&gt;&amp;'"''', s.resolved('x2').cat())
        self.assertEqual("""'abc&lt;&gt;&amp;"'""", s.resolved('x3').cat())
        # Escape all quotes as users may expect to be able to paste into attribute content:
        self.assertEqual('abc&lt;&gt;&amp;&quot;&apos;', s.resolved('y').cat())

    def test_tomlquote(self):
        self.assertEqual('"abc\t \x7e\x80"', _tomlquote('abc\t \x7e\x80'))
        self.assertEqual(r'"\u005C\u0022"', _tomlquote(r'\"'))
        self.assertEqual(r'"\u0000\u0008\u000A\u001F\u007F"', _tomlquote('\x00\x08\x0a\x1f\x7f'))

    def test_urlquote(self):
        if ispy2:
            return
        s = Scope()
        with Repl(s) as repl:
            repl('a = $urlquote($.( /?&=_\N{POUND SIGN}))')
        self.assertEqual('%20%2F%3F%26%3D_%C2%A3', s.resolved('a').cat())

    def test_pyref(self):
        s = Scope()
        with Repl(s) as repl:
            repl('f = $pyref(sys exc_info)')
        obj = s.resolved('f')
        self.assertIs(Function, type(obj))
        self.assertIs(sys.exc_info, obj.functionvalue)
        self.assertIs(sys.exc_info, obj.scalar)
        self.assertIs(sys.exc_info, obj.unravel())
