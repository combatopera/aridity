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

from inspect import getsource
from shutil import rmtree
from subprocess import check_call, check_output
from tempfile import mkdtemp
from unittest import TestCase
import os, sys

def functionstyle():
    from aridity.config import ConfigCtrl
    print(ConfigCtrl().loadappconfig(functionstyle, 'root.arid', settingsoptional = True).appname)

def tuplestyle():
    from aridity.config import ConfigCtrl
    print(ConfigCtrl().loadappconfig((__name__, 'woo'), 'root.arid', settingsoptional = True).appname)

def otherfunction():
    from pkg.functionstyle import functionstyle
    from aridity.config import ConfigCtrl
    print(ConfigCtrl().loadappconfig(functionstyle, 'root.arid', settingsoptional = True).appname)

def otherfunction2():
    from pkg.tuplestyle import tuplestyle
    from aridity.config import ConfigCtrl
    print(ConfigCtrl().loadappconfig(tuplestyle, 'root.arid', settingsoptional = True).appname)

class TestLoad(TestCase):

    def setUp(self):
        self.d = mkdtemp()
        try:
            pkg = os.path.join(self.d, 'pkg')
            os.mkdir(pkg)
            otherpkg = os.path.join(self.d, 'otherpkg')
            os.mkdir(otherpkg)
            with open(os.path.join(pkg, '__init__.py'), 'w') as f:
                pass
            with open(os.path.join(otherpkg, '__init__.py'), 'w') as f:
                pass
            with open(os.path.join(pkg, 'root.arid'), 'w') as f:
                f.write('appname = $label()\n')
            for p, main in zip([pkg, pkg, otherpkg, otherpkg], [functionstyle, tuplestyle, otherfunction, otherfunction2]):
                with open(os.path.join(p, "%s.py" % main.__name__), 'w') as f:
                    f.write(getsource(main))
                    f.write("""if '__main__' == __name__:
    %s()
""" % main.__name__)
            with open(os.path.join(self.d, 'setup.py'), 'w') as f:
                f.write('''from setuptools import find_packages, setup
setup(
    entry_points = dict(console_scripts = [
        'function-style=pkg.functionstyle:functionstyle',
        'tuple-style=pkg.tuplestyle:tuplestyle',
    ]),
    packages = find_packages(),
)
''')
        except:
            rmtree(self.d)
            raise

    def _runmodule(self, module):
        return check_output([sys.executable, '-m', module], cwd = self.d, env = dict(os.environ, PYTHONPATH = os.pathsep.join(sys.path)), universal_newlines = True)

    def tearDown(self):
        rmtree(self.d)

    def test_works(self):
        self.assertEqual('functionstyle\n', self._runmodule('pkg.functionstyle'))
        self.assertEqual('woo\n', self._runmodule('pkg.tuplestyle'))
        check_call([sys.executable, 'setup.py', 'egg_info'], cwd = self.d)
        self.assertEqual('function-style\n', self._runmodule('otherpkg.otherfunction'))
        self.assertEqual('tuple-style\n', self._runmodule('otherpkg.otherfunction2'))
