from .grammar import Text, List, Fork
from .util import allfunctions, NoSuchPathException

class Functions:

    def screenstr(context, resolvable):
        text = resolvable.resolve(context).cat()
        return Text('"%s"' % text.replace('\\', '\\\\').replace('\n', '\\n').replace('"', '\\"'))

    def scstr(context, resolvable):
        text = resolvable.resolve(context).cat()
        return Text('"%s"' % text.replace('\\', '\\\\').replace('\n', '\\n').replace('"', '\\"'))

    def pystr(context, resolvable):
        return Text(repr(resolvable.resolve(context).cat()))

    def map(context, objs, *args):
        if 1 == len(args):
            expr, = args
            return List([expr.resolve(c) for c in objs.resolve(context)])
        else:
            name, expr = args
            name = name.resolve(context).cat()
            def g():
                for obj in objs.resolve(context):
                    c = context.createchild()
                    c[name] = obj
                    yield expr.resolve(c)
            return List(list(g()))

    def join(context, resolvables, *args):
        if args:
            r, = args
            separator = r.resolve(context).cat()
        else:
            separator = ''
        return Text(separator.join(r.cat() for r in resolvables.resolve(context)))

    def get(context, *resolvables):
        for r in resolvables:
            context = context.resolved(r.resolve(context).cat())
        return context

    def str(context, resolvable):
        return resolvable.resolve(context).totext()

    def list(context, *objs):
        return List(list(objs))

    def fork(context):
        return Fork(context)

    def try_(context, *resolvables):
        for r in resolvables[:-1]:
            try:
                return r.resolve(context)
            except NoSuchPathException:
                pass
        return resolvables[-1].resolve(context)

def getfunctions():
    return allfunctions(Functions)
