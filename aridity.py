#!/usr/bin/env python3

import sys, traceback, pyparsing
from aridityimpl.parser import commandparser
from aridityimpl.grammar import Stream
from aridityimpl.context import Context, NoSuchPathException
from aridityimpl.directives import execute, UnsupportedEntryException

class DanglingStackException(Exception): pass

def repl(instream, outstream, interactive = False):
    context = Context()
    context['stdout'] = Stream(outstream)
    stack = []
    for line in instream:
        try:
            command = commandparser(''.join(stack + [line]))
            stack.clear()
        except pyparsing.ParseException:
            stack.append(line)
            continue
        try:
            execute(command, context)
        except (UnsupportedEntryException, NoSuchPathException):
            if not interactive:
                raise
            traceback.print_exc(0)
    if stack:
        raise DanglingStackException(stack)

if '__main__' == __name__:
    repl(sys.stdin, sys.stdout, True)
