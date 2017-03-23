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
        print(phrase.resolve(context), file = sys.stderr)

lookup = {Text(name): d for name, d in allfunctions(Directives)}

def resolvepath(phrase, context):
    path = phrase.resolve(context).cat()
    return path if os.path.isabs(path) else os.path.join(context.resolved('cwd').cat(), path)

def execute(entry, context):
    n = entry.size()
    if not n:
        return
    firstword = entry.word(0)
    if 1 < n and Text('=') == entry.word(1):
        context[firstword.cat()] = entry.phrase(2)
    else:
        try:
            d = lookup.get(firstword)
        except TypeError:
            d = None
        if d is None:
            raise UnsupportedEntryException(entry)
        d(entry.phrase(1), context)
