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
import tarfile


import turrishw as thw

# TODO mox-4.14
@pytest.fixture(params=[
    "omnia",
    "mox1",
    "mox2",
    "mox3",
    ])
def set_root(request, monkeypatch, tmpdir):
    root = request.param
    roots_dir = os.path.join(os.getcwd(), 'tests_roots')
    result_json = os.path.join(roots_dir, root + '.json')
    root_tar = os.path.join(roots_dir, root + '.tar.gz')
    tmpdir = str(tmpdir)
    with tarfile.open(root_tar) as tar:
        tar.extractall(path=tmpdir)
    with monkeypatch.context() as m:
        m.setattr("turrishw.__P_ROOT__", tmpdir)
        m.setattr("turrishw.mox.__P_ROOT__", tmpdir)
        m.setattr("turrishw.omnia.__P_ROOT__", tmpdir)
        yield result_json


def test_all(set_root):
    with open(set_root) as file:
        assert json.load(file) == thw.get_ifaces()
