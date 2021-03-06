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

from .grammar import templateparser
from .model import Concat, Stream, Text
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
    def __call__(self, prefix, suffix, scope):
        scope.execute(prefix, True)

@directive
class Redirect:
    name = 'redirect'
    def __call__(self, prefix, suffix, scope):
        scope['stdout',] = Stream(open(resolvepath(suffix.tophrase(), scope), 'w'))

@directive
class Write:
    name = 'write'
    def __call__(self, prefix, suffix, scope):
        scope.resolved('stdout').flush(suffix.tophrase().resolve(scope).cat())

@directive
class Source:
    name = '.'
    def __call__(self, prefix, suffix, scope):
        # XXX: Use full algo to get phrasescope?
        phrasescope = scope
        for word in prefix.topath(scope):
            s = phrasescope.resolvedscopeornone([word])
            if s is None:
                break
            phrasescope = s
        suffix.tophrase().resolve(phrasescope).source(scope, prefix)

@directive
class CD:
    name = 'cd'
    def __call__(self, prefix, suffix, scope):
        scope['cwd',] = Text(resolvepath(suffix.tophrase(), scope))

@directive
class Test:
    name = 'test'
    def __call__(self, prefix, suffix, scope):
        sys.stderr.write(suffix.tophrase().resolve(scope))
        sys.stderr.write(os.linesep)

@directive
class Equals:
    name = '='
    def __call__(self, prefix, suffix, scope):
        scope[prefix.topath(scope)] = suffix.tophrase()

@directive
class ColonEquals:
    name = ':='
    def __call__(self, prefix, suffix, scope):
        path = prefix.topath(scope)
        scope[path] = suffix.tophrase().resolve(scope.getorcreatesubscope(path[:-1]))

@directive
class PlusEquals:
    name = '+='
    def __call__(self, prefix, suffix, scope):
        phrase = suffix.tophrase()
        scope[prefix.topath(scope) + (phrase.unparse(),)] = phrase

@directive
class Cat:
    name = '<'
    def __call__(self, prefix, suffix, scope):
        scope = scope.getorcreatesubscope(prefix.topath(scope))
        scope.resolved('stdout').flush(processtemplate(scope, suffix.tophrase()))

def resolvepath(resolvable, scope):
    return resolvable.resolve(scope).pathvalue(scope) # TODO: Support resources.

def processtemplate(scope, pathresolvable):
    path = resolvepath(pathresolvable, scope)
    with open(path) as f, scope.staticscope().here.push(Text(os.path.dirname(path))):
        return processtemplateimpl(scope, f)

def processtemplateimpl(scope, f):
    with scope.staticscope().indent.push() as monitor:
        return Concat(templateparser(f.read()), monitor).resolve(scope).cat()
