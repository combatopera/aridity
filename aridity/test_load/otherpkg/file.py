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

from aridity.config import ConfigCtrl
from pkg.file import functionstyle, tuplestyle
import sys

def otherfunction():
    c = ConfigCtrl().loadappconfig(functionstyle, 'root.arid', settingsoptional = True)
    c.modname = __name__
    print(c.info)

def otherfunction2():
    c = ConfigCtrl().loadappconfig(tuplestyle, 'root.arid', settingsoptional = True)
    c.modname = __name__
    print(c.info)

def main():
    globals()[sys.argv.pop(1)]()

if '__main__' == __name__:
    main()
