from .grammar import Function, Text, List, Fork
import os, collections

def screenstr(text):
    return '"%s"' % text.replace('\\', '\\\\').replace('\n', '\\n').replace('"', '\\"')

def scstr(text):
    return '"%s"' % text.replace('\\', '\\\\').replace('\n', '\\n').replace('"', '\\"')

def shstr(text):
    return "'%s'" % text.replace("'", r"'\''")

def mapobjs(context, objs, name, expr):
    v = []
    for obj in objs.resolve(context):
        c = Context(context)
        c[name.cat()] = obj
        v.append(expr.resolve(c))
    return List(v)

def join(context, resolvables, separator):
    return Text(separator.resolve(context).cat().join(r.cat() for r in resolvables.resolve(context)))

def get(context, *keys):
    for key in keys:
        context = context[key.cat()]
    return context

class SuperContext:

    resolvables = collections.OrderedDict([
        ['get', Function(get)],
        ['str', Function(lambda context, obj: obj.resolve(context).totext())],
        ['~', Text(os.path.expanduser('~'))],
        ['screenstr', Function(lambda context, text: Text(screenstr(text.resolve(context).cat())))],
        ['scstr', Function(lambda context, text: Text(scstr(text.resolve(context).cat())))],
        ['shstr', Function(lambda context, text: Text(shstr(text.cat())))],
        ['env', Function(lambda context, key: Text(os.environ[key.cat()]))],
        ['LF', Text('\n')],
        ['EOL', Text(os.linesep)],
        ['list', Function(lambda context, *objs: List(list(objs)))],
        ['fork', Function(lambda context: Fork(collections.OrderedDict()))],
        ['map', Function(mapobjs)],
        ['join', Function(join)],
    ])

    def namesimpl(self, names):
        names.update([name, None] for name in self.resolvables.keys())

    def __getitem__(self, name):
        return self.resolvables[name]

supercontext = SuperContext()

class Context:

    def __init__(self, parent = supercontext):
        self.resolvables = collections.OrderedDict()
        self.parent = parent

    def __setitem__(self, name, resolvable):
        self.resolvables[name] = resolvable

    def namesimpl(self, names):
        self.parent.namesimpl(names)
        names.update([name, None] for name in self.resolvables.keys())

    def names(self):
        names = collections.OrderedDict()
        self.namesimpl(names)
        return names.keys()

    def __getitem__(self, name):
        try:
            return self.resolvables[name]
        except KeyError:
            return self.parent[name]

    def resolved(self, name):
        obj = self[name].resolve(self)
        prefix = name + '#'
        for name in self.names():
            if name.startswith(prefix):
                modname = name[len(prefix):]
                if '#' not in modname:
                    obj.modify(modname, self.resolved(name))
        return obj
