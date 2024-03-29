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

from .model import Function, Stream, Text
from .repl import Repl
from .scope import Scope
from tempfile import NamedTemporaryFile
from unittest import TestCase

def _blockquote(scope, resolvable):
    indent = scope.resolved('indent').scalar
    return Text(''.join((indent if i else '') + l for i, l in enumerate(resolvable.resolve(scope).scalar.splitlines(True))))

def _processtemplate(scope, path):
    with open(path) as f:
        return Stream(f).processtemplate(scope)

class TestTemplate(TestCase):

    def test_indentworks(self):
        with NamedTemporaryFile('w') as f:
            f.write('root: .$(indent).\n')
            f.write(' sp: .$(indent).\n')
            f.write('    4sp: .$(indent).\n')
            f.write('\ttab: .$(indent).\n')
            f.write('\t mixed: .$(indent).\n')
            f.write('\t$(indent) compound: .$(indent).\n')
            f.flush()
            self.assertEqual('''root: ..
 sp: . .
    4sp: .    .
\ttab: .\t.
\t mixed: .\t .
\t\t compound: .\t\t .
''', _processtemplate(Scope(), f.name))

    def test_trivialindent(self):
        with NamedTemporaryFile('w') as f:
            f.write('$(indent) should not fail')
            f.flush()
            self.assertEqual(' should not fail', _processtemplate(Scope(), f.name))

    def test_getindentinfunction(self):
        s = Scope()
        s['"',] = Function(_blockquote)
        with Repl(s) as repl:
            repl('block = $.(z\ny\nx\n)') # XXX: Is this sane?
        with NamedTemporaryFile('w') as f:
            f.write('  hmm: $"$(block)\n')
            f.flush()
            self.assertEqual('''  hmm: z
  y
  x

''', _processtemplate(s, f.name))

    def test_nestedexprindent(self):
        with NamedTemporaryFile('w') as f:
            f.write('''  $.[outer=<$(indent)>
    inner=<$(indent)>]''')
            f.flush()
            self.assertEqual('  outer=<  >\n    inner=<    >', _processtemplate(Scope(), f.name))
