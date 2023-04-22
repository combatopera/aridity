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

    def _python(self, *args):
        return check_output([sys.executable] + list(args), cwd = self.d, env = dict(os.environ, PYTHONPATH = os.pathsep.join(sys.path)), universal_newlines = True)

    def _moduleasself(self, module, command):
        return self._python('-m', 'delegate', module, command)

    def _moduleasmain(self, module, command):
        return self._python('-m', module, command)

    def tearDown(self):
        rmtree(self.tempdir)

    def test_functionstyle(self):
        self.assertEqual('pkg __main__ --main--\n', self._moduleasmain('pkg', 'functionstyle'))
        self.assertEqual('pkg __main__ file\n', self._moduleasmain('pkg.file', 'functionstyle'))
        self.assertEqual('sub __main__ --main--\n', self._moduleasmain('pkg.subpkg', 'functionstyle'))
        self.assertEqual('sub __main__ file\n', self._moduleasmain('pkg.subpkg.file', 'functionstyle'))
        self.assertEqual('pkg __main__ function-style-init\n', self._moduleasmain('others', 'pkg'))
        self.assertEqual('pkg __main__ function-style\n', self._moduleasmain('others', 'pkg_file'))
        self.assertEqual('sub __main__ function-style-init2\n', self._moduleasmain('others', 'pkg_subpkg'))
        self.assertEqual('sub __main__ function-style-sub\n', self._moduleasmain('others', 'pkg_subpkg_file'))
        self.assertEqual('pkg pkg function-style-init\n', self._moduleasself('pkg', 'functionstyle'))
        self.assertEqual('pkg pkg.file function-style\n', self._moduleasself('pkg.file', 'functionstyle'))
        self.assertEqual('sub pkg.subpkg function-style-init2\n', self._moduleasself('pkg.subpkg', 'functionstyle'))
        self.assertEqual('sub pkg.subpkg.file function-style-sub\n', self._moduleasself('pkg.subpkg.file', 'functionstyle'))
        self.assertEqual('pkg others function-style-init\n', self._moduleasself('others', 'pkg'))
        self.assertEqual('pkg others function-style\n', self._moduleasself('others', 'pkg_file'))
        self.assertEqual('sub others function-style-init2\n', self._moduleasself('others', 'pkg_subpkg'))
        self.assertEqual('sub others function-style-sub\n', self._moduleasself('others', 'pkg_subpkg_file'))
