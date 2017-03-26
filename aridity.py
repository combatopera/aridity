#!/usr/bin/env python3

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

import sys, traceback, pyparsing
from aridityimpl.parser import commandparser
from aridityimpl.grammar import Stream
from aridityimpl.context import Context, NoSuchPathException
from aridityimpl.directives import execute, UnsupportedEntryException

class DanglingStackException(Exception): pass

def repl(instream, outstream, interactive = False):
    context = Context()
    context['stdout'] = Stream(outstream)
    stack = []
    for line in instream:
        try:
            command = commandparser(''.join(stack + [line]))
            stack.clear()
        except pyparsing.ParseException:
            stack.append(line)
            continue
        try:
            execute(command, context)
        except (UnsupportedEntryException, NoSuchPathException, FileNotFoundError):
            if not interactive:
                raise
            traceback.print_exc(0)
    if stack:
        raise DanglingStackException(stack)

def main():
    repl(sys.stdin, sys.stdout, True)

if '__main__' == __name__:
    main()
