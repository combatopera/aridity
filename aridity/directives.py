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

from .model import Stream, Text
import os, sys

class Precedence:

    void, = range(-1, 0)
    default, colon = range(2)

    @classmethod
    def ofdirective(cls, d):
        return getattr(d, 'precedence', cls.default)

lookup = {}

def _directive(cls):
    obj = cls()
    lookup[Text(cls.name)] = obj
    return obj

@_directive
class Colon:
    name = ':'
    precedence = Precedence.colon
    def __call__(self, prefix, suffix, scope):
        scope.execute(prefix, True)

@_directive
class Redirect:
    name = '!redirect'
    def __call__(self, prefix, suffix, scope):
        scope['stdout',] = Stream(suffix.tophrase().resolve(scope).openable(scope).open(True))

@_directive
class Write:
    name = '!write'
    def __call__(self, prefix, suffix, scope):
        scope.resolved('stdout').flush(suffix.tophrase().resolve(scope).cat())

@_directive
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
        # XXX: Pass phrasescope to openable?
        suffix.tophrase().resolve(phrasescope).openable(scope).source(scope, prefix)

@_directive
class CD:
    name = '!cd'
    def __call__(self, prefix, suffix, scope):
        scope['cwd',] = suffix.tophrase().resolve(scope).openable(scope)

@_directive
class Test:
    name = '!test'
    def __call__(self, prefix, suffix, scope):
        sys.stderr.write(str(suffix.tophrase().resolve(scope)))
        sys.stderr.write(os.linesep)

@_directive
class Equals:
    name = '='
    def __call__(self, prefix, suffix, scope):
        scope[prefix.topath(scope)] = suffix.tophrase()

@_directive
class ColonEquals:
    name = ':='
    def __call__(self, prefix, suffix, scope):
        path = prefix.topath(scope)
        scope[path] = suffix.tophrase().resolve(scope.getorcreatesubscope(path[:-1]))

@_directive
class PlusEquals:
    name = '+='
    def __call__(self, prefix, suffix, scope):
        from .functions import OpaqueKey
        phrase = suffix.tophrase()
        scope[prefix.topath(scope) + (OpaqueKey(),)] = phrase

@_directive
class Cat:
    name = '<'
    def __call__(self, prefix, suffix, scope):
        scope = scope.getorcreatesubscope(prefix.topath(scope))
        scope.resolved('stdout').flush(suffix.tophrase().resolve(scope).openable(scope).processtemplate(scope))
