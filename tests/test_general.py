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
import turrishw as thw


# TODO mox-4.14
@pytest.fixture(params=[
    "mox+C",
    "mox+EEC",
    "omnia-4.0",
    ])
def set_root(request):
    root = request.param
    testdir = os.path.join(os.getcwd(), 'tests_roots')
    orig_root = thw.__P_ROOT__
    newroot = os.path.join(testdir, root) + "/"
    print(newroot)
    thw.__P_ROOT__ = newroot

    yield os.path.join(testdir, root + '.json')

    thw.__P_ROOT__ = orig_root


def test_all(set_root):
    with open(set_root) as file:
        assert json.load(file) == thw.get_ifaces()
