#!/usr/bin/env python3

import sys, re
from aridity.grammar import loader, Concat, templateparser, AnyScalar
from aridity.context import Context

class Directive:

    def include(context, path):
        with open(path) as f:
            for entry in loader(f.read()):
                entry.execute(context)

    def scalar(context, name, scalar):
        context[name] = AnyScalar.pa(None, None, [scalar])

def main():
    context = Context()
    directive = re.compile('^#([^\s(]+)(?:[(]([^)]+)[)])?\s+(.+)')
    for line in sys.stdin:
        m = directive.search(line)
        if m is None:
            for entry in loader(line):
                entry.execute(context)
        else:
            args = [g for g in m.groups()[1:] if g is not None]
            getattr(Directive, m.group(1))(context, *args) # TODO: Strip trailing whitespace from arg.

if '__main__' == __name__:
    main()
