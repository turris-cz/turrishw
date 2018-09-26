#!/usr/bin/env python3

import turrishw
import json
import sys

if len(sys.argv) > 1:
    turrishw.__P_ROOT__=sys.argv[1]
print(json.dumps(turrishw.get_ifaces(), indent=2, sort_keys=True))
