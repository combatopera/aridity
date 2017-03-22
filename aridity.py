#!/usr/bin/env python3

import sys
from aridityimpl.grammar import loader, Stream
from aridityimpl.context import Context

def repl(instream, outstream):
    context = Context()
    context['stdout'] = Stream(outstream)
    for entry in loader(instream.read()): # TODO: Load line-by-line.
        entry.execute(context)

if '__main__' == __name__:
    repl(sys.stdin, sys.stdout)
