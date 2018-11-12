#!/usr/bin/env python3

import turrishw
import json
import sys
import re

if len(sys.argv) > 1:
    turrishw.__P_ROOT__=sys.argv[1]
ifaces=json.dumps(turrishw.get_ifaces(), indent=2, sort_keys=True, separators=(', ', ': '))

# I want just one line per interface (merge lines with indent level 4)
ifaces = re.sub(r"    (.*)\n", r"\1", ifaces)
ifaces = re.sub(r"(.+){\n", r"\1{", ifaces)
ifaces = re.sub(r"  }", "}", ifaces)
print(ifaces)
