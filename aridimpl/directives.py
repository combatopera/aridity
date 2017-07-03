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

from .model import Text, Stream, Concat
from .grammar import templateparser
from .util import allfunctions
import os, sys

class Directives:

    def redirect(phrase, context):
        context['stdout',] = Stream(open(resolvepath(phrase, context), 'w'))

    def write(phrase, context):
        context.resolved('stdout').flush(phrase.resolve(context).cat())

    def cat(phrase, context):
        with open(resolvepath(phrase, context)) as f:
            context.resolved('stdout').flush(Concat(templateparser(f.read())).resolve(context).cat())

    def source(phrase, context):
        context.source([], resolvepath(phrase, context))

    def cd(phrase, context):
        context['cwd',] = Text(resolvepath(phrase, context))

    def test(phrase, context):
        sys.stderr.write(phrase.resolve(context))
        sys.stderr.write(os.linesep)

def resolvepath(phrase, context):
    path = phrase.resolve(context).cat()
    return path if os.path.isabs(path) else os.path.join(context.resolved('cwd').cat(), path)

lookup = {Text(name): d for name, d in allfunctions(Directives)}
