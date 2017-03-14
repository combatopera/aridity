#!/usr/bin/env python3

import sys
from aridity.grammar import Text, parser, Concat, Number
from aridity.context import Context

def resolve(expr):
    context = Context()
    builtinsname = '__builtins__'
    scope = {builtinsname: eval(builtinsname)}
    for t in Text, Number:
        scope[t.__name__] = t
    for name, obj in eval(sys.stdin.read(), scope).items():
        context[name] = obj
    sys.stdout.write(Concat(parser(expr)).resolve(context).cat())

def main():
    path, = sys.argv[1:]
    with open(path) as f:
        resolve(f.read())

if '__main__' == __name__:
    main()
