import turrishw
import json
import pprint
import sys

turrishw.__P_ROOT__=sys.argv[1]
print(json.dumps(turrishw.get_ifaces()))
