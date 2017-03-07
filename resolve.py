#!/usr/bin/env python3

import sys, getopt
from aridity.grammar import Text, parser, Concat
from aridity.context import Context

def main():
    pairs, args = getopt.gnu_getopt(sys.argv[1:], 'D:')
    path, = args
    context = Context()
    for option, value in pairs:
        if '-D' == option:
            eq = value.index('=')
            context[value[:eq]] = Text(value[eq + 1:])
    with open(path) as f:
        sys.stdout.write(Concat(parser(f.read())).resolve(context).cat())

if '__main__' == __name__:
    main()
