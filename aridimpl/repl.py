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
from .context import NoSuchPathException, UnsupportedEntryException
from .model import List, Entry

class DanglingStackException(Exception): pass

class NoSuchIndentException(Exception): pass

class DanglingPrefixException(Exception): pass

class MalformedEntryException(Exception): pass

class Repl:

    u = '[$\r\n]'
    pattern = re.compile(r"^\s+%s*|%s*\s+$|%s+" % (u, u, u))
    del u

    @classmethod
    def quote(cls, obj):
        try:
            return cls.pattern.sub(lambda m: "$'(%s)" % m.group(), obj)
        except TypeError:
            return obj

    def __init__(self, context, interactive = False):
        self.stack = []
        self.indent = ''
        self.prefix = None
        self.context = context
        self.interactive = interactive

    def __enter__(self):
        return self

    def printf(self, template, *args): # TODO: Replace with methods corresponding to directives.
        self(template % tuple(self.quote(a) for a in args))

    def __call__(self, line):
        try:
            command = commandparser(''.join(self.stack + [line]))
            del self.stack[:]
        except pyparsing.ParseException:
            self.stack.append(line)
            return
        indent = command.indent()
        common = min(len(self.indent), len(indent))
        if indent[:common] != self.indent[:common]:
            raise MalformedEntryException(command)
        if self.prefix is not None:
            if len(indent) <= len(self.indent):
                raise MalformedEntryException(command)
            self.context['prefix', indent] = List(self.prefix.words()) # XXX: Is words() necessary?
            self.prefix = None
        self.indent = indent
        prefix = self.context.resolved('prefix', indent)
        command = Entry(prefix.objs + command.resolvables)
        try:
            self.context.execute(command)
        except UnsupportedEntryException:
            self.prefix = command
        except (NoSuchPathException, OSError): # XXX: Or just any exception?
            if not self.interactive:
                raise
            traceback.print_exc(0)

    def __exit__(self, exc_type, *args):
        if exc_type is None:
            if self.stack:
                raise DanglingStackException(self.stack)
            if self.prefix is not None:
                raise DanglingPrefixException(self.prefix)
