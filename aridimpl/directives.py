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

from .model import Text, Stream, Entry
import os, sys

lookup = {}

def directive(cls):
    lookup[Text(cls.name)] = cls()

@directive
class Redirect:
    name = 'redirect'
    def __call__(self, phrase, context):
        context['stdout',] = Stream(open(resolvepath(phrase, context), 'w'))

@directive
class Write:
    name = 'write'
    def __call__(self, phrase, context):
        context.resolved('stdout').flush(phrase.resolve(context).cat())

@directive
class Source:
    name = 'source'
    def __call__(self, phrase, context):
        context.source(Entry([]), resolvepath(phrase, context))

@directive
class CD:
    name = 'cd'
    def __call__(self, phrase, context):
        context['cwd',] = Text(resolvepath(phrase, context))

@directive
class Test:
    name = 'test'
    def __call__(self, phrase, context):
        sys.stderr.write(phrase.resolve(context))
        sys.stderr.write(os.linesep)

def resolvepath(phrase, context):
    path = phrase.resolve(context).cat()
    return path if os.path.isabs(path) else os.path.join(context.resolved('cwd').cat(), path)
