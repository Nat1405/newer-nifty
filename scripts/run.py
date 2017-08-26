#!/usr/bin/env python

import sys
import nifty.linearPipeline as linearPipeline

if __name__ == '__main__':

    if '--version' in sys.argv:
        sys.stdout.write("%s\n" % stpipe.__version__)
        sys.exit(0)

    if '-f' in sys.argv:
        linearPipeline.start(sys.argv[1:])
