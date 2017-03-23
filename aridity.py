#!/usr/bin/env python3

import sys
from aridityimpl.parser import loader
from aridityimpl.grammar import Stream
from aridityimpl.context import Context
from aridityimpl.directives import execute

def repl(instream, outstream):
    context = Context()
    context['stdout'] = Stream(outstream)
    for entry in loader(instream.read()): # TODO: Load line-by-line.
        execute(entry, context)

if '__main__' == __name__:
    repl(sys.stdin, sys.stdout)
