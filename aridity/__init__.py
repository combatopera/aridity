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

'Interactive REPL.'
from .model import Stream
from .repl import Repl
from .scope import Scope
from .util import NoSuchPathException
import sys

assert NoSuchPathException

def main():
    scope = Scope()
    scope['stdout',] = Stream(sys.stdout)
    with Repl(scope, True) as repl:
        for line in sys.stdin:
            repl(line)

if '__main__' == __name__:
    main()
