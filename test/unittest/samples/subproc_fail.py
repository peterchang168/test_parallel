#!/usr/bin/python2.6
import sys
def write():
    print  >> sys.stderr,  't'*65000
    return -1

if __name__ == '__main__':
    sys.exit(write())
