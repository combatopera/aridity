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
from .directives import processtemplate
from .model import Text
from tempfile import NamedTemporaryFile
from unittest import TestCase

class TestTemplate(TestCase):

    def test_indent(self):
        c = Context()
        with NamedTemporaryFile('w') as f:
            f.write('root: .$(indent).\n')
            f.write(' sp: .$(indent).\n')
            f.write('    4sp: .$(indent).\n')
            f.write('\ttab: .$(indent).\n')
            f.write('\t mixed: .$(indent).\n')
            f.write('\t$(indent) dynamic: .$(indent).\n')
            f.flush()
            self.assertEqual('''root: ..
 sp: . .
    4sp: .    .
\ttab: .\t.
\t mixed: .\t .
\t\t dynamic: .\t\t .
''', processtemplate(c, Text(f.name)))

    def test_trivialindent(self):
        c = Context()
        with NamedTemporaryFile('w') as f:
            f.write('$(indent) should not fail')
            f.flush()
            self.assertEqual(' should not fail', processtemplate(c, Text(f.name)))