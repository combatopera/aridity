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

import traceback, pyparsing, re
from .grammar import commandparser
from .model import Entry, Text

class DanglingStackException(Exception): pass

class NoSuchIndentException(Exception): pass

class MalformedEntryException(Exception): pass

class Repl:

    quotablebysquare = re.compile('[$)]+')

    @classmethod
    def _quote(cls, obj):
        try:
            from pathlib import PurePath
            if isinstance(obj, PurePath):
                obj = str(obj)
        except ImportError:
            pass
        try:
            return "$.(%s)" % cls.quotablebysquare.sub(lambda m: "$'[%s]" % m.group(), obj)
        except TypeError:
            return obj

    def __init__(self, context, interactive = False, rootprefix = Entry([])):
        self.stack = []
        self.indent = ''
        self.command = Entry([Text(':')])
        self.commandsize = self.command.size()
        self.partials = {'': rootprefix}
        self.context = context
        self.interactive = interactive

    def __enter__(self):
        return self

    def printf(self, template, *args): # TODO: Replace with methods corresponding to directives.
        self(template % tuple(self._quote(a) for a in args))

    def __call__(self, line):
        try:
            suffix = commandparser(''.join(self.stack + [line]))
            del self.stack[:]
        except pyparsing.ParseException:
            self.stack.append(line)
            return
        indent = suffix.indent()
        common = min(len(self.indent), len(indent))
        if indent[:common] != self.indent[:common]:
            raise MalformedEntryException(suffix)
        if len(indent) <= len(self.indent):
            self.fire()
            if indent not in self.partials:
                raise NoSuchIndentException(suffix)
        else:
            self.partials[indent] = self.command
        for i in list(self.partials):
            if len(indent) < len(i):
                del self.partials[i]
        self.command = Entry(self.partials[indent].resolvables + suffix.resolvables)
        self.commandsize = Entry(suffix.resolvables).size()
        self.indent = indent

    def fire(self):
        if self.commandsize:
            try:
                self.context.execute(self.command)
            except:
                if not self.interactive:
                    raise
                traceback.print_exc(0)

    def __exit__(self, exc_type, *args):
        if exc_type is None:
            if self.stack:
                raise DanglingStackException(self.stack)
            self.fire()
