#!/usr/bin/env python3

import sys, io
from aridityimpl.grammar import loader, WriteAndFlush
from aridityimpl.context import Context

def main(script):
    stdout = io.StringIO()
    context = Context()
    context['stdout'] = WriteAndFlush(stdout)
    for entry in loader(script):
        entry.execute(context)
    return stdout.getvalue()

if '__main__' == __name__:
    sys.stdout.write(main(sys.stdin.read()))
