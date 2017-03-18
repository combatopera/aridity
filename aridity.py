#!/usr/bin/env python3

import sys
from aridity.grammar import loader
from aridity.context import Context

def main():
    context = Context()
    for entry in loader(sys.stdin.read()):
        entry.execute(context)

if '__main__' == __name__:
    main()
