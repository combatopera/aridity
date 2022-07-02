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

from .model import Blank, Boolean, Boundary, Call, Concat, Entry, Number, Text
from decimal import Decimal
from pyparsing import Forward, Literal, MatchFirst, NoMatch, OneOrMore, Optional, Regex, Suppress, ZeroOrMore
import re

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

def _getoptblank(pa, boundarychars):
    return Optional(Regex(r"[^\S%s]+" % re.escape(boundarychars)).leaveWhitespace().setParseAction(pa))

def _gettext(pa, boundarychars):
    return Regex(r"[^$\s%s]+" % re.escape(boundarychars)).leaveWhitespace().setParseAction(pa)

def _getoptboundary(pa, boundarychars):
    return Optional(Regex("[%s]+" % re.escape(boundarychars)).leaveWhitespace().setParseAction(pa) if boundarychars else NoMatch())

def _getaction():
    def clauses():
        def getbrackets(blankpa, scalarpa):
            optblank = _getoptblank(blankpa, '')
            return Literal(o) + ZeroOrMore(optblank + _getarg(action, scalarpa, c)) + optblank + Literal(c)
        for o, c in bracketpairs:
            yield (Suppress(Regex("lit|'")) + Suppress(o) + Regex("[^%s]*" % re.escape(c)) + Suppress(c)).setParseAction(Text.pa)
            yield (Suppress(Regex('pass|[.]')) + getbrackets(Text.pa, Text.pa)).setParseAction(Concat.strictpa)
            yield (identifier + getbrackets(Blank.pa, AnyScalar.pa)).setParseAction(Call.pa)
    action = Forward()
    action << Suppress('$').leaveWhitespace() + MatchFirst(clauses()).leaveWhitespace()
    return action

def _getarg(action, scalarpa, boundarychars):
    opttext = Optional(_gettext(Text.pa, boundarychars))
    return (OneOrMore(opttext + action) + opttext | _gettext(scalarpa, boundarychars)).setParseAction(Concat.smartpa)

class Parser:

    def __init__(self, g, singleton = False):
        self.g = g.parseWithTabs()
        self.singleton = singleton

    def __call__(self, text):
        result = self.g.parseString(text, parseAll = True).asList()
        if self.singleton:
            result, = result
        return result

class Factory:

    @classmethod
    def default(cls):
        return cls(AnyScalar.pa, '\r\n')

    def __init__(self, scalarpa, boundarychars):
        self.scalarpa = scalarpa
        self.boundarychars = boundarychars

    def create(self):
        optboundary = _getoptboundary(Boundary.pa, self.boundarychars)
        optblank = _getoptblank(Blank.pa, self.boundarychars)
        return OneOrMore(optblank + _getarg(_getaction(), self.scalarpa, self.boundarychars)) + optblank + optboundary

    def getcommand(self):
        optboundary = _getoptboundary(Boundary.pa, self.boundarychars)
        optblank = _getoptblank(Blank.pa, self.boundarychars)
        return ZeroOrMore(optblank + _getarg(_getaction(), self.scalarpa, self.boundarychars)) + optblank + optboundary

templateparser = Parser(Factory(Text.pa, '').create() | Regex('^$').setParseAction(Text.pa))
commandparser = Parser(Factory.default().getcommand().setParseAction(Entry.pa), True)
