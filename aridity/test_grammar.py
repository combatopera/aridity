import unittest, pyparsing
from .grammar import expressionparser as p, loader as l, Text, Call, Blank, Concat, Number, Boolean, Function, Entry, List
from decimal import Decimal
from .context import Context

class Functions:

    def get(context, key):
        return context[key.resolve(context, None).cat()]

    def a(context):
        return Text('A')

    def ac(context, x):
        return Text('ac.' + x.resolve(context, None).cat())

    def id(context, x):
        return x

    def act(context, x, y):
        return Text('act.' + x.resolve(context, None).cat() + '.' + y.resolve(context, None).cat())

class TestGrammar(unittest.TestCase):

    def test_parser(self):
        ae = self.assertEqual
        ae([Text('x')], p('x'))
        ae([Text('yy')], p('yy'))
        ae([Text('x'), Blank('  '), Text('y')], p('x  y'))
        ae([Blank('\t'), Text('x'), Blank('  '), Text('y'), Blank('\r')], p('\tx  y\r'))
        for text in ('$a()',
                     '$a[]'):
            ae([Call('a', [])], p(text))
        for text in ('$ac(x)',
                     '$ac[x]'):
            ae([Call('ac', [Text('x')])], p(text))
        for text in ('$act(x yy)',
                     '$act[x yy]'):
            ae([Call('act', [Text('x'), Blank(' '), Text('yy')])], p(text))
        for text in ('$act(\rx  yy\t)',
                     '$act[\rx  yy\t]'):
            ae([Call('act', [Blank('\r'), Text('x'), Blank('  '), Text('yy'), Blank('\t')])], p(text))
        for text in ('$act(\rx$b()z  yy\t)',
                     '$act(\rx$b[]z  yy\t)',
                     '$act[\rx$b[]z  yy\t]',
                     '$act[\rx$b()z  yy\t]'):
            ae([Call('act', [Blank('\r'), Concat([Text('x'), Call('b', []), Text('z')]), Blank('  '), Text('yy'), Blank('\t')])], p(text))
        ae([], p(''))
        ae([Text('woo')], p('woo'))
        ae([Text('woo'), Call('get', [Text('yay')]), Text('houpla')], p('woo$get(yay)houpla'))
        ae([Text('woo'), Blank(' '), Call('get', [Blank('\n '), Text('yay'), Blank('\n')]), Blank('\t'), Text('houpla'), Blank('  ')], p('''woo $get(
 yay
)\thoupla  '''))
        ae([Number(1)], p('1'))
        ae([Number(-5)], p('-5'))
        ae([Call('id', [Number(Decimal('.1'))])], p('$id(.1)'))
        ae([Call('id', [Number(Decimal('-5.4'))])], p('$id(-5.4)'))
        ae([Call('id', [Text('.1woo')])], p('$id(.1woo)'))
        ae([Text('100woo')], p('100woo'))
        ae([Boolean(False)], p('false'))
        ae([Call('id', [Boolean(True)])], p('$id(true)'))
        ae([Call('id', [Text('falseyay')])], p('$id(falseyay)'))
        ae([Text('truewoo')], p('truewoo'))
        ae([Text('100'), Call('a', [])], p('100$a()'))

    def test_loader(self):
        ae = self.assertEqual
        ae([], l(''))
        ae([Entry('x', [])], l('x='))
        ae([Entry('x', [])], l('x=  '))
        ae([Entry('x', [Text('y'), Blank('  '), Text('z')])], l('x = y  z\t'))
        ae([Entry('x', [Text('y')]), Entry('x2', [Text('y2')])], l('x=y\nx2=y2'))
        ae([Entry('x', [Boolean(True)])], l('x = true'))
        ae([Entry('x', [Boolean(True)])], l('x =true '))

    def test_resolve(self):
        c = dict([name, Function(getattr(Functions, name))] for name in ['a', 'ac', 'act', 'id', 'get'])
        c['minus124'] = Number(-124)
        c['minus124txt'] = Text('minus124')
        ae = self.assertEqual
        ae(Text(''), Text('').resolve(None, None))
        ae(Text('\r\n\t'), Text('\r\n\t').resolve(None, None))
        ae(Text('A'), Call('a', []).resolve(c, None))
        ae(Text('A'), Call('a', [Blank('   ')]).resolve(c, None))
        ae(Text('ac.woo'), Call('ac', [Blank('\t'), Text('woo')]).resolve(c, None))
        ae(Text('act.woo.yay'), Call('act', [Text('woo'), Blank(' '), Text('yay')]).resolve(c, None))
        ae(Number(-123), Call('id', [Number(-123)]).resolve(c, None))
        ae(Number(-124), Call('get', [Text('minus124')]).resolve(c, None))
        ae(Text('ac.A'), Call('ac', [Call('a', [])]).resolve(c, None))
        ae(Text('xy'), Concat([Text('x'), Text('y')]).resolve(c, None))
        ae(Number(-124), Call('get', [Call('get', [Text('minus124txt')])]).resolve(c, None))

    def test_lit(self):
        ae = self.assertEqual
        ae([Text('$doesNotExist(]')], p('$lit($doesNotExist(])'))
        ae([Text('$doesNotExist[)')], p('$lit[$doesNotExist[)]'))
        ae([Text(' \t')], p('$lit[ \t]'))
        ae([Text('10')], p('$lit[10]'))

    def test_pass(self):
        ae = self.assertEqual
        ae([Text(' '), Text('x'), Text('  '), Text('y'), Text('\t')], p('$pass( x  y\t)'))
        ae([Text(' '), Text('x'), Text('  '), Text('y'), Text('\t')], p('$pass[ x  y\t]'))
        actual = p('$act(x $pass[ y\t])')
        ae([Call('act', [Text('x'), Blank(' '), Concat([Text(' '), Text('y'), Text('\t')])])], actual)
        c = dict([name, Function(getattr(Functions, name))] for name in ['act'])
        ae(Text('act.x. y\t'), Concat(actual).resolve(c, None))
        ae([Text('10')], p('$pass[10]'))
        ae([Text('x('), Blank(' '), Text(')')], p('$pass(x() )'))
        ae([Text('x()'), Text(' ')], p('$pass[x() ]'))
        ae(Text('act.x. '), Concat(p('$act(x $pass( ))')).resolve(c, None))
        ae(Text(' 100'), Concat(p('$pass( 100)')).resolve(c, None))

    def test_whitespace(self):
        ae = self.assertEqual
        ae([Blank(' '), Text(' x '), Blank(' ')], p(' $lit( x ) '))
        ae([Blank(' '), Text(' '), Text('x'), Text(' '), Blank(' ')], p(' $pass( x ) '))
        for name in 'lit', 'pass':
            for text in (' $ %s( x ) ' % name,
                         ' $%s ( x ) ' % name):
                with self.assertRaises(pyparsing.ParseException):
                    p(text)

    def test_map(self):
        call, = p('$map($list(a b c) x $get(x)2)')
        self.assertEqual(List([Text('a2'), Text('b2'), Text('c2')]), call.resolve(Context(), None))

    def test_join(self):
        call, = p('$join($list(a bb ccc) -)')
        self.assertEqual(Text('a-bb-ccc'), call.resolve(Context(), None))
