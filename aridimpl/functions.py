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

from .model import Text, List, Fork, Number
from .util import allfunctions, NoSuchPathException, realname

class Functions:

    def screenstr(context, resolvable):
        text = resolvable.resolve(context).cat()
        return Text('"%s"' % text.replace('\\', '\\\\').replace('\n', '\\n').replace('"', '\\"'))

    def scstr(context, resolvable):
        text = resolvable.resolve(context).cat()
        return Text('"%s"' % text.replace('\\', '\\\\').replace('\n', '\\n').replace('"', '\\"'))

    def pystr(context, resolvable):
        return Text(repr(resolvable.resolve(context).cat()))

    def map(context, objs, *args):
        if 1 == len(args):
            expr, = args
            return List([expr.resolve(c) for c in objs.resolve(context)])
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
                for k, v in objs.resolve(context).objs.items():
                    c = context.createchild()
                    c[kname,] = Text(k)
                    c[vname,] = v
                    yield expr.resolve(c)
            return List(list(g()))

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
        return context.resolved(*(r.resolve(context).cat() for r in resolvables), aslist = True)

    def str(context, resolvable):
        return resolvable.resolve(context).totext()

    def java(context, resolvable):
        return resolvable.resolve(context).tojava()

    def list(context, *resolvables):
        return List([r.resolve(context) for r in resolvables])

    def fork(context):
        return Fork(context)

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

def getimpl(context, *resolvables):
    return context.resolved(*(r.resolve(context).cat() for r in resolvables))

def getfunctions():
    return allfunctions(Functions)
