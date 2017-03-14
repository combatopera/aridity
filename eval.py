#!/usr/bin/env python3

from resolve import resolve
import sys

def main():
    expr, = sys.argv[1:]
    resolve(expr)

if '__main__' == __name__:
    main()
