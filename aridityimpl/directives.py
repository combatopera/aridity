from .grammar import Text, Stream, Concat, templateparser, loader
import os

class UnsupportedEntryException(Exception): pass

def execute(entry, context):
    def resolvepath(i):
        path = entry.phrase(i).resolve(context).cat()
        return path if os.path.isabs(path) else os.path.join(context.resolved('cwd').cat(), path)
    if Text('=') == entry.word(1):
        context[entry.word(0).cat()] = entry.phrase(2)
    elif Text('redirect') == entry.word(0):
        context['stdout'] = Stream(open(resolvepath(1), 'w'))
    elif Text('echo') == entry.word(0):
        template = entry.phrase(1).resolve(context).cat()
        context.resolved('stdout').writeflush(Concat(templateparser(template)).resolve(context).cat())
    elif Text('cat') == entry.word(0):
        with open(resolvepath(1)) as f:
            context.resolved('stdout').writeflush(Concat(templateparser(f.read())).resolve(context).cat())
    elif Text('source') == entry.word(0):
        with open(resolvepath(1)) as f:
            for entry in loader(f.read()):
                execute(entry, context)
    elif Text('cd') == entry.word(0):
        context['cwd'] = Text(resolvepath(1))
    else:
        raise UnsupportedEntryException(entry)
