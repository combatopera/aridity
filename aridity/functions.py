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

from __future__ import division
from .model import Boolean, Number, Text, wrap
from .util import allfunctions, dotpy, NoSuchPathException, realname
from importlib import import_module
import itertools, json, re, shlex

xmlentities = dict([c, "&%s;" % w] for c, w in [['"', 'quot'], ["'", 'apos']])
tomlbasicbadchars = re.compile('[%s]+' % re.escape(r'\"' + ''.join(chr(x) for x in itertools.chain(range(0x08 + 1), range(0x0A, 0x1F + 1), [0x7F]))))
zeroormoredots = re.compile('[.]*')

def _tomlquote(text):
    def repl(m):
        return ''.join(r"\u%04X" % ord(c) for c in m.group())
    return '"%s"' % tomlbasicbadchars.sub(repl, text)

class OpaqueKey(object):

    @classmethod
    def isopaque(cls, key):
        return all(cls.isopaque(k) for k in key) if isinstance(key, tuple) else isinstance(key, cls)

class Functions:

    from .keyring import gpg, keyring

    def screenstr(scope, resolvable):
        text = resolvable.resolve(scope).cat()
        return Text('"%s"' % text.replace('\\', '\\\\').replace('\n', '\\n').replace('"', '\\"'))

    def scstr(scope, resolvable):
        'SuperCollider string literal.'
        text = resolvable.resolve(scope).cat()
        return Text('"%s"' % text.replace('\\', '\\\\').replace('\n', '\\n').replace('"', '\\"'))

    def hclstr(scope, resolvable):
        text = resolvable.resolve(scope).cat()
        return Text('"%s"' % text.replace('\\', '\\\\').replace('\n', '\\n').replace('"', '\\"'))

    def groovystr(scope, resolvable):
        text = resolvable.resolve(scope).cat()
        return Text("'%s'" % text.replace('\\', '\\\\').replace('\n', '\\n').replace("'", "\\'"))

    def pystr(scope, resolvable):
        return Text(repr(resolvable.resolve(scope).scalar))

    def shstr(scope, resolvable):
        return Text(shlex.quote(resolvable.resolve(scope).cat()))

    def jsonquote(scope, resolvable):
        'Also suitable for YAML.'
        return Text(json.dumps(resolvable.resolve(scope).scalar))

    def xmlattr(scope, resolvable):
        from xml.sax.saxutils import quoteattr
        return Text(quoteattr(resolvable.resolve(scope).cat())) # TODO: Support booleans.

    def xmltext(scope, resolvable):
        'Suggest assigning this to & with xmlattr assigned to " as is convention.'
        from xml.sax.saxutils import escape
        return Text(escape(resolvable.resolve(scope).cat(), xmlentities))

    def tomlquote(scope, resolvable):
        return Text(_tomlquote(resolvable.resolve(scope).cat()))

    def urlquote(scope, resolvable):
        from urllib.parse import quote
        return Text(quote(resolvable.resolve(scope).cat(), safe = ''))

    def map(scope, objsresolvable, *args):
        from .scope import ScalarScope, Scope
        objs = objsresolvable.resolve(scope)
        parents = objs, scope
        if 1 == len(args):
            def context(k, v):
                try:
                    resolvables = v.resolvables
                except AttributeError:
                    s = ScalarScope(parents, v)
                else:
                    s = Scope(parents)
                    s.label = Text(k)
                    for i in resolvables.items():
                        s.resolvables.put(*i)
                return s
            resolvable, = args
        elif 2 == len(args):
            def context(k, v):
                s = Scope(parents)
                s[vname,] = v
                return s
            vname, resolvable = args
            vname = vname.resolve(scope).cat()
        else:
            def context(k, v):
                s = Scope(parents)
                s[kname,] = Text(k)
                s[vname,] = v
                return s
            kname, vname, resolvable = args
            kname = kname.resolve(scope).cat()
            vname = vname.resolve(scope).cat()
        result = Scope(islist = True) # XXX: Really no parent?
        for k, v in objs.resolveditems():
            result.resolvables.put(k, resolvable.resolve(context(k, v)))
        return result

    def flat(scope, listsresolvable):
        from .scope import Scope
        s = Scope(islist = True) # XXX: Really no parent?
        for lk, l in listsresolvable.resolve(scope).resolvables.items():
            for ok, obj in l.resolvables.items():
                s.resolvables.put((lk, ok), obj)
        return s

    def label(scope):
        return scope.label

    def join(scope, resolvables, *args):
        if args:
            r, = args
            separator = r.resolve(scope).cat()
        else:
            separator = ''
        s = resolvables.resolve(scope)
        return Text(separator.join(o.cat() for _, o in s.resolveditems()))

    def get(*args): return getimpl(*args)

    @realname('')
    def get_(*args): return getimpl(*args)

    @realname(',') # XXX: Oh yeah?
    def aslist(scope, *resolvables):
        return scope.resolved(*(r.resolve(scope).cat() for r in resolvables), **{'aslist': True})

    def str(scope, resolvable):
        return resolvable.resolve(scope).totext()

    def java(scope, resolvable):
        return resolvable.resolve(scope).tojava()

    def list(scope, *resolvables):
        v = scope.createchild(islist = True)
        for r in resolvables:
            v[OpaqueKey(),] = r
        return v

    def fork(scope):
        return scope.createchild()

    @realname('try')
    def try_(scope, *resolvables):
        for r in resolvables[:-1]:
            try:
                return r.resolve(scope)
            except NoSuchPathException:
                pass # XXX: Log it at a fine level?
        return resolvables[-1].resolve(scope)

    def mul(scope, *resolvables):
        x = 1
        for r in resolvables:
            x *= r.resolve(scope).scalar
        return Number(x)

    def div(scope, r, *resolvables):
        x = r.resolve(scope).scalar
        for r in resolvables:
            x /= r.resolve(scope).scalar
        return Number(x)

    def repr(scope, resolvable):
        return Text(repr(resolvable.resolve(scope).unravel()))

    @realname('./')
    def hereslash(scope, *resolvables):
        return scope.resolved('here').slash((r.resolve(scope).cat() for r in resolvables), False)

    def readfile(scope, resolvable):
        with resolvable.resolve(scope).openable(scope).open(False) as f:
            return Text(f.read())

    def processtemplate(scope, resolvable):
        return Text(resolvable.resolve(scope).openable(scope).processtemplate(scope))

    def lower(scope, resolvable):
        return Text(resolvable.resolve(scope).cat().lower())

    def pyref(scope, moduleresolvable, qualnameresolvable):
        def moduleobj():
            moduleref = moduleresolvable.resolve(scope).cat()
            leadingdots = len(zeroormoredots.match(moduleref).group())
            if not leadingdots:
                return import_module(moduleref)
            words = moduleref[leadingdots:].split('.')
            openable = scope.resolved('here').slash(['..'] * (leadingdots - 1) + words[:-1] + [words[-1] + dotpy], False)
            openablemodule = openable.modulenameornone()
            if openablemodule is not None:
                return import_module(openablemodule)
            class M:
                def __getattr__(self, name):
                    return g[name]
            g = {} # XXX: Set __name__ so it can do its own relative imports?
            with openable.open(False) as f:
                exec(f.read(), g)
            return M()
        pyobj = moduleobj()
        for name in qualnameresolvable.resolve(scope).cat().split('.'):
            pyobj = getattr(pyobj, name)
        return wrap(pyobj)

    @realname('\N{NOT SIGN}')
    def not_(scope, resolvable):
        return Boolean(not resolvable.resolve(scope).truth())

    def getfrom(scope, scoperesolvable, *resolvables):
        return scoperesolvable.resolve(scope).resolved(*(r.resolve(scope).cat() for r in resolvables))

def getimpl(scope, *resolvables):
    return scope.resolved(*(r.resolve(scope).cat() for r in resolvables))

def getfunctions():
    return allfunctions(Functions)
