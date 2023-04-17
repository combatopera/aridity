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
        except:
            rmtree(self.tempdir)
            raise

    def _runmodule(self, module, *command):
        return check_output([sys.executable, '-m', module] + list(command), cwd = self.d, env = dict(os.environ, PYTHONPATH = os.pathsep.join(sys.path)), universal_newlines = True)

    def tearDown(self):
        rmtree(self.tempdir)

    def test_works(self):
        check_call([sys.executable, 'setup.py', 'egg_info'], cwd = self.d)

        self.assertEqual('pkg __main__ woo\n', self._runmodule('toplevel', 'tuplestyle'))
        self.assertEqual('pkg toplevel woo\n', self._runmodule('delegate', 'toplevel', 'tuplestyle'))

        self.assertEqual('pkg __main__ file\n', self._runmodule('pkg.file', 'functionstyle'))
        self.assertEqual('pkg pkg.file function-style\n', self._runmodule('delegate', 'pkg.file', 'functionstyle'))
        self.assertEqual('pkg __main__ woo\n', self._runmodule('pkg.file', 'tuplestyle'))
        self.assertEqual('pkg pkg.file woo\n', self._runmodule('delegate', 'pkg.file', 'tuplestyle'))

        self.assertEqual('sub __main__ file\n', self._runmodule('pkg.subpkg.file', 'functionstyle'))
        self.assertEqual('sub pkg.subpkg.file function-style-sub\n', self._runmodule('delegate', 'pkg.subpkg.file', 'functionstyle'))
        self.assertEqual('sub __main__ woo\n', self._runmodule('pkg.subpkg.file', 'tuplestyle'))
        self.assertEqual('sub pkg.subpkg.file woo\n', self._runmodule('delegate', 'pkg.subpkg.file', 'tuplestyle'))

        self.assertEqual('pkg __main__ function-style\n', self._runmodule('otherpkg.file', 'otherfunction'))
        self.assertEqual('pkg __main__ tuple-style\n', self._runmodule('otherpkg.file', 'otherfunction2'))
