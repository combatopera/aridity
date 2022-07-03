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

from .model import Blank, Boolean, Boundary, Call, Concat, Entry, nullmonitor, Number, Text
from decimal import Decimal
from functools import reduce
from pyparsing import Forward, Literal, MatchFirst, NoMatch, OneOrMore, Optional, Regex, Suppress, ZeroOrMore
import operator, re

class AnyScalar:

    numberpattern = re.compile('^-?(?:[0-9]+|[0-9]*[.][0-9]+)$')
    booleans = {str(b).lower(): Boolean(b) for b in map(bool, range(2))}

    @classmethod
    def pa(cls, s, l, t):
        text, = t
        if text in cls.booleans:
            return cls.booleans[text]
        m = cls.numberpattern.search(text)
        return Text(text) if m is None else Number((Decimal if '.' in text else int)(text))

bracketpairs = '()', '[]'
idregex = r'[^\s$%s]*' % ''.join(re.escape(o) for o, _ in bracketpairs)
identifier = Regex("%s(?:[$]%s)*" % (idregex, idregex))

class ConcatPA:

    def __init__(self, monitor):
        self.monitor = monitor

    def template(self, s, l, t):
        return Concat(t, self.monitor)

    def brackets(self, s, l, t):
        return Concat(t[1:-1], self.monitor)

def _smartpa(s, l, t):
    return Concat.unlesssingleton(t.asList())

def _getarg(action, scalarpa, boundarychars):
    def gettext(pa):
        return Regex(r"[^$\s%s]+" % re.escape(boundarychars)).leaveWhitespace().setParseAction(pa)
    opttext = Optional(gettext(Text.pa))
    return (OneOrMore(opttext + action) + opttext | gettext(scalarpa)).setParseAction(_smartpa)

def _getoptblank(pa, boundarychars):
    return Optional(Regex(r"[^\S%s]+" % re.escape(boundarychars)).leaveWhitespace().setParseAction(pa))

class Parser:

    def __init__(self, g, singleton = True):
        self.g = g.parseWithTabs()
        self.singleton = singleton

    def __call__(self, text):
        result = self.g.parseString(text, parseAll = True).asList()
        if self.singleton:
            result, = result
        return result

class GFactory:

    scalarpa = AnyScalar.pa
    boundarychars = '\r\n'
    ormorecls = OneOrMore
    concatpa = ConcatPA(nullmonitor)

    @classmethod
    def create(cls, **kwargs):
        factory = cls()
        for k, v in kwargs.items():
            setattr(factory, k, v)
        return factory._create()

    def _create(self):
        def clauses():
            def getbrackets(blankpa, scalarpa):
                optblank = _getoptblank(blankpa, '')
                return Literal(o) + ZeroOrMore(optblank + _getarg(action, scalarpa, c)) + optblank + Literal(c)
            for o, c in bracketpairs:
                yield (Suppress(Regex("lit|'")) + Suppress(o) + Regex("[^%s]*" % re.escape(c)) + Suppress(c)).setParseAction(Text.pa)
                yield (Suppress(Regex('pass|[.]')) + getbrackets(Text.pa, Text.pa)).setParseAction(self.concatpa.brackets)
                yield (identifier + getbrackets(Blank.pa, AnyScalar.pa)).setParseAction(Call.pa)
        optblank = _getoptblank(Blank.pa, self.boundarychars)
        action = Forward()
        action << Suppress('$').leaveWhitespace() + MatchFirst(clauses()).leaveWhitespace()
        return reduce(operator.add, [
            self.ormorecls(optblank + _getarg(action, self.scalarpa, self.boundarychars)),
            optblank,
            Optional(Regex("[%s]+" % re.escape(self.boundarychars)).leaveWhitespace().setParseAction(Boundary.pa) if self.boundarychars else NoMatch()),
        ])

commandparser = Parser(GFactory.create(ormorecls = ZeroOrMore).setParseAction(Entry.pa))

def templateparser(monitor):
    concatpa = ConcatPA(monitor)
    return Parser(reduce(operator.or_, [
        GFactory.create(scalarpa = Text.pa, boundarychars = '', concatpa = concatpa).setParseAction(concatpa.template),
        Regex('^$').setParseAction(Text.pa),
    ]))
