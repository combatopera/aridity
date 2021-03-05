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

from .model import Resolvable, Text
from .util import NoSuchPathException
from contextlib import contextmanager
import re

class ThreadLocalResolvable(Resolvable):

    def __init__(self, threadlocals, name):
        self.threadlocals = threadlocals
        self.name = name

    def resolve(self, scope):
        return getattr(self.threadlocals, self.name).resolve(scope)

class Stack:

    def __init__(self, label):
        self.stack = []
        self.label = label

    @contextmanager
    def pushimpl(self, value):
        self.stack.append(value)
        try:
            yield value
        finally:
            self.stack.pop()

    def head(self):
        try:
            return self.stack[-1]
        except IndexError:
            raise NoSuchPathException("Head of thread-local stack: %s" % self.label)

class SimpleStack(Stack):

    def push(self, value):
        return self.pushimpl(value)

    def resolve(self, scope):
        return self.head()

class IndentStack(Stack):

    class Monitor:

        nontrivialtextblock = re.compile(r'(?:.*[\r\n]+)+')
        indentpattern = re.compile(r'\s*')

        def __init__(self):
            self.parts = []

        def __call__(self, text):
            m = self.nontrivialtextblock.match(text)
            if m is None:
                self.parts.append(text)
            else:
                self.parts[:] = text[m.end():],

        def indent(self):
            return Text(self.indentpattern.match(''.join(self.parts)).group())

    def push(self):
        return self.pushimpl(self.Monitor())

    def resolve(self, scope):
        return self.head().indent()
