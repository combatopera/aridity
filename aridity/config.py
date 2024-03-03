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

from .model import Entry, Function, Locator, Number, Resource, Scalar, Stream, Text, wrap
from .repl import Repl
from .scope import Scope
from .util import CycleException, dotpy, NoSuchPathException, qualname, selectentrypoints, solo
from functools import partial
from itertools import chain
from weakref import WeakKeyDictionary
import errno, logging, os, sys

log = logging.getLogger(__name__)
ctrls = WeakKeyDictionary()

def _newnode(configcls, ctrl):
    node = configcls()
    ctrls[node] = ctrl
    return node

def _processmainfunction(mainfunction):
    module = mainfunction.__module__
    if '__main__' == module:
        p = sys.argv[0]
        name = os.path.basename(p)
        if '__main__.py' == name:
            stem = os.path.basename(os.path.dirname(p))
        else:
            assert name.endswith(dotpy)
            stem = name[:-len(dotpy)]
        assert '-' not in stem
        appname = stem.replace('_', '-')
    else:
        attr = qualname(mainfunction)
        # FIXME: Requires metadata e.g. egg-info in projects that have not been installed:
        appname, = (ep.name for ep in selectentrypoints('console_scripts') if ep.module == module and ep.attr == attr)
    return module, appname

class ForeignScopeException(Exception): pass

def _wrappathorstream(pathorstream):
    return (Stream if getattr(pathorstream, 'readable', lambda: False)() else Locator)(pathorstream)

class ConfigCtrl:

    @classmethod
    def _of(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    @property
    def r(self):
        return _newnode(RConfig, self)

    @property
    def w(self):
        return _newnode(WConfig, self)

    def __init__(self, basescope = None, prefix = None):
        self.node = _newnode(Config, self)
        self.basescope = Scope() if basescope is None else basescope
        self.prefix = [] if prefix is None else prefix

    def loadappconfig(self, mainfunction, moduleresource, encoding = 'ascii', settingsoptional = False):
        try:
            module_name, appname = mainfunction
        except TypeError:
            module_name, appname = _processmainfunction(mainfunction)
        appconfig = self._loadappconfig(appname, Resource(module_name, moduleresource, encoding))
        try:
            self.loadsettings()
        except (IOError, OSError) as e:
            if not (settingsoptional and errno.ENOENT == e.errno):
                raise
            log.info("No such file: %s", e)
        return appconfig

    def _loadappconfig(self, appname, resource):
        resource.source(self.basescope.getorcreatesubscope(self.prefix + [appname]), Entry([]))
        return getattr(self.node, appname)

    def reapplysettings(self, mainfunction):
        if hasattr(mainfunction, 'encode'):
            appname = mainfunction
        else:
            _, appname = _processmainfunction(mainfunction)
        s = self.scope(True).duplicate()
        s.label = Text(appname)
        p = solo(s.parents)
        p[appname,] = s
        parent = self._of(p)
        parent.loadsettings()
        return getattr(parent.node, appname)

    def printf(self, template, *args):
        with Repl(self.basescope) as repl:
            repl.printf(''.join(chain(("%s " for _ in self.prefix), [template])), *chain(self.prefix, args))

    def load(self, pathorstream):
        s = self.scope(True)
        _wrappathorstream(pathorstream).source(s, Entry([]))

    def loadsettings(self):
        self.load(os.path.join(os.path.expanduser('~'), '.settings.arid'))

    def repl(self):
        assert not self.prefix # XXX: Support prefix?
        return Repl(self.basescope)

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
        self.basescope[tuple(self.prefix) + path] = factory()

    def scope(self, strict = False):
        if strict:
            s = self.basescope.resolvedscopeornone(self.prefix)
            if s is None:
                raise ForeignScopeException
            return s
        return self.basescope.resolved(*self.prefix) # TODO: Test what happens if it changes.

    def __iter__(self): # TODO: Add API to get keys without resolving values.
        for k, o in self.scope().resolveditems():
            try:
                yield k, o.scalar
            except AttributeError:
                yield k, self._of(self.basescope, self.prefix + [k]).node

    def processtemplate(self, frompathorstream, topathorstream):
        s = self.scope()
        text = _wrappathorstream(frompathorstream).processtemplate(s)
        if getattr(topathorstream, 'writable', lambda: False)():
            topathorstream.write(text)
        else:
            with open(topathorstream, 'w') as g:
                g.write(text)

    def freectrl(self):
        return self._of(self.scope()) # XXX: Strict?

    def childctrl(self):
        return self._of(self.scope(True).createchild())

    def addname(self, name):
        return self._of(self.basescope, self.prefix + [name])

    def resolve(self):
        return self.basescope.resolved(*self.prefix)

class Config(object):

    def __getattr__(self, name):
        ctrl = ctrls[self]
        path = ctrl.prefix + [name]
        try:
            obj = ctrl.basescope.resolved(*path) # TODO LATER: Guidance for how lazy non-scalars should be in this situation.
        except (CycleException, NoSuchPathException): # XXX: Should this really translate CycleException?
            raise AttributeError(' '.join(path))
        try:
            return obj.scalar
        except AttributeError:
            return ctrl._of(ctrl.basescope, path).node

    def __iter__(self):
        for _, o in ctrls[self]:
            yield o

    def __neg__(self):
        return ctrls[self]

    def __setattr__(self, name, value):
        ctrls[self].scope(True)[name,] = wrap(value)

class RConfig(object):

    def __getattr__(self, name):
        query = ctrls[self].addname(name)
        try:
            obj = query.resolve()
        except NoSuchPathException:
            raise AttributeError
        try:
            return obj.scalar
        except AttributeError:
            return query.r

class WConfig(object):

    def __getattr__(self, name):
        return ctrls[self].addname(name).w

    def __setattr__(self, name, value):
        query = ctrls[self].addname(name)
        query.basescope[tuple(query.prefix)] = wrap(value)
