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

from .config import Config, ConfigCtrl
from .model import Boolean, Function, Number, Resource, Scalar, star, Text
from .util import ispy2, NoSuchPathException
from functools import wraps
from io import BytesIO, StringIO
from shutil import rmtree
from tempfile import mkdtemp
from unittest import TestCase
import os

def _flip(cls):
    def d(f):
        @wraps(f)
        def g(self, *args, **kwargs):
            try:
                f(self, *args, **kwargs)
            except cls:
                pass
            else:
                self.fail('You fixed a bug!')
        return g
    return d

class TestConfig(TestCase):

    def test_listdict(self):
        c = ConfigCtrl().node
        (-c).put('v', 'a', text = 'A')
        self.assertEqual(['A'], list(c.v))
        self.assertEqual(dict(a = 'A'), dict(-c.v))
        (-c).put('v', 'b', text = 'B')
        self.assertEqual(['A', 'B'], list(c.v))
        self.assertEqual(dict(a = 'A', b = 'B'), dict(-c.v))
        (-c).put('v', 'c', 'x', text = 'X')
        l = list(c.v)
        self.assertEqual(3, len(l))
        self.assertEqual('A', l[0])
        self.assertEqual('B', l[1])
        self.assertEqual(['X'], list(l[2]))
        self.assertEqual(dict(x = 'X'), dict(-l[2]))
        d = dict(-c.v)
        self.assertEqual(set('abc'), set(d.keys()))
        self.assertEqual('A', d['a'])
        self.assertEqual('B', d['b'])
        self.assertEqual(['X'], list(d['c']))
        self.assertEqual(dict(x = 'X'), dict(-d['c']))

    def test_printf(self):
        c = ConfigCtrl().node
        (-c).printf('woo a = b')
        (-c.woo).printf('c = d')
        self.assertEqual(['b', 'd'], list(c.woo))
        self.assertEqual(dict(a = 'b', c = 'd'), dict(-c.woo))
        self.assertEqual(dict(a = 'b', c = 'd'), (-c.woo).scope().unravel())

    def test_crosschildresolve(self):
        cc = ConfigCtrl()
        cc.printf('app xform = <$(data)>')
        cc.printf('app item data = woo')
        c = cc.node.app
        self.assertEqual(['app'], (-c).prefix)
        self.assertEqual('<woo>', c.item.xform)
        f = (-c).freectrl().node
        self.assertEqual([], (-f).prefix)
        self.assertEqual('<woo>', f.item.xform)
        h = (-c).childctrl().node
        self.assertEqual([], (-h).prefix)
        self.assertEqual('<woo>', h.item.xform)

    def test_tailmoresignificant(self):
        cc = ConfigCtrl()
        cc.printf('X Y := $fork()')
        cc.printf('Y Z = woo')
        cc.printf('Z = yay')
        c = cc.node
        self.assertEqual('woo', c.X.Y.Z)
        f = (-c.X.Y).freectrl().node
        self.assertEqual('yay', f.Z)

    def test_multibacktrack(self):
        cc = ConfigCtrl()
        cc.printf('A = woo')
        cc.printf('B C := $fork()')
        cc.printf('D E F := $fork()')
        c = cc.node
        self.assertEqual('woo', c.A)
        self.assertEqual('woo', c.B.A)
        self.assertEqual('woo', c.D.A)
        self.assertEqual('woo', c.B.C.A)
        self.assertEqual('woo', c.D.E.A)
        self.assertEqual('woo', c.D.E.F.A)
        self.assertEqual('woo', c.D.E.F.B.C.A)

    def source(self, scope, prefix):
        scope.sourceimpl(prefix, StringIO(self.sourcetext))

    def test_appnamelabel(self):
        self.sourcetext = u'n := $label()\nx y = $(n)'
        c = ConfigCtrl()._loadappconfig('The App', self)
        self.assertEqual('The App', c.n)
        self.assertEqual('The App', c.x.y)

    def test_loadlibconfig(self):
        c = ConfigCtrl().loadappconfig((__name__, 'CDEFGAB'), 'test_config/libconf.arid', settingsoptional = True)
        self.assertEqual('response', c.music)
        self.assertEqual('CDEFGAB', (-c).scope().label.scalar)

    def test_setattr(self):
        cc = ConfigCtrl()
        cc.node.p = 'yay'
        cc.node.q = 100
        cc.node.r = True
        cc.node.s = False
        cc.node.t = None
        cc.node.u = ord
        obj = cc.scope().resolved('p')
        self.assertIs(Text, type(obj))
        self.assertEqual('yay', obj.textvalue)
        self.assertEqual('yay', obj.scalar)
        self.assertEqual('yay', obj.unravel())
        obj = cc.scope().resolved('q')
        self.assertIs(Number, type(obj))
        self.assertEqual(100, obj.numbervalue)
        self.assertEqual(100, obj.scalar)
        self.assertEqual(100, obj.unravel())
        obj = cc.scope().resolved('r')
        self.assertIs(Boolean, type(obj))
        self.assertIs(True, obj.booleanvalue)
        self.assertIs(True, obj.scalar)
        self.assertIs(True, obj.unravel())
        obj = cc.scope().resolved('s')
        self.assertIs(Boolean, type(obj))
        self.assertIs(False, obj.booleanvalue)
        self.assertIs(False, obj.scalar)
        self.assertIs(False, obj.unravel())
        obj = cc.scope().resolved('t')
        self.assertIs(Scalar, type(obj))
        self.assertIs(None, obj.scalar) # No type-specific field.
        self.assertIs(None, obj.unravel())
        obj = cc.scope().resolved('u')
        self.assertIs(Function, type(obj))
        self.assertIs(ord, obj.functionvalue)
        self.assertIs(ord, obj.scalar)
        self.assertIs(ord, obj.unravel())

    def test_multiscalar(self):
        cc = ConfigCtrl()
        cc.execute('a = $(/)\nb = $(*)')
        c = cc.node
        self.assertEqual(os.sep, c.a)
        self.assertEqual(os.sep, getattr(c, '/'))
        obj = cc.scope().resolved('/')
        self.assertEqual(os.sep, obj.textvalue)
        self.assertEqual(os.sep, obj.scalar)
        self.assertEqual(os.sep, obj.unravel())
        self.assertNotEqual(os.sep, obj.functionvalue)
        self.assertEqual(star, c.b)
        self.assertEqual(star, getattr(c, '*'))
        obj = cc.scope().resolved('*')
        self.assertEqual(star, obj.functionvalue)
        self.assertEqual(star, obj.scalar)
        self.assertEqual(star, obj.unravel())
        self.assertNotEqual(star, obj.directivevalue)

    def test_badmap(self):
        cc = ConfigCtrl()
        cc.execute('badmap = $map($list(x y) base $(base)-$(name))')
        c = cc.node
        with self.assertRaises(AttributeError) as cm:
            c.badmap
        self.assertEqual(('badmap',), cm.exception.args)
        cc.execute('name = woo')
        self.assertEqual(['x-woo', 'y-woo'], list(c.badmap))

    def test_resolvescope(self):
        cc = ConfigCtrl()
        cc.execute('boot name = leaf')
        cc.execute('boot dirs = $map($list(x y) d $/($(d) $(name)))')
        cc.execute('boot common name = com')
        c = cc.node
        obj = c.boot.dirs
        self.assertIs(Config, type(obj))
        self.assertEqual([os.path.join('x', 'leaf'), os.path.join('y', 'leaf')], list(obj))
        obj = c.boot.common.dirs
        self.assertIs(Config, type(obj))
        self.assertEqual([os.path.join('x', 'com'), os.path.join('y', 'com')], list(obj))

    def test_cliref(self):
        from argparse import ArgumentParser
        cc = ConfigCtrl()
        cc.execute('app ago = $(cli ago)s')
        cc.execute('app cli := $fork()')
        c = cc.node.app
        ap = ArgumentParser()
        ap.add_argument('ago')
        ap.parse_args(['1 day'], c.cli)
        self.assertEqual('1 days', c.ago)

    def test_resourcecwd(self):
        cc = ConfigCtrl()
        cc.scope()['cwd',] = Resource(__name__, 'test_config')
        cc.execute('. chess.arid')
        self.assertEqual('gambit', cc.node.queen)

    def test_textcwd(self):
        cc = ConfigCtrl()
        cc.node.cwd = os.path.join(os.path.dirname(__file__), 'test_config')
        cc.execute('. chess.arid')
        self.assertEqual('gambit', cc.node.queen)

    @_flip(AttributeError)
    def test_assigntopath(self):
        config = ConfigCtrl().node
        config.foo.bar = 'yay'
        self.assertEqual('yay', config.foo.bar)

    @_flip(AssertionError)
    def test_listsuffixoverride(self):
        cc = ConfigCtrl()
        cc.execute('item suffix = default')
        cc.execute('those items += foo-$(item suffix)')
        cc.execute('those items += bar-$(item suffix)')
        cc.execute('env eranu code no = 1')
        cc.execute('env uvavu code no = 2')
        cc.execute('env uvavu item suffix = override')
        c = cc.node
        eranu = c.env.eranu
        uvavu = c.env.uvavu
        self.assertEqual(1, eranu.code.no)
        self.assertEqual(2, uvavu.code.no)
        self.assertEqual(['foo-default', 'bar-default'], list(eranu.those.items))
        self.assertEqual(['foo-override', 'bar-override'], list(uvavu.those.items))

    def test_spread(self):
        c = ConfigCtrl().node
        (-c).execute('''v +=
    x
    y
    $*$(z)
z = $list(a b)
j = $join($(v) ,)''')
        self.assertEqual('x,y,a,b', c.j)
        self.assertEqual(['x', 'y', 'a', 'b'], list(c.v))

    def test_spread2(self):
        c = ConfigCtrl().node
        (-c).execute('''n v +=
    x
    y
    $*$map($(z) $lower($()))
z +=
    A
    B''')
        self.assertEqual(['x', 'y', 'a', 'b'], list(c.n.v))
        self.assertEqual(['x', 'y', 'a', 'b'], list((-c.n).freectrl().node.v))

    def test_nestedspread(self):
        c = ConfigCtrl().node
        (-c).execute('''a +=
    x
    $*$(b)
b += $*$(c)
c += y
b += z''')
        self.assertEqual(['x', 'y', 'z'], list(c.a))
        (-c).execute('c = $list()')
        self.assertEqual(['x', 'z'], list(c.a))

    def test_spreadfunc(self):
        def f(): pass
        def g(): pass
        c = ConfigCtrl().node
        c.f = f
        c.g = g
        (-c).execute('''v +=
    $(f)
    $*$(w)
w += $(g)''')
        self.assertEqual([f, g], list(c.v))

    def test_configfunction(self):
        cc = ConfigCtrl()
        cc.execute('lib hcllist = [$join($map($(elements) $hclstr($())) $.(, ))]')
        cc.execute(r'''tf
    stuffcalc elements +=
        foo
        bar
    stuff = $(stuffcalc lib hcllist)
    other
        elements += "\
        result = $(lib hcllist)''')
        self.assertEqual('["foo", "bar"]', cc.node.tf.stuff)
        self.assertEqual(r'["\"\\"]', cc.node.tf.other.result)

    def test_anchor(self):
        cc = ConfigCtrl()
        cc.execute('''TOP = $()
x = 200
y
    x
        ` = $()
        x = 100
        y
            x = $(` x)
            y = $(TOP x)''')
        self.assertEqual(100, cc.node.y.x.y.x)
        self.assertEqual(200, cc.node.y.x.y.y)

class TestLoading(TestCase):

    def setUp(self):
        def w(name, text):
            with open(os.path.join(self.d, name), 'w') as f:
                f.write(text)
        self.d = mkdtemp()
        w('9.arid', 'woo = yay')
        w('9.txt', 'yay')
        w('h.arid', '. $./(9.arid)')
        w('c.arid', '. 9.arid')
        w('h.aridt', '$readfile$./(9.txt)')
        w('c.aridt', '$readfile(9.txt)')

    def tearDown(self):
        rmtree(self.d)

    def test_loadabshere(self):
        cc = ConfigCtrl()
        cc.load(os.path.join(self.d, 'h.arid'))
        self.assertEqual('yay', cc.node.woo)

    @_flip(NoSuchPathException)
    def test_loadrelhere(self):
        cc = ConfigCtrl()
        cc.load(os.path.relpath(os.path.join(self.d, 'h.arid')))
        self.assertEqual('yay', cc.node.woo)

    def test_ptabshere(self):
        stream = (BytesIO if ispy2 else StringIO)()
        ConfigCtrl().processtemplate(os.path.join(self.d, 'h.aridt'), stream)
        self.assertEqual('yay', stream.getvalue())

    @_flip(NoSuchPathException)
    def test_ptrelhere(self):
        stream = (BytesIO if ispy2 else StringIO)()
        ConfigCtrl().processtemplate(os.path.relpath(os.path.join(self.d, 'h.aridt')), stream)
        self.assertEqual('yay', stream.getvalue())

    def test_loadabscwdfail(self):
        cc = ConfigCtrl()
        with self.assertRaises(NoSuchPathException) as cm:
            cc.load(os.path.join(self.d, 'c.arid'))
        self.assertEqual((('cwd',),), cm.exception.args)

    def test_loadrelcwdfail(self):
        cc = ConfigCtrl()
        with self.assertRaises(NoSuchPathException) as cm:
            cc.load(os.path.relpath(os.path.join(self.d, 'c.arid')))
        self.assertEqual((('cwd',),), cm.exception.args)

    def test_ptabscwdfail(self):
        stream = (BytesIO if ispy2 else StringIO)()
        with self.assertRaises(NoSuchPathException) as cm:
            ConfigCtrl().processtemplate(os.path.join(self.d, 'c.aridt'), stream)
        self.assertEqual((('cwd',),), cm.exception.args)

    def test_ptrelcwdfail(self):
        stream = (BytesIO if ispy2 else StringIO)()
        with self.assertRaises(NoSuchPathException) as cm:
            ConfigCtrl().processtemplate(os.path.relpath(os.path.join(self.d, 'c.aridt')), stream)
        self.assertEqual((('cwd',),), cm.exception.args)

    def test_loadabscwdabs(self):
        cc = ConfigCtrl()
        cc.node.cwd = self.d
        cc.load(os.path.join(self.d, 'c.arid'))
        self.assertEqual('yay', cc.node.woo)

    def test_loadrelcwdabs(self):
        cc = ConfigCtrl()
        cc.node.cwd = self.d
        cc.load(os.path.relpath(os.path.join(self.d, 'c.arid')))
        self.assertEqual('yay', cc.node.woo)

    def test_ptabscwdabs(self):
        stream = (BytesIO if ispy2 else StringIO)()
        cc = ConfigCtrl()
        cc.node.cwd = self.d
        cc.processtemplate(os.path.join(self.d, 'c.aridt'), stream)
        self.assertEqual('yay', stream.getvalue())

    def test_ptrelcwdabs(self):
        stream = (BytesIO if ispy2 else StringIO)()
        cc = ConfigCtrl()
        cc.node.cwd = self.d
        cc.processtemplate(os.path.relpath(os.path.join(self.d, 'c.aridt')), stream)
        self.assertEqual('yay', stream.getvalue())

    @_flip(RuntimeError)
    def test_loadabscwdrel(self):
        cc = ConfigCtrl()
        cc.node.cwd = os.path.relpath(self.d)
        cc.load(os.path.join(self.d, 'c.arid'))
        self.assertEqual('yay', cc.node.woo)

    @_flip(RuntimeError)
    def test_loadrelcwdrel(self):
        cc = ConfigCtrl()
        cc.node.cwd = os.path.relpath(self.d)
        cc.load(os.path.relpath(os.path.join(self.d, 'c.arid')))
        self.assertEqual('yay', cc.node.woo)

    def test_ptabscwdrel(self):
        stream = (BytesIO if ispy2 else StringIO)()
        cc = ConfigCtrl()
        cc.node.cwd = os.path.relpath(self.d)
        cc.processtemplate(os.path.join(self.d, 'c.aridt'), stream)
        self.assertEqual('yay', stream.getvalue())

    def test_ptrelcwdrel(self):
        stream = (BytesIO if ispy2 else StringIO)()
        cc = ConfigCtrl()
        cc.node.cwd = os.path.relpath(self.d)
        cc.processtemplate(os.path.relpath(os.path.join(self.d, 'c.aridt')), stream)
        self.assertEqual('yay', stream.getvalue())
