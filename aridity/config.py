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
from io import TextIOWrapper
from itertools import chain
from pkg_resources import iter_entry_points, resource_stream
from weakref import WeakKeyDictionary
import errno, logging, os

log = logging.getLogger(__name__)
ctrls = WeakKeyDictionary()

def _newnode(ctrl):
    node = Config()
    ctrls[node] = ctrl
    return node

class ConfigCtrl:

    @classmethod
    def _node(cls, context, prefix):
        def init(self):
            self.context = context
            self.prefix = prefix
        return cls(init).node

    def __init__(self, init = None):
        self.node = _newnode(self)
        if init is None:
            self.context = Context()
            self.prefix = []
        else:
            init(self)

    def loadappconfig(self, mainfunction, moduleresource, settingsoptional = False):
        module_name = mainfunction.__module__
        attrs = tuple(mainfunction.__qualname__.split('.'))
        appname, = (ep.name for ep in iter_entry_points('console_scripts') if ep.module_name == module_name and ep.attrs == attrs)
        self.context.getorcreatesubcontext(self.prefix + [appname])
        appconfig = getattr(self.node, appname)
        with TextIOWrapper(resource_stream(module_name, moduleresource)) as f: # TODO: System encoding not appropriate here.
            (-appconfig).load(f)
        try:
            self.loadsettings()
        except OSError as e:
            if not (settingsoptional and errno.ENOENT == e.errno):
                raise
            log.info("No such file: %s", e)
        return appconfig

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
                yield k, self._node(self.context, self.prefix + [k])

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
        return self._node(self.context.createchild(), [])

    def unravel(self):
        return self._localcontext().unravel()

    def __neg__(self):
        'Included for completeness, normally the node attribute should be used directly.'
        return self.node

class Config(object):

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
            return ctrl._node(ctrl.context, path)

    def __iter__(self):
        for _, o in ctrls[self]:
            yield o

    def __neg__(self):
        return ctrls[self]
