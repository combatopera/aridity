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

from .context import Context, Resource
from .directives import processtemplate, processtemplateimpl
from .model import Entry, Function, Number, Scalar, Text, wrap
from .repl import Repl
from .util import CycleException, NoSuchPathException
from functools import partial
from itertools import chain
from pkg_resources import iter_entry_points # TODO: Port to new API.
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
    def _of(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    def __init__(self, basecontext = None, prefix = None):
        self.node = _newnode(self)
        self.basecontext = Context() if basecontext is None else basecontext
        self.prefix = [] if prefix is None else prefix

    def loadappconfig(self, mainfunction, moduleresource, encoding = 'ascii', settingsoptional = False):
        try:
            module_name, appname = mainfunction
        except TypeError:
            module_name = mainfunction.__module__
            attrs = tuple(mainfunction.__qualname__.split('.'))
            appname, = (ep.name for ep in iter_entry_points('console_scripts') if ep.module_name == module_name and ep.attrs == attrs)
        appconfig = self._loadappconfig(appname, Resource(module_name, moduleresource, encoding))
        try:
            self.loadsettings()
        except OSError as e:
            if not (settingsoptional and errno.ENOENT == e.errno):
                raise
            log.info("No such file: %s", e)
        return appconfig

    def _loadappconfig(self, appname, resource):
        resource.source(self.basecontext.getorcreatesubcontext(self.prefix + [appname]), Entry([]))
        return getattr(self.node, appname)

    def reapplysettings(self, appname):
        c = self.context(True).duplicate()
        c.label = Text(appname)
        c.parent[appname,] = c
        parent = self._of(c.parent)
        parent.loadsettings()
        return getattr(parent.node, appname)

    def printf(self, template, *args):
        with Repl(self.basecontext) as repl:
            repl.printf(''.join(chain(("%s " for _ in self.prefix), [template])), *chain(self.prefix, args))

    def load(self, pathorstream):
        c = self.context(True)
        (c.sourceimpl if getattr(pathorstream, 'readable', lambda: False)() else c.source)(Entry([]), pathorstream)

    def loadsettings(self):
        self.load(os.path.join(os.path.expanduser('~'), '.settings.arid'))

    def repl(self):
        assert not self.prefix # XXX: Support prefix?
        return Repl(self.basecontext)

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
        self.basecontext[tuple(self.prefix) + path] = factory()

    def context(self, strict = False):
        if strict:
            c = self.basecontext.resolvedcontextornone(self.prefix)
            assert c is not None
            return c
        return self.basecontext.resolved(*self.prefix) # TODO: Test what happens if it changes.

    def __iter__(self):
        for k, o in self.context().itero():
            try:
                yield k, o.scalar
            except AttributeError:
                yield k, self._of(self.basecontext, self.prefix + [k]).node

    def processtemplate(self, frompathorstream, topathorstream):
        c = self.context()
        if getattr(frompathorstream, 'readable', lambda: False)():
            text = processtemplateimpl(c, frompathorstream)
        else:
            text = processtemplate(c, Text(frompathorstream))
        if getattr(topathorstream, 'writable', lambda: False)():
            topathorstream.write(text)
        else:
            with open(topathorstream, 'w') as g:
                g.write(text)

    def free(self):
        return self._of(self.context()) # XXX: Strict?

    def createchild(self):
        return self._of(self.context(True).createchild())

    def __neg__(self):
        'Included for completeness, normally the node attribute should be used directly.'
        return self.node

class Config(object):

    def __getattr__(self, name):
        ctrl = ctrls[self]
        path = ctrl.prefix + [name]
        try:
            obj = ctrl.basecontext.resolved(*path) # TODO LATER: Guidance for how lazy non-scalars should be in this situation.
        except (CycleException, NoSuchPathException):
            raise AttributeError(' '.join(path))
        try:
            return obj.scalar
        except AttributeError:
            return ctrl._of(ctrl.basecontext, path).node

    def __iter__(self):
        for _, o in ctrls[self]:
            yield o

    def __neg__(self):
        return ctrls[self]

    def __setattr__(self, name, value):
        ctrls[self].context(True)[name,] = wrap(value)
