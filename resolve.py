#!/usr/bin/env python3

import sys, collections
from aridity.grammar import Text, templateparser, Concat, Number, List
from aridity.context import Context

def resolvetemplate(template):
    context = Context()
    builtinsname = '__builtins__'
    scope = {builtinsname: eval(builtinsname)}
    for t in Text, Number, List, collections.OrderedDict:
        scope[t.__name__] = t
    for name, obj in eval(sys.stdin.read(), scope).items():
        context[name] = obj
    sys.stdout.write(Concat(templateparser(template)).resolve(context).cat())

def main():
    path, = sys.argv[1:]
    with open(path) as f:
        resolvetemplate(f.read())

if '__main__' == __name__:
    main()
