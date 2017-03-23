#!/usr/bin/env python3

import sys, traceback
from aridityimpl.parser import commandparser
from aridityimpl.grammar import Stream
from aridityimpl.context import Context
from aridityimpl.directives import execute, UnsupportedEntryException

def repl(instream, outstream):
    context = Context()
    context['stdout'] = Stream(outstream)
    for line in instream:
        command = commandparser(line) # TODO: Support multi-line commands.
        try:
            execute(command, context)
        except UnsupportedEntryException:
            traceback.print_exc(0)

if '__main__' == __name__:
    repl(sys.stdin, sys.stdout)
