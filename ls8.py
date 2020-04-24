#!/usr/bin/env python3

"""Main."""

import sys
from cpu import *

if len(sys.argv) == 0:
    sys.exit('Must include a program filename')

cpu = CPU()

try:
    cpu.load(sys.argv[1])
except:
    sys.exit('Was unable to load program')

cpu.run()