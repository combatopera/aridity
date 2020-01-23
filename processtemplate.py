#!/usr/bin/env python3

import aridity, os, sys

def main():
    templatepath, = sys.argv[1:]
    with aridity.Repl(aridity.Context()) as repl:
        for line in sys.stdin:
            repl(line)
        repl.printf("< %s", os.path.abspath(templatepath))

if '__main__' == __name__:
    main()
