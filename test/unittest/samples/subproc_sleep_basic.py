#!/usr/bin/python2.6
import sys
import time
def write():
    time.sleep(4)
    print 't'*64000
    return 0

if __name__ == '__main__':
    sys.exit(write())
