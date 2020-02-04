# Copyright (c) 2018-2021, CZ.NIC, z.s.p.o. (http://www.nic.cz/)
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
import logging
import re
from . import utils

logger = logging.getLogger(__name__)


def get_interfaces():
    def append_iface(iface, if_type, bus, port, macaddr):
        ifaces.append(utils.iface_info(iface, if_type, bus, 0, str(port), macaddr))

    major_version = utils.get_TOS_major_version()
    if major_version < 4:
        logger.warning("Unsupported TOS version (on Turris omnia): %d", major_version)
        return []

    ifaces = []
    for iface in utils.get_ifaces():
        path = os.readlink(utils.inject_file_root("sys/class/net", iface))
        iface_path = utils.inject_file_root("sys/class/net", iface)
        macaddr = utils.get_first_line(os.path.join(iface_path, "address")).strip()
        if "f1072004.mdio" in path:
            # switch
            port = int(utils.get_first_line(os.path.join(iface_path, "phys_port_name"))[1:])
            # phys_port_name is "p{number}", e.g. 'p1' - remove leading p and
            # convert to int
            append_iface(iface, "eth", "eth", "LAN" + str(port), macaddr)
        elif "f1034000.ethernet" in path:
            # WAN port
            append_iface(iface, "eth", "eth", "WAN", macaddr)
        elif "pci0000:00" in path:
            # PCI
            m = re.search(r'/0000:00:0([0-3])\.0/', path)
            if m:
                slot = m.group(1)
                append_iface(iface, "wifi", "pci", slot, macaddr)
            else:
                logger.warning("unknown PCI slot module")
        elif "f10f0000.usb3" in path:
            # front USB3.0
            append_iface(iface, utils.find_iface_type(iface), "usb", "front", macaddr)
        elif "f10f8000.usb3" in path:
            # rear USB3.0
            append_iface(iface, utils.find_iface_type(iface), "usb", "rear", macaddr)
        elif "f1058000.usb" in path:
            # USB2.0 on the PCI connector 3
            append_iface(iface, utils.find_iface_type(iface), "pci", 3, macaddr)
        elif "f1070000.ethernet" in path or "f1030000.ethernet" in path:
            # ethernet interfaces connected to switch - ignore them
            pass
        elif "virtual" in path:
            # virtual ifaces (loopback, bridges, ...) - we don't care about these
            pass
        # TODO: add SFP - once it starts to work
        else:
            logger.warning("unknown interface type: %s", iface)
    return ifaces
