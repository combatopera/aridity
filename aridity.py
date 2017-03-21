#!/usr/bin/env python3

import sys
from aridityimpl.grammar import loader
from aridityimpl.context import Context

def main(script):
    context = Context()
    for entry in loader(script):
        entry.execute(context)

if '__main__' == __name__:
    main(sys.stdin.read())
