# Copyright 2018, CZ.NIC z.s.p.o. (http://www.nic.cz/)
#
# This file is part of the PyUCI.
#
# PyUCI is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
# PyUCI is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PyUCI.  If not, see <http://www.gnu.org/licenses/>.
import pytest
import os
import json
from types import ModuleType
import turrishw as thw


# TODO mox-4.14
@pytest.fixture(params=[
    {"board": "turris", "version": "4.4"},
    {"board": "turris", "version": "4.14"},
    {"board": "omnia", "version": "4.4"},
    ])
def set_root(request):
    root = request.param['board'] + '-' + request.param['version']
    testdir = os.path.join(os.getcwd(), 'tests_roots')

    assert thw.board.__P_MODEL__ == "/sys/firmware/devicetree/base/model"
    orig_vals = dict()

    # First redirect all paths to our root and setup PATH
    # This works only if every module has uniq name
    def _update(mod):
        if mod.__name__ in orig_vals:
            return  # Skip processed module
        orig_vals[mod.__name__] = dict()
        for name in dir(mod):
            if isinstance(getattr(mod, name), ModuleType):
                _update(getattr(mod, name))
            elif name.startswith('__P_'):
                cur = getattr(mod, name)
                orig_vals[mod.__name__][name] = cur
                setattr(mod, name,
                        os.path.join(testdir, root, cur.lstrip('/')))

    _update(thw)
    processed_mod = set()
    orig_path = os.environ['PATH']
    os.environ['PATH'] = \
        os.path.join(testdir, root, "bin") + ":" + os.environ['PATH']

    yield os.path.join(testdir, request.param['board'] + '.json')

    # Restore all modified paths and PATH environment variable
    def _restore(mod):
        for name in dir(mod):
            if isinstance(getattr(mod, name), ModuleType):
                if name not in processed_mod:
                    processed_mod.add(name)
                    _restore(getattr(mod, name))
            elif name.startswith('__P_'):
                setattr(mod, name, orig_vals[mod.__name__][name])
    _restore(thw)
    os.environ['PATH'] = orig_path


def test_all(set_root):
    with open(set_root) as file:
        assert json.load(file) == thw.get_all()
