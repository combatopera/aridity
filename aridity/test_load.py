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

from shutil import copytree, rmtree
from subprocess import check_call, check_output
from tempfile import mkdtemp
from unittest import TestCase
import os, sys

class TestLoad(TestCase):

    def setUp(self):
        self.tempdir = mkdtemp()
        try:
            self.d = os.path.join(self.tempdir, 'project')
            copytree(os.path.join(os.path.dirname(__file__), 'test_load'), self.d)
            check_call([sys.executable, 'setup.py', 'egg_info'], cwd = self.d)
        except:
            rmtree(self.tempdir)
            raise

    def _file(self, *args):
        return check_output([sys.executable] + list(args), cwd = self.d, env = dict(os.environ, PYTHONPATH = os.pathsep.join(sys.path)), universal_newlines = True)

    def _moduleasself(self, module, command):
        return self._file('-m', 'delegate', module, command)

    def _moduleasmain(self, module, command):
        return self._file('-m', module, command)

    def tearDown(self):
        rmtree(self.tempdir)

    def test_works(self):
        self.assertEqual('pkg __main__ woo\n', self._file('toplevel.py', 'tuplestyle'))
        self.assertEqual('pkg __main__ woo\n', self._moduleasmain('toplevel', 'tuplestyle'))
        self.assertEqual('pkg toplevel woo\n', self._moduleasself('toplevel', 'tuplestyle'))

        self.assertEqual('pkg __main__ --main--\n', self._moduleasmain('pkg', 'functionstyle'))
        self.assertEqual('pkg __main__ woo\n', self._moduleasmain('pkg', 'tuplestyle'))

        self.assertEqual('pkg pkg function-style-init\n', self._moduleasself('pkg', 'functionstyle'))
        self.assertEqual('pkg pkg woo\n', self._moduleasself('pkg', 'tuplestyle'))

        self.assertEqual('pkg __main__ file\n', self._moduleasmain('pkg.file', 'functionstyle'))
        self.assertEqual('pkg pkg.file function-style\n', self._moduleasself('pkg.file', 'functionstyle'))
        self.assertEqual('pkg __main__ woo\n', self._moduleasmain('pkg.file', 'tuplestyle'))
        self.assertEqual('pkg pkg.file woo\n', self._moduleasself('pkg.file', 'tuplestyle'))

        self.assertEqual('sub __main__ --main--\n', self._moduleasmain('pkg.subpkg', 'functionstyle'))
        self.assertEqual('sub __main__ woo\n', self._moduleasmain('pkg.subpkg', 'tuplestyle'))

        self.assertEqual('sub pkg.subpkg function-style-init2\n', self._moduleasself('pkg.subpkg', 'functionstyle'))
        self.assertEqual('sub pkg.subpkg woo\n', self._moduleasself('pkg.subpkg', 'tuplestyle'))

        self.assertEqual('sub __main__ file\n', self._moduleasmain('pkg.subpkg.file', 'functionstyle'))
        self.assertEqual('sub pkg.subpkg.file function-style-sub\n', self._moduleasself('pkg.subpkg.file', 'functionstyle'))
        self.assertEqual('sub __main__ woo\n', self._moduleasmain('pkg.subpkg.file', 'tuplestyle'))
        self.assertEqual('sub pkg.subpkg.file woo\n', self._moduleasself('pkg.subpkg.file', 'tuplestyle'))

        self.assertEqual('pkg __main__ function-style\n', self._moduleasmain('otherpkg.file', 'otherfunction'))
        self.assertEqual('pkg otherpkg.file function-style\n', self._moduleasself('otherpkg.file', 'otherfunction'))
        self.assertEqual('pkg __main__ tuple-style\n', self._moduleasmain('otherpkg.file', 'otherfunction2'))
        self.assertEqual('pkg otherpkg.file tuple-style\n', self._moduleasself('otherpkg.file', 'otherfunction2'))
