#!/usr/bin/env python3

import sys, re
from aridity.grammar import loader, Concat, templateparser
from aridity.context import Context

class Directive:

    def include(context, path):
        with open(path) as f:
            for entry in loader(f.read()):
                context[entry.name] = Concat.unlesssingleton(entry.resolvables)

    def eval(context, template):
        context.resolved('stdout')(Concat(templateparser(template)).resolve(context).cat())

    def evalfile(context, path):
        with open(path) as f:
            return Directive.eval(context, f.read())

def main():
    context = Context()
    directive = re.compile('^#(\S+)\s+(.+)')
    for line in sys.stdin:
        m = directive.search(line)
        if m is None:
            for entry in loader(line):
                context[entry.name] = Concat.unlesssingleton(entry.resolvables)
        else:
            name, arg = m.groups()
            getattr(Directive, name)(context, arg)

if '__main__' == __name__:
    main()
