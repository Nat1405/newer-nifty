#!/usr/bin/env python

import sys
import nifty

if __name__ == '__main__':

    if '--version' in sys.argv:
        sys.stdout.write("%s\n" % stpipe.__version__)
        sys.exit(0)

    if '-f' or '-r' or '-l' in sys.argv:
        nifty.linearPipeline.start(sys.argv[1:])
