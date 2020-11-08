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

class Precedence:

    void, = range(-1, 0)
    default, colon = range(2)

    @classmethod
    def ofdirective(cls, d):
        return getattr(d, 'precedence', cls.default)

lookup = {}

def directive(cls):
    obj = cls()
    lookup[Text(cls.name)] = obj
    return obj

@directive
class Colon:
    name = ':'
    precedence = Precedence.colon
    def __call__(self, prefix, suffix, context):
        context.execute(prefix, True)

@directive
class Redirect:
    name = 'redirect'
    def __call__(self, prefix, suffix, context):
        context['stdout',] = Stream(open(resolvepath(suffix.tophrase(), context), 'w'))

@directive
class Write:
    name = 'write'
    def __call__(self, prefix, suffix, context):
        context.resolved('stdout').flush(suffix.tophrase().resolve(context).cat())

@directive
class Source:
    name = '.'
    def __call__(self, prefix, suffix, context):
        # XXX: Use full algo to get phrasecontext?
        phrasecontext = context
        for word in prefix.topath(context):
            c = phrasecontext.resolvedcontextornone([word])
            if c is None:
                break
            phrasecontext = c
        suffix.tophrase().resolve(phrasecontext).source(context, prefix)

@directive
class CD:
    name = 'cd'
    def __call__(self, prefix, suffix, context):
        context['cwd',] = Text(resolvepath(suffix.tophrase(), context))

@directive
class Test:
    name = 'test'
    def __call__(self, prefix, suffix, context):
        sys.stderr.write(suffix.tophrase().resolve(context))
        sys.stderr.write(os.linesep)

@directive
class Equals:
    name = '='
    def __call__(self, prefix, suffix, context):
        context[prefix.topath(context)] = suffix.tophrase()

@directive
class ColonEquals:
    name = ':='
    def __call__(self, prefix, suffix, context):
        path = prefix.topath(context)
        context[path] = suffix.tophrase().resolve(context.getorcreatesubcontext(path[:-1]))

@directive
class PlusEquals:
    name = '+='
    def __call__(self, prefix, suffix, context):
        phrase = suffix.tophrase()
        context[prefix.topath(context) + (phrase.unparse(),)] = phrase

@directive
class Cat:
    name = '<'
    def __call__(self, prefix, suffix, context):
        context = context.getorcreatesubcontext(prefix.topath(context))
        context.resolved('stdout').flush(processtemplate(context, suffix.tophrase()))

def resolvepath(resolvable, context):
    return resolvable.resolve(context).pathvalue(context) # XXX: Could this be more OO?

def processtemplate(context, pathresolvable):
    path = resolvepath(pathresolvable, context)
    with open(path) as f, context.staticcontext().here.push(Text(os.path.dirname(path))):
        return processtemplateimpl(context, f)

def processtemplateimpl(context, f):
    with context.staticcontext().indent.push() as monitor:
        return Concat(templateparser(f.read()), monitor).resolve(context).cat()
