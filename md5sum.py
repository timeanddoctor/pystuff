import sys
import os
import hashlib

def md5sum(argv):
  if len(argv) < 2:
    raise Exception('Usage md5sum filename')
  retval = None
  with open(argv[1], 'rb') as fh:
    s = fh.read()
    retval = hashlib.md5(s).hexdigest()
  return retval
if __name__ == "__main__":
  s = md5sum(sys.argv)
  sys.stdout.write(s)
