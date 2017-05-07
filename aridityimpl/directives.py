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

from .grammar import Text, Stream, Concat
from .parser import templateparser, loader
from .util import allfunctions
import os, sys

class UnsupportedEntryException(Exception): pass

class Directives:

    def redirect(phrase, context):
        context['stdout'] = Stream(open(resolvepath(phrase, context), 'w'))

    def write(phrase, context):
        context.resolved('stdout').flush(phrase.resolve(context).cat())

    def cat(phrase, context):
        with open(resolvepath(phrase, context)) as f:
            context.resolved('stdout').flush(Concat(templateparser(f.read())).resolve(context).cat())

    def source(phrase, context):
        with open(resolvepath(phrase, context)) as f:
            for entry in loader(f.read()):
                execute(entry, context)

    def cd(phrase, context):
        context['cwd'] = Text(resolvepath(phrase, context))

    def test(phrase, context):
        sys.stderr.write(phrase.resolve(context))
        sys.stderr.write(os.linesep)

lookup = {Text(name): d for name, d in allfunctions(Directives)}

def resolvepath(phrase, context):
    path = phrase.resolve(context).cat()
    return path if os.path.isabs(path) else os.path.join(context.resolved('cwd').cat(), path)

def execute(entry, context):
    n = entry.size()
    if not n:
        return
    for i in range(n):
        if Text('=') == entry.word(i):
            context[tuple(entry.word(k).totext().cat() for k in range(i))] = entry.phrase(i + 1)
            return
    word = entry.word(0)
    try:
        d = lookup.get(word)
    except TypeError:
        d = None
    if d is None:
        raise UnsupportedEntryException(entry)
    d(entry.phrase(1), context)
