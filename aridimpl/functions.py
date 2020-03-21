# Copyright 2017 Andrzej Cichocki

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
from .grammar import templateparser
from .model import Concat, List, Number, Text
from .util import allfunctions, NoSuchPathException, realname
import json, os, shlex

class Functions:

    def screenstr(context, resolvable):
        text = resolvable.resolve(context).cat()
        return Text('"%s"' % text.replace('\\', '\\\\').replace('\n', '\\n').replace('"', '\\"'))

    def scstr(context, resolvable):
        'SuperCollider string literal.'
        text = resolvable.resolve(context).cat()
        return Text('"%s"' % text.replace('\\', '\\\\').replace('\n', '\\n').replace('"', '\\"'))

    def hclstr(context, resolvable):
        text = resolvable.resolve(context).cat()
        return Text('"%s"' % text.replace('\\', '\\\\').replace('\n', '\\n').replace('"', '\\"'))

    def groovystr(context, resolvable):
        text = resolvable.resolve(context).cat()
        return Text("'%s'" % text.replace('\\', '\\\\').replace('\n', '\\n').replace("'", "\\'"))

    def pystr(context, resolvable):
        return Text(repr(resolvable.resolve(context).cat()))

    def shstr(context, resolvable):
        return Text(shlex.quote(resolvable.resolve(context).cat()))

    def jsonquote(context, resolvable):
        'Also suitable for YAML.'
        return Text(json.dumps(resolvable.resolve(context).value))

    def map(context, objs, *args):
        if 1 == len(args):
            expr, = args
            def g():
                for k, v in objs.resolve(context).resolvables.items():
                    c = v.createchild()
                    c.label = Text(k)
                    yield expr.resolve(c)
            return List(list(g()))
        elif 2 == len(args):
            name, expr = args
            name = name.resolve(context).cat()
            def g():
                for obj in objs.resolve(context):
                    c = context.createchild()
                    c[name,] = obj
                    yield expr.resolve(c)
            return List(list(g()))
        else:
            kname, vname, expr = args
            kname = kname.resolve(context).cat()
            vname = vname.resolve(context).cat()
            def g():
                for k, v in objs.resolve(context).resolvables.items():
                    c = context.createchild()
                    c[kname,] = Text(k)
                    c[vname,] = v
                    yield expr.resolve(c)
            return List(list(g()))

    def label(context):
        return context.label

    def join(context, resolvables, *args):
        if args:
            r, = args
            separator = r.resolve(context).cat()
        else:
            separator = ''
        return Text(separator.join(r.cat() for r in resolvables.resolve(context)))

    def get(*args): return getimpl(*args)

    @realname('')
    def get_(*args): return getimpl(*args)

    @realname(',') # XXX: Oh yeah?
    def aslist(context, *resolvables):
        return context.resolved(*(r.resolve(context).cat() for r in resolvables), **{'aslist': True})

    def str(context, resolvable):
        return resolvable.resolve(context).totext()

    def java(context, resolvable):
        return resolvable.resolve(context).tojava()

    def list(context, *resolvables):
        v = context.createchild(islist = True)
        for r in resolvables:
            v[r.unparse(),] = r
        return v

    def fork(context):
        return context.createchild()

    @realname('try')
    def try_(context, *resolvables):
        for r in resolvables[:-1]:
            try:
                return r.resolve(context)
            except NoSuchPathException:
                pass
        return resolvables[-1].resolve(context)

    def mul(context, *resolvables):
        x = 1
        for r in resolvables:
            x *= r.resolve(context).value
        return Number(x)

    def div(context, r, *resolvables):
        x = r.resolve(context).value
        for r in resolvables:
            x /= r.resolve(context).value
        return Number(x)

    def repr(context, resolvable):
        return Text(repr(resolvable.resolve(context).unravel()))

    @realname('./')
    def hereslash(context, *resolvables):
        return Text(os.path.join(context.resolved('here').cat(), *(r.resolve(context).cat() for r in resolvables)))

    def readfile(context, resolvable):
        with open(resolvable.resolve(context).cat()) as f:
            return Text(f.read())

    def processtemplate(context, resolvable):
        with open(resolvable.resolve(context).cat()) as f:
            return Text(Concat(templateparser(f.read())).resolve(context).cat()) # TODO: Duplicated code.

def getimpl(context, *resolvables):
    return context.resolved(*(r.resolve(context).cat() for r in resolvables))

def getfunctions():
    return allfunctions(Functions)
