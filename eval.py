#!/usr/bin/env python3

from resolve import resolvetemplate
import sys

def main():
    template, = sys.argv[1:]
    resolvetemplate(template)

if '__main__' == __name__:
    main()
