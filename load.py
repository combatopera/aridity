#!/usr/bin/env python3

import sys, getopt
from aridity.grammar import loader, Concat, Text
from aridity.context import Context

def main():
    pairs, args = getopt.gnu_getopt(sys.argv[1:], 'D:', [])
    path, = args
    context = Context()
    for option, value in pairs: # XXX: Maybe these should override file entries?
        if '-D' == option:
            k, v = value.split('=', 1)
            context[k] = Text(v) # XXX: Parse the value as a scalar?
    with open(path) as f:
        for entry in loader(f.read()):
            context[entry.name] = Concat.unlesssingleton(entry.resolvables)
    config = {}
    for name in context.names():
        obj = context[name].resolve(context)
        if obj.serializable:
            config[name] = obj
    print(config)

if '__main__' == __name__:
    main()
