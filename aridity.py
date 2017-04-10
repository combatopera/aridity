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

import sys, traceback, pyparsing, re
from aridityimpl.parser import commandparser
from aridityimpl.grammar import Stream
from aridityimpl.context import Context, NoSuchPathException
from aridityimpl.directives import execute, UnsupportedEntryException

class Script:

    u = '[$\r\n]'
    pattern = re.compile(r"^\s+%s*|%s*\s+$|%s+" % (u, u, u))
    del u

    def __init__(self):
        self.lines = []

    def quote(self, text):
        return self.pattern.sub(lambda m: "$lit(%s)" % m.group(), text)

    def __call__(self, template, *args):
        self.lines.append(template % tuple(self.quote(a) for a in args))

    def __iter__(self):
        return iter(self.lines)

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
