from .grammar import Text, List, Fork
import inspect

class Functions:

    def screenstr(context, text):
        text = text.resolve(context).cat()
        return Text('"%s"' % text.replace('\\', '\\\\').replace('\n', '\\n').replace('"', '\\"'))

    def scstr(context, text):
        text = text.resolve(context).cat()
        return Text('"%s"' % text.replace('\\', '\\\\').replace('\n', '\\n').replace('"', '\\"'))

    def pystr(context, text):
        return Text(repr(text.resolve(context).cat()))

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

    def get(context, *keys):
        for key in keys:
            context = context.resolved(key.cat())
        return context

    def str(context, resolvable):
        return resolvable.resolve(context).totext()

    def list(context, *objs):
        return List(list(objs))

    def fork(context):
        return Fork(context)

def getfunctions():
    return inspect.getmembers(Functions, predicate = inspect.isfunction)
