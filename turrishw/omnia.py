# Copyright (c) 2018-2023, CZ.NIC, z.s.p.o. (http://www.nic.cz/)
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
import os
import re
import typing

from . import utils

logger = logging.getLogger(__name__)


def get_interfaces() -> typing.Dict[str, dict]:
    ifaces: typing.Dict[str, dict] = {}
    second_pass_ifaces: typing.List[typing.Dict[str, str]] = []
    vlan_ifaces: typing.List[str] = utils.get_vlan_interfaces()

    # First pass - process the detected physical interfaces
    for iface_name in utils.get_ifaces():
        path = os.readlink(utils.inject_file_root("sys/class/net", iface_name))
        iface_path = utils.inject_file_root("sys/class/net", iface_name)
        iface_type = utils.find_iface_type(iface_name)
        macaddr = utils.get_first_line(iface_path / "address").strip()

        if "f1072004.mdio" in path:
            # switch
            port_label = utils.get_iface_label(iface_path)
            utils.append_iface(ifaces, iface_name, "eth", "eth", port_label, macaddr)
        elif "f1034000.ethernet" in path:
            # WAN port
            utils.append_iface(ifaces, iface_name, "eth", "eth", "WAN", macaddr)
        elif "pci0000:00" in path:
            # PCI
            m = re.search(r"/0000:00:0([0-3])\.0/", path)
            if m:
                slot = m.group(1)
                utils.append_iface(ifaces, iface_name, "wifi", "pci", slot, macaddr, slot_path=path)
            else:
                logger.warning("unknown PCI slot module")
        elif "f10f0000.usb3" in path:
            # front USB3.0
            utils.append_iface(ifaces, iface_name, iface_type, "usb", "USB Front", macaddr, slot_path=path)
        elif "f10f8000.usb3" in path:
            # rear USB3.0
            utils.append_iface(ifaces, iface_name, iface_type, "usb", "USB Rear", macaddr, slot_path=path)
        elif "f1058000.usb" in path:
            # USB2.0 on the PCI connector 3
            utils.append_iface(ifaces, iface_name, iface_type, "pci", "3", macaddr, slot_path=path)
        elif "f1070000.ethernet" in path or "f1030000.ethernet" in path:
            # ethernet interfaces connected to switch - ignore them
            pass
        elif "virtual" in path:
            # virtual ifaces (loopback, bridges, ...) - we don't care about these
            #
            # `utils.get_ifaces` can return interfaces in random order, so interfaces with VLAN assigned
            # will be processed in second pass to ensure that its parent interface exists and is already processed.
            if iface_name in vlan_ifaces:
                second_pass_ifaces.append({"name": iface_name, "macaddr": macaddr})
        # TODO: add SFP - once it starts to work
        else:
            logger.warning("unknown interface type: %s", iface_name)

    # Second pass - process virtual interfaces with VLAN assigned.
    utils.process_vlan_interfaces(ifaces, second_pass_ifaces)

    return ifaces
