# Copyright 2018-2022, CZ.NIC z.s.p.o. (http://www.nic.cz/)
#
# TurrisHW is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
# TurrisHW is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with TurrisHW.  If not, see <http://www.gnu.org/licenses/>.
import json
import os
import tarfile

import pytest

import turrishw


@pytest.fixture
def set_root(request, monkeypatch, tmpdir):
    root = request.param
    roots_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "tests_roots")
    result_json = os.path.join(roots_dir, root + '.json')
    root_tar = os.path.join(roots_dir, root + '.tar.gz')
    tdir = str(tmpdir)
    with tarfile.open(root_tar) as tar:
        tar.extractall(path=tdir)

    with monkeypatch.context() as m:
        m.setattr(turrishw.utils, "TURRISHW_FILE_ROOT", tdir)
        yield result_json


@pytest.mark.parametrize(
    "set_root",
    [
        "mox1",
        "mox2",
        "mox3",
        "mox-ac-6.0-vlans",
        "mox-ad-6.0-vlans",
        "omnia",
        "omnia-lan2-flapping",
        "omnia-6.0-vlans",
        "turris",
        "turris-6.0-vlans"
    ],
    indirect=True
)
def test_get_interfaces(set_root):
    with open(set_root) as file:
        thw_ifaces = turrishw.get_ifaces()
        json_data = json.load(file)
        assert json_data == thw_ifaces

        # test order of interfaces
        assert [*json_data.keys()] == [*thw_ifaces.keys()]
