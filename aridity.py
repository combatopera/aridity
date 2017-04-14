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

class DanglingStackException(Exception): pass

class Repl:

    u = '[$\r\n]'
    pattern = re.compile(r"^\s+%s*|%s*\s+$|%s+" % (u, u, u))
    del u

    @classmethod
    def quote(cls, obj):
        try:
            return cls.pattern.sub(lambda m: "$lit(%s)" % m.group(), obj)
        except TypeError:
            return obj

    def __init__(self, context, interactive = False):
        self.stack = []
        self.context = context
        self.interactive = interactive

    def __enter__(self):
        return self

    def printf(self, template, *args):
        self(template % tuple(self.quote(a) for a in args))

    def __call__(self, line):
        try:
            command = commandparser(''.join(self.stack + [line]))
            self.stack.clear()
        except pyparsing.ParseException:
            self.stack.append(line)
            return
        try:
            execute(command, self.context)
        except (UnsupportedEntryException, NoSuchPathException, FileNotFoundError):
            if not self.interactive:
                raise
            traceback.print_exc(0)

    def __exit__(self, *args):
        if self.stack:
            raise DanglingStackException(self.stack)

def main():
    context = Context()
    context['stdout'] = Stream(sys.stdout)
    with Repl(context, True) as repl:
        for line in sys.stdin:
            repl(line)

if '__main__' == __name__:
    main()
