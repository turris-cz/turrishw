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

# ENV variable is needed for blackbox testing with foris-controller
TURRISHW_FILE_ROOT = os.getenv("TURRISHW_ROOT", "/")


def inject_file_root(*paths):
    """Inject TURRISHW_FILE_ROOT prefix to file path(s)"""
    return os.path.join(TURRISHW_FILE_ROOT, *paths)


def get_first_line(filename):
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


def get_iface_label(iface_path: str) -> str:
    """Get inteface label, e.g. lan1, by given interface path

    Search /sys subsystem for `<iface_path>/of_node/label`.
    """
    return get_first_line(os.path.join(iface_path, "of_node/label")).rstrip("\x00").upper()


def find_iface_type(iface):
    path = inject_file_root('sys/class/net', iface)
    if os.path.isdir(os.path.join(path, "phy80211")):
        return "wifi"
    if os.path.isdir(os.path.join(path, "qmi")):
        return "wwan"
    # TODO: support other protocols of LTE modems
    return "eth"


def get_ifaces():
    path = inject_file_root('sys/class/net')
    for f in os.listdir(path):
        # we only need links, not files
        if os.path.islink(os.path.join(path, f)):
            yield f


def get_TOS_major_version():
    version = get_first_line(inject_file_root('etc/turris-version'))
    parts = version.split('.')
    return int(parts[0])


def iface_info(iface, if_type, bus, module_id, slot, macaddr):
    state = get_iface_state(iface)
    return {"name": iface, "type": if_type, "bus": bus, "state": state,
            "slot": slot, "module_id": module_id, 'macaddr': macaddr,
            "link_speed": get_iface_speed(iface) if state == "up" else 0}


def ifaces_array2dict(ifaces_array: typing.List[dict]) -> typing.Dict[str, dict]:
    """Convert array of interfaces dict objects to dictionary with `name` as key and the rest as value.

    Reading interfaces from /sys might return them in different order based on tool used.
    See difference between order of items for `os.listdir()` vs `ls` in shell.

    It will be more useful for consumer of `turrishw` to get interfaces sorted in resulting dictionary
    to avoid dealing with the possibly random order of interfaces.

    Thus return them sorted.
    """
    d = {}
    ifaces = sort_by_natural_order(ifaces_array)
    for iface in ifaces:
        name = iface.pop("name")
        d[name] = iface
    return d


def sort_by_natural_order(items: typing.List[dict]) -> typing.List[dict]:
    """Sort interfaces in list by their `name` by natural order."""
    return sorted(
        items,
        key=lambda l: [int(s) if s.isdigit() else s.lower() for s in re.split(r"(\d+)", l["name"])]
    )
