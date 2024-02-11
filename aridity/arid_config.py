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

'Print given config (with optional path in config) as shell snippet.'
from .model import Boolean, Entry, Locator, Number, Text
from .scope import Scope
import os, sys

def _configpath(configname):
    if os.sep in configname:
        return configname
    for parent in os.environ['PATH'].split(os.pathsep):
        path = os.path.join(parent, configname)
        if os.path.exists(path):
            return path
    raise Exception("Not found: %s" % configname)

def _scopetobash(self, toplevel = False):
    if toplevel:
        return ''.join("%s=%s\n" % (name, obj.resolve(self).tobash()) for name, obj in self.resolvables.items())
    if self.islist:
        return "(%s)" % ' '.join(x.resolve(self).tobash() for _, x in self.resolvables.items())
    return Text(self.tobash(True)).tobash()

Scope.tobash = _scopetobash
Boolean.tobash = lambda self, toplevel: 'true' if self.booleanvalue else 'false'
Number.tobash = lambda self: str(self.numbervalue)
Text.tobash = lambda self: "'%s'" % self.textvalue.replace("'", r"'\''")

def main():
    scope = Scope()
    Locator(_configpath(sys.argv[1])).source(scope, Entry([]))
    sys.stdout.write(scope.resolved(*sys.argv[2:]).tobash(True))

if '__main__' == __name__:
    main()
