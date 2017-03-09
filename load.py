#!/usr/bin/env python3

import sys
from aridity.grammar import loader, Concat
from aridity.context import Context

def main():
    path, = sys.argv[1:]
    context = Context()
    with open(path) as f:
        for entry in loader(f.read()):
            context[entry.name] = Concat.unlesssingleton(entry.resolvables)
    print({name: context[name].resolve(context) for name in context.names()})

if '__main__' == __name__:
    main()
