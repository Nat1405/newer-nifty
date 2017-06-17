#!/Usr/bin/env python

import subprocess

print subprocess.__file__

def test():
    print "Entering test module shell script."
    subprocess.call("./test.sh")
    print "Done testing"

test()
