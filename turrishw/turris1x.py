# Copyright (c) 2021-2022, CZ.NIC, z.s.p.o. (https://www.nic.cz/)
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
import os
import re
import typing

from . import utils

logger = logging.getLogger(__name__)


def get_interfaces() -> typing.Dict[str, dict]:
    def append_iface(name: str, if_type: str, bus: str, port_label: str, macaddr: str):
        ifaces[name] = utils.iface_info(name, if_type, bus, 0, port_label, macaddr)

    def detect_pcie_wifi(iface, path, regex):
        """Try to detect wifi interface based on regex"""
        m = re.search(regex, path)
        if m:
            append_iface(iface, "wifi", "pci", "0", macaddr)
        else:
            logger.warning("unknown PCI slot module")

    ifaces = {}
    for iface in utils.get_ifaces():
        path = os.readlink(utils.inject_file_root("sys/class/net", iface))
        iface_path = utils.inject_file_root("sys/class/net", iface)
        macaddr = utils.get_first_line(os.path.join(iface_path, "address")).strip()
        if "mdio@ffe24520" in path:  # Switch exported ports
            port_label = utils.get_iface_label(iface_path)
            append_iface(iface, "eth", "eth", port_label, macaddr)
        elif "ffe26000.ethernet" in path:  # WAN port
            append_iface(iface, "eth", "eth", "WAN", macaddr)
        elif "pci0001:02" in path:  # pcie wifi
            detect_pcie_wifi(iface, path, r"/0001:02:00\.0/")
        elif "pci0002:04" in path:  # pcie wifi
            detect_pcie_wifi(iface, path, r"/0002:04:00\.0/")
        elif "fsl-ehci.0" in path:
            # back two USB2.0 ports.
            append_iface(iface, utils.find_iface_type(iface), "usb", "front", macaddr)
            append_iface(iface, utils.find_iface_type(iface), "usb", "rear", macaddr)
        elif "f1058000.usb" in path:
            append_iface(iface, utils.find_iface_type(iface), "pci", "3", macaddr)
        elif "ffe24000.ethernet" in path or "ffe25000.ethernet" in path:
            # ethernet interfaces connected to switch - ignore them
            pass
        elif "virtual" in path:
            # virtual ifaces (loopback, bridges, ...) - we don't care about these
            pass
        else:
            logger.warning("unknown interface type: %s", iface)
    return ifaces
