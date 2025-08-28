# Copyright (c) 2021-2025, CZ.NIC, z.s.p.o. (https://www.nic.cz/)
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

"""Implementation of Turris 1.x router HW"""

import logging
import re
import typing
from pathlib import Path

from . import utils
from .interface import Interface

logger = logging.getLogger(__name__)


def get_interfaces() -> typing.List[Interface]:
    def detect_pcie_wifi(iface, path, regex):
        """Try to detect wifi interface based on regex"""
        m = re.search(regex, path)
        if m:
            ifaces.append(utils.make_iface(iface, "wifi", "pci", "0", macaddr, slot_path=path))
        else:
            logger.warning("unknown PCI slot module")

    ifaces: typing.List[Interface] = []
    virtual_ifaces: typing.List[typing.Dict[str, str]] = []
    vlan_ifaces: typing.List[str] = utils.get_vlan_interfaces()

    # First pass - process the detected physical interfaces
    for iface_name in utils.get_ifaces():
        iface_path: Path = utils.inject_file_root("sys/class/net", iface_name)
        iface_abspath: Path = iface_path.resolve()
        iface_path_str = str(iface_abspath)
        iface_type = utils.find_iface_type(iface_name)
        macaddr = utils.get_first_line(iface_path / "address").strip()

        if "mdio@ffe24520" in iface_path_str:  # Switch exported ports
            port_label = utils.get_iface_label(iface_path)
            ifaces.append(utils.make_iface(iface_name, "eth", "eth", port_label, macaddr))
        elif "ffe26000.ethernet" in iface_path_str:  # WAN port
            ifaces.append(utils.make_iface(iface_name, "eth", "eth", "WAN", macaddr))
        elif "pci0001:02" in iface_path_str:  # pcie wifi
            detect_pcie_wifi(iface_name, iface_path_str, r"/0001:02:00\.0/")
        elif "pci0002:04" in iface_path_str:  # pcie wifi
            detect_pcie_wifi(iface_name, iface_path_str, r"/0002:04:00\.0/")
        elif "fsl-ehci.0" in iface_path_str:
            # rear USB2.0 ports.
            if "1-1.1" in iface_path_str:
                ifaces.append(
                    utils.make_iface(
                        iface_name,
                        iface_type,
                        "usb",
                        "USB 1",
                        macaddr,
                        slot_path=iface_path_str,
                        parent_device_abs_path=iface_abspath,
                    )
                )
            elif "1-1.2" in iface_path_str:
                ifaces.append(
                    utils.make_iface(
                        iface_name,
                        iface_type,
                        "usb",
                        "USB 2",
                        macaddr,
                        slot_path=iface_path_str,
                        parent_device_abs_path=iface_abspath,
                    )
                )
        # Turris 1.1 USB ports
        elif "pci0002:00" in iface_path_str:
            if "2-2" in iface_path_str:
                ifaces.append(
                    utils.make_iface(
                        iface_name,
                        iface_type,
                        "pci",
                        "2",
                        macaddr,
                        slot_path=iface_path_str,
                        parent_device_abs_path=iface_abspath,
                    )
                )
            elif "3-1" in iface_path_str:
                # front USB 3.0 port
                ifaces.append(
                    utils.make_iface(
                        iface_name,
                        iface_type,
                        "usb",
                        "USB Front",
                        macaddr,
                        slot_path=iface_path_str,
                        parent_device_abs_path=iface_abspath,
                    )
                )
        elif "ffe24000.ethernet" in iface_path_str or "ffe25000.ethernet" in iface_path_str:
            # ethernet interfaces connected to switch - ignore them
            pass
        elif "virtual" in iface_path_str:
            # virtual ifaces (loopback, bridges, ...) - we don't care about these
            if iface_name in vlan_ifaces:
                virtual_ifaces.append({"name": iface_name, "macaddr": macaddr})
        else:
            logger.warning("unknown interface type: %s", iface_name)

    # Second pass - process virtual interfaces with VLAN assigned.
    vlan_ifaces = utils.make_vlan_interfaces(ifaces, virtual_ifaces)

    return ifaces + vlan_ifaces
