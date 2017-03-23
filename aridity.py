#!/usr/bin/env python3

import sys
from aridityimpl.parser import commandparser
from aridityimpl.grammar import Stream
from aridityimpl.context import Context
from aridityimpl.directives import execute

def repl(instream, outstream):
    context = Context()
    context['stdout'] = Stream(outstream)
    for line in instream:
        command = commandparser(line) # TODO: Support multi-line commands.
        execute(command, context)

if '__main__' == __name__:
    repl(sys.stdin, sys.stdout)
