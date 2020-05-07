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

from __future__ import with_statement
from .model import Text, Stream, Concat
from .grammar import templateparser
import os, sys

lookup = {}

def directive(cls):
    obj = cls()
    lookup[Text(cls.name)] = obj
    return obj

@directive
class Colon:
    name = ':'
    def __call__(self, prefix, phrase, context):
        pass # Do nothing.

@directive
class Redirect:
    name = 'redirect'
    def __call__(self, prefix, phrase, context):
        context['stdout',] = Stream(open(resolvepath(phrase, context), 'w'))

@directive
class Write:
    name = 'write'
    def __call__(self, prefix, phrase, context):
        context.resolved('stdout').flush(phrase.resolve(context).cat())

@directive
class Source:
    name = '.'
    def __call__(self, prefix, phrase, context):
        context.source(prefix, resolvepath(phrase, context))

@directive
class CD:
    name = 'cd'
    def __call__(self, prefix, phrase, context):
        context['cwd',] = Text(resolvepath(phrase, context))

@directive
class Test:
    name = 'test'
    def __call__(self, prefix, phrase, context):
        sys.stderr.write(phrase.resolve(context))
        sys.stderr.write(os.linesep)

@directive
class Equals:
    name = '='
    def __call__(self, prefix, phrase, context):
        context[prefix.topath(context)] = phrase

@directive
class ColonEquals:
    name = ':='
    def __call__(self, prefix, phrase, context):
        Equals(prefix, phrase.resolve(context), context)

@directive
class PlusEquals:
    name = '+='
    def __call__(self, prefix, phrase, context):
        context[prefix.topath(context) + (phrase.unparse(),)] = phrase

@directive
class Cat:
    name = '<'
    def __call__(self, prefix, phrase, context):
        context = context.getorcreatesubcontext(prefix.topath(context))
        context.resolved('stdout').flush(processtemplate(context, phrase))

def resolvepath(resolvable, context):
    path = resolvable.resolve(context).cat()
    return path if os.path.isabs(path) else os.path.join(context.resolved('cwd').cat(), path)

def processtemplate(context, pathresolvable):
    path = resolvepath(pathresolvable, context)
    static = context.staticcontext()
    with open(path) as f, static.here.push(Text(os.path.dirname(path))), static.indent.push() as monitor:
        return Concat(templateparser(f.read()), monitor).resolve(context).cat()
