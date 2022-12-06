# Copyright (c) 2018-2022, CZ.NIC, z.s.p.o. (http://www.nic.cz/)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the CZ.NIC nor the
#      names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL CZ.NIC BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
import os
import re
import typing
from pathlib import Path

# ENV variable is needed for blackbox testing with foris-controller
TURRISHW_FILE_ROOT = os.getenv("TURRISHW_ROOT", "/")


def inject_file_root(*paths) -> Path:
    """Inject TURRISHW_FILE_ROOT prefix to file path(s)"""
    return Path(TURRISHW_FILE_ROOT, *paths)


def get_first_line(filename: Path) -> str:
    with open(filename, 'r') as f:
        return f.readline()


def get_iface_state(iface):
    operstate = get_first_line(inject_file_root('sys/class/net/{}/operstate'.format(iface)))
    if operstate.strip() == "up":
        return "up"
    else:
        return "down"


def get_iface_speed(iface):
    try:
        speed = get_first_line(inject_file_root('sys/class/net/{}/speed'.format(iface)))
        speed = int(speed)
        # sometimes we can get -1 from sysfs, meaning speed is not negotiated yet
        return max(speed, 0)
    except (OSError, ValueError):
        # can't read the file or can't convert value to int (file is empty)
        return 0


def get_iface_label(iface_path: Path) -> str:
    """Get inteface label, e.g. lan1, by given interface path

    Search /sys subsystem for `<iface_path>/of_node/label`.
    """
    return get_first_line(iface_path / "of_node/label").rstrip("\x00").upper()


def find_iface_type(iface):
    path = inject_file_root('sys/class/net', iface)
    if path.joinpath("phy80211").is_dir():
        return "wifi"
    if path.joinpath("qmi").is_dir():
        return "wwan"
    # TODO: support other protocols of LTE modems
    return "eth"


def get_ifaces():
    path = inject_file_root('sys/class/net')
    for f in path.iterdir():
        # we only need links, not files
        if f.is_symlink():
            yield f.name


def get_vlan_interfaces() -> typing.List[str]:
    """Get name of all interfaces, which has VLAN id set.

    Take a look into `/proc/net/vlan/` provided by kernel.
    Based on the kernel documentation, there should be only only `config` and interface-like files
    (i.e. <interface_name>.<vlan_number>) in `/proc/net/vlan`.
    Ignore the `config` and fetch all interface-like looking files.

    For instance:

    ```
    # ls /proc/net/vlan/
    config    eth2.128
    ```

    Please note that alternative approach could be to parse `/proc/net/vlan/config` as single source of truth,
    to get all interfaces with VLAN id.
    But that would mean parsing text file, which formatting could be less stable between kernel versions
    than vlan interfaces representation on `/proc` subsystem.

    Return list of interfaces names.
    """

    path = inject_file_root("proc/net/vlan")
    if not path.is_dir():
        return []

    return [iface.name for iface in path.glob("*.*")]


def process_vlan_interfaces(
    first_pass_ifaces: typing.Dict[str, dict],
    second_pass_ifaces: typing.List[typing.Dict[str, str]]
) -> None:
    """Process virtual interfaces that have VLAN ID assigned.
    Reuse its parent interface properties and fill in the differences.

    For instance: eth2.100 should always be of the same type (wired ethernet) as its parent (eth2),
    but it could have a different MAC address.

    first_pass_ifaces: Physical interfaces detected in first pass processing.
    second_pass_ifaces: Virtual interfaces that need to be matched to their parent interfaces.
    """
    for virt_iface in second_pass_ifaces:
        iface_name = virt_iface["name"]
        macaddr = virt_iface["macaddr"]
        base_iface, vlan_id = iface_name.rsplit(".", maxsplit=1)
        vlan_id_no = int(vlan_id)

        # Parent interface (e.g. eth2) must be available and processed if we intend to reference it.
        # If we can't find the parent, ignore this interface.
        if base_iface in first_pass_ifaces:
            parent = first_pass_ifaces[base_iface]
            first_pass_ifaces[iface_name] = iface_info(
                iface_name, parent["type"], parent["bus"], parent["slot"], macaddr, vlan_id_no, parent["module_id"]
            )


def get_TOS_major_version():
    version = get_first_line(inject_file_root('etc/turris-version'))
    parts = version.split('.')
    return int(parts[0])


def iface_info(
    iface_name: str,
    if_type: str,
    bus: str,
    port_label: str,
    macaddr: str,
    vlan_id: typing.Optional[int] = None,
    module_id: int = 0,  # `module_id` is useful only for Mox, fallback to 0 for other HW
):
    state = get_iface_state(iface_name)
    iface_speed = get_iface_speed(iface_name) if state == "up" else 0
    res = {
        "type": if_type, "bus": bus, "state": state,
        "slot": port_label, "module_id": module_id, 'macaddr': macaddr,
        "link_speed": iface_speed
    }

    if vlan_id is not None:
        res["vlan_id"] = vlan_id

    return res


def sort_by_natural_order(interfaces: typing.Dict[str, dict]) -> typing.Dict[str, dict]:
    """Sort dictionary by keys in natural order."""
    return dict(
        sorted(
            interfaces.items(),
            key=lambda l: [int(s) if s.isdigit() else s.lower() for s in re.split(r"(\d+)", l[0])]
        )
    )
