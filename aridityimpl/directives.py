from .grammar import Text, Stream, Concat
from .parser import templateparser, loader
from .util import allfunctions
import os

class UnsupportedEntryException(Exception): pass

class Directives:

    def redirect(entry, context):
        context['stdout'] = Stream(open(resolvepath(entry, context, 1), 'w'))

    def echo(entry, context):
        context.resolved('stdout').writeflush(entry.phrase(1).resolve(context).cat())

    def cat(entry, context):
        with open(resolvepath(entry, context, 1)) as f:
            context.resolved('stdout').writeflush(Concat(templateparser(f.read())).resolve(context).cat())

    def source(entry, context):
        with open(resolvepath(entry, context, 1)) as f:
            for entry in loader(f.read()):
                execute(entry, context)

    def cd(entry, context):
        context['cwd'] = Text(resolvepath(entry, context, 1))

lookup = {Text(name): d for name, d in allfunctions(Directives)}

def resolvepath(entry, context, i):
    path = entry.phrase(i).resolve(context).cat()
    return path if os.path.isabs(path) else os.path.join(context.resolved('cwd').cat(), path)

def execute(entry, context):
    n = entry.size()
    if not n:
        raise UnsupportedEntryException(entry)
    firstword = entry.word(0)
    if 1 < n and Text('=') == entry.word(1):
        context[firstword.cat()] = entry.phrase(2)
    else:
        d = lookup.get(firstword)
        if d is None:
            raise UnsupportedEntryException(entry)
        d(entry, context)
