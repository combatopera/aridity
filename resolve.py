#!/usr/bin/env python3

import sys
from aridity.grammar import Text, parser, Concat, Number
from aridity.context import Context

def main():
    path, = sys.argv[1:]
    context = Context()
    builtinsname = '__builtins__'
    scope = {builtinsname: eval(builtinsname)}
    for t in Text, Number:
        scope[t.__name__] = t
    for name, obj in eval(sys.stdin.read(), scope).items():
        context[name] = obj
    with open(path) as f:
        sys.stdout.write(Concat(parser(f.read())).resolve(context).cat())

if '__main__' == __name__:
    main()
