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

from pyparsing import Forward, OneOrMore, Optional, MatchFirst, Regex, Suppress, ZeroOrMore, NoMatch, Literal
from decimal import Decimal
from .model import Text, Boolean, Number, Blank, Call, Concat, Boundary, Entry
import re

class AnyScalar:

    numberpattern = re.compile('^-?(?:[0-9]+|[0-9]*[.][0-9]+)$')
    booleans = dict([str(x).lower(), Boolean(x)] for x in [True, False])

    @classmethod
    def pa(cls, s, l, t):
        text, = t
        if text in cls.booleans:
            return cls.booleans[text]
        else:
            m = cls.numberpattern.search(text)
            return Text(text) if m is None else Number((Decimal if '.' in text else int)(text))

class Parser:

    bracketpairs = '()', '[]'
    idregex = r'[^\s$%s]*' % ''.join(re.escape(o) for o, _ in bracketpairs)
    identifier = Regex("%s(?:[$]%s)*" % (idregex, idregex))

    @staticmethod
    def getoptblank(pa, boundarychars):
        return Optional(Regex(r"[^\S%s]+" % re.escape(boundarychars)).leaveWhitespace().setParseAction(pa))

    @staticmethod
    def gettext(pa, boundarychars):
        return Regex(r"[^$\s%s]+" % re.escape(boundarychars)).leaveWhitespace().setParseAction(pa)

    @staticmethod
    def getoptboundary(pa, boundarychars):
        return Optional(Regex("[%s]+" % re.escape(boundarychars)).leaveWhitespace().setParseAction(pa) if boundarychars else NoMatch())

    @classmethod
    def getaction(cls):
        action = Forward()
        def clauses():
            for o, c in cls.bracketpairs:
                yield (Suppress(Regex("lit|'")) + Suppress(o) + Regex("[^%s]*" % re.escape(c)) + Suppress(c)).setParseAction(Text.pa)
                def getbrackets(blankpa, scalarpa):
                    optblank = cls.getoptblank(blankpa, '')
                    return Literal(o) + ZeroOrMore(optblank + cls.getarg(action, scalarpa, c)) + optblank + Literal(c)
                yield (Suppress(Regex('pass|[.]')) + getbrackets(Text.pa, Text.pa)).setParseAction(Concat.strictpa)
                yield (cls.identifier + getbrackets(Blank.pa, AnyScalar.pa)).setParseAction(Call.pa)
        action << Suppress('$').leaveWhitespace() + MatchFirst(clauses()).leaveWhitespace()
        return action

    @classmethod
    def getarg(cls, action, scalarpa, boundarychars):
        opttext = Optional(cls.gettext(Text.pa, boundarychars))
        return (OneOrMore(opttext + action) + opttext | cls.gettext(scalarpa, boundarychars)).setParseAction(Concat.smartpa)

    @classmethod
    def create(cls, scalarpa, boundarychars):
        optboundary = cls.getoptboundary(Boundary.pa, boundarychars)
        optblank = cls.getoptblank(Blank.pa, boundarychars)
        return OneOrMore(optblank + cls.getarg(cls.getaction(), scalarpa, boundarychars)) + optblank + optboundary

    @classmethod
    def getcommand(cls, scalarpa, boundarychars):
        optboundary = cls.getoptboundary(Boundary.pa, boundarychars)
        optblank = cls.getoptblank(Blank.pa, boundarychars)
        return ZeroOrMore(optblank + cls.getarg(cls.getaction(), scalarpa, boundarychars)) + optblank + optboundary

    def __init__(self, g, singleton = False):
        self.g = g.parseWithTabs()
        self.singleton = singleton

    def __call__(self, text):
        result = self.g.parseString(text, parseAll = True).asList()
        if self.singleton:
            result, = result
        return result

expressionparser = Parser(Parser.create(AnyScalar.pa, '\r\n'))
templateparser = Parser(Parser.create(Text.pa, '') | Regex('^$').setParseAction(Text.pa))
loader = Parser(ZeroOrMore(Parser.create(AnyScalar.pa, '\r\n').setParseAction(Entry.pa)))
commandparser = Parser(Parser.getcommand(AnyScalar.pa, '\r\n').setParseAction(Entry.pa), True)
