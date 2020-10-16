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
from .directives import processtemplate, processtemplateimpl
from .model import Entry, Function, Number, Scalar, Text
from .repl import Repl
from .util import NoSuchPathException
from functools import partial
from itertools import chain
from weakref import WeakKeyDictionary
import os

ctrls = WeakKeyDictionary()

class ConfigCtrl:

    def __init__(self, config, context, prefix):
        self.config = config
        self.context = context
        self.prefix = prefix

    def printf(self, template, *args):
        with Repl(self.context) as repl:
            repl.printf(''.join(chain(("%s " for _ in self.prefix), [template])), *chain(self.prefix, args))

    def load(self, pathorstream):
        c = self._localcontext()
        (c.sourceimpl if getattr(pathorstream, 'readable', lambda: False)() else c.source)(Entry([]), pathorstream)

    def loadsettings(self):
        self.load(os.path.join(os.path.expanduser('~'), '.settings.arid'))

    def repl(self):
        assert not self.prefix # XXX: Support prefix?
        return Repl(self.context)

    def execute(self, text):
        with self.repl() as repl:
            for line in text.splitlines():
                repl(line)

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
        self.context[tuple(self.prefix) + path] = factory()

    def _localcontext(self):
        return self.context.resolved(*self.prefix)

    def __iter__(self):
        for k, o in self._localcontext().itero():
            try:
                yield k, o.value
            except AttributeError:
                yield k, type(self.config)(self.context, self.prefix + [k])

    def processtemplate(self, frompathorstream, topathorstream):
        c = self._localcontext()
        if getattr(frompathorstream, 'readable', lambda: False)():
            text = processtemplateimpl(c, frompathorstream)
        else:
            text = processtemplate(c, Text(frompathorstream))
        if getattr(topathorstream, 'writable', lambda: False)():
            topathorstream.write(text)
        else:
            with open(topathorstream, 'w') as g:
                g.write(text)

    def createchild(self): # XXX: Is _localcontext quite similar?
        assert not self.prefix
        return type(self.config)(self.context.createchild(), [])

    def unravel(self):
        return self._localcontext().unravel()

class Config(object):

    @classmethod
    def blank(cls):
        return cls(Context(), [])

    def __init__(self, context, prefix):
        ctrls[self] = ConfigCtrl(self, context, prefix)

    def __getattr__(self, name):
        ctrl = ctrls[self]
        path = ctrl.prefix + [name]
        try:
            obj = ctrl.context.resolved(*path) # TODO LATER: Guidance for how lazy non-scalars should be in this situation.
        except NoSuchPathException:
            raise AttributeError(' '.join(path))
        try:
            return obj.value # FIXME: Does not work for all kinds of scalar.
        except AttributeError:
            return type(self)(ctrl.context, path)

    def __iter__(self):
        for _, o in ctrls[self]:
            yield o

    def __invert__(self):
        return ctrls[self]
