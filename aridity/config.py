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

from .context import Context
from .model import Function, Number, Scalar, Text
from .repl import Repl
from .util import NoSuchPathException
from functools import partial
from importlib import import_module
from itertools import chain
import os

def _pyref(context, moduleresolvable, qualnameresolvable):
    pyobj = import_module(moduleresolvable.resolve(context).cat())
    for name in qualnameresolvable.resolve(context).cat().split('.'):
        pyobj = getattr(pyobj, name)
    return Function(pyobj) # FIXME LATER: Could be any type.

class Config(object):

    @classmethod
    def blank(cls):
        c = Context()
        c['pyref',] = Function(_pyref)
        return cls(c, [])

    def __init__(self, context, prefix):
        self._context = context
        self._prefix = prefix

    def printf(self, template, *args):
        with Repl(self._context) as repl:
            repl.printf(''.join(chain(("%s " for _ in self._prefix), [template])), *chain(self._prefix, args))

    def load(self, path):
        self.printf(". %s", path)

    def loadsettings(self):
        self.load(os.path.join(os.path.expanduser('~'), '.settings.arid'))

    def repl(self):
        assert not self._prefix # XXX: Support prefix?
        return Repl(self._context)

    def execute(self, text):
        with self.repl() as repl:
            for line in text.splitlines():
                repl(line)

    def __getattr__(self, name):
        path = self._prefix + [name]
        try:
            obj = self._context.resolved(*path) # TODO LATER: Guidance for how lazy non-scalars should be in this situation.
        except NoSuchPathException:
            raise AttributeError(name) # XXX: Misleading?
        try:
            return obj.value # FIXME: Does not work for all kinds of scalar.
        except AttributeError:
            return type(self)(self._context, path)

    def put(self, *path, **kwargs):
        def pairs():
            for t, k in [
                    [Function, 'function'],
                    [Number, 'number'],
                    [Scalar, 'scalar'],
                    [Text, 'text'],
                    [lambda x: x, 'resolvable']]:
                try:
                    yield t, kwargs[k]
                except KeyError:
                    pass
        # XXX: Support combination of types e.g. slash is both function and text?
        factory, = (partial(t, v) for t, v in pairs())
        self._context[tuple(self._prefix) + path] = factory()

    def _localcontext(self):
        return self._context.resolved(*self._prefix)

    def __iter__(self):
        for _, o in self.items():
            yield o

    def items(self):
        for k, o in self._localcontext().itero():
            try:
                yield k, o.value
            except AttributeError:
                yield k, type(self)(self._context, self._prefix + [k])

    def processtemplate(self, frompath, topath):
        with Repl(self._localcontext()) as repl:
            repl.printf("redirect %s", topath) # XXX: Could this modify the underlying context?
            repl.printf("< %s", frompath)

    def createchild(self): # XXX: Is _localcontext quite similar?
        assert not self._prefix
        return type(self)(self._context.createchild(), [])

    def unravel(self):
        return self._localcontext().unravel()
