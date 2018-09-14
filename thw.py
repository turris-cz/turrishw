import turrishw
import json
import pprint

turrishw.__P_ROOT__="./tests_roots/mox+EEC/"
print(json.dumps(turrishw.get_ifaces()))
