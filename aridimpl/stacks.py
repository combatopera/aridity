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

from .model import Resolvable, Text
from contextlib import contextmanager
import re

class ThreadLocalResolvable(Resolvable):

    def __init__(self, threadlocals, name):
        self.threadlocals = threadlocals
        self.name = name

    def resolve(self, context):
        return getattr(self.threadlocals, self.name).resolve(context)

class Stack:

    def __init__(self):
        self.stack = []

    @contextmanager
    def pushimpl(self, value):
        self.stack.append(value)
        try:
            yield value
        finally:
            self.stack.pop()

class SimpleStack(Stack):

    def push(self, value):
        return self.pushimpl(value)

    def resolve(self, context):
        return self.stack[-1]

class IndentStack(Stack):

    class Monitor:

        textblock = re.compile(r'(?:.*[\r\n]+)+')
        whitespace = re.compile(r'\s*')

        def __init__(self):
            self.parts = []

        def __call__(self, text):
            m = self.textblock.match(text)
            if m is None:
                self.parts.append(text)
            else:
                self.parts[:] = text[m.end():],

        def indent(self):
            return Text(self.whitespace.match(''.join(self.parts)).group())

    def push(self):
        return self.pushimpl(self.Monitor())

    def resolve(self, context):
        return self.stack[-1].indent()
