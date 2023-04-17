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

from common import printinfo
from pkg.file import functionstyle, tuplestyle
import sys

def otherfunction():
    printinfo(__name__, functionstyle)

def otherfunction2():
    printinfo(__name__, tuplestyle)

def main():
    globals()[sys.argv.pop(1)]()

if '__main__' == __name__:
    main()
