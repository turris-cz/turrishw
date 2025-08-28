# Copyright (c) 2025, CZ.NIC, z.s.p.o. (http://www.nic.cz/)
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
import logging
import re
import typing
from pathlib import Path

from . import utils
from .interface import Interface

logger = logging.getLogger(__name__)


def get_interfaces() -> typing.List[Interface]:
    ifaces: typing.List[Interface] = []
    virtual_ifaces: typing.List[typing.Dict[str, str]] = []
    vlan_ifaces: typing.List[str] = utils.get_vlan_interfaces()

    # First pass - process the detected physical interfaces
    for iface_name in utils.get_ifaces():
        iface_path: Path = utils.inject_file_root("sys/class/net", iface_name)
        iface_abspath: Path = iface_path.resolve()
        iface_path_str = str(iface_abspath)
        iface_type = utils.find_iface_type(iface_name)
        path = iface_path / "address"
        if not path.exists():
            logger.warning("File '%s' is missing. Skipping interface '%s'", path, iface_name)
            continue
        macaddr = utils.get_first_line(path).strip()

        slot_map = {"1": "ETH0", "2": "ETH1", "3": "ETH2", "4": "ETH3", "5": "SFP0", "6": "SFP1"}

        if ".dp" in iface_path_str:
            if m := re.search(r"/[a-f0-9]+\.dp(\d+)/", iface_path_str):
                slot_idx = m.group(1)
                slot = slot_map.get(slot_idx)
                ifaces.append(
                    utils.make_iface(
                        iface_name,
                        "eth",
                        "eth",
                        slot or slot_idx,
                        macaddr,
                        slot_path=iface_path_str,
                        parent_device_abs_path=iface_abspath,
                    )
                )
            else:
                logger.warning("unknown DP slot module")

        elif "pci0002:00" in iface_path_str:
            # PCI
            m = re.search(r"/0002:00:0([0-3])\.0/", iface_path_str)
            if m:
                slot = m.group(1)
                ifaces.append(utils.make_iface(iface_name, "wifi", "pci", slot, macaddr, slot_path=iface_path_str))
            else:
                logger.warning("unknown PCI slot module")
        elif ".wifi" in iface_path_str:
            # WIFI slot ?
            ifaces.append(
                utils.make_iface(
                    iface_name,
                    iface_type,
                    "wifi",
                    "0",
                    macaddr,
                    slot_path=iface_path_str,
                    parent_device_abs_path=iface_abspath,
                )
            )
        elif "virtual" in iface_path_str:
            # virtual ifaces (loopback, bridges, ...) - we don't care about these
            #
            # `utils.get_ifaces` can return interfaces in random order, so interfaces with VLAN assigned
            # will be processed in second pass to ensure that its parent interface exists and is already processed.
            if iface_name in vlan_ifaces:
                virtual_ifaces.append({"name": iface_name, "macaddr": macaddr})
        else:
            logger.warning("unknown interface type: %s", iface_name)

    # Second pass - process virtual interfaces with VLAN assigned.
    vlan_ifaces = utils.make_vlan_interfaces(ifaces, virtual_ifaces)

    return ifaces + vlan_ifaces
