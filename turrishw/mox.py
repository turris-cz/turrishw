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
import logging
import os
import re
import typing

from . import utils

logger = logging.getLogger(__name__)


def _get_modules():
    modules = os.listdir(utils.inject_file_root('sys/bus/moxtet/devices'))
    # modules in /sys/bus/moxtet/devices/ are named moxtet-NAME.SEQUENCE
    modules = sorted(modules, key=lambda x: x.split('.')[-1])
    return modules


def _get_switch_id(iface_path: str) -> int:
    """Get id (number) of ethernet switch based on given interface path.

    This is Mox specific function as other Turris devices have fixed ethernet ports layout.

    It is useful to be able to figure out which switch the port belongs to
    and use that information to determine which physical Mox module that port belongs to.

    Read switch name from the result of `readlink /sys/class/net/<iface>/device/of_node`,
    and try to match the `switchX@Y` pattern in path.
    These `switchX@Y` identifiers should remain stable because they are defined in kernel DTS.
    """
    link_path = os.readlink(os.path.join(iface_path, "device/of_node"))
    m = re.search(r"switch([0-2])@[0-9]+$", link_path)  # maximum of three ethernet switches is supported in Mox
    if not m:
        return 0  # fallback to 0 (first switch)

    return int(m.group(1))


def get_interfaces() -> typing.Dict[str, dict]:
    def append_iface(name: str, if_type: str, bus: str, module_seq: int, port_label: str, macaddr: str):
        ifaces[name] = utils.iface_info(name, if_type, bus, module_seq, port_label, macaddr)

    def get_module_rank(name):
        seq = [i + 1 for i, s in enumerate(modules) if name in s]
        if seq:
            return seq[0]
        else:
            return 0

    modules = _get_modules()
    ifaces = {}
    switch_idxs = [i + 1 for i, s in enumerate(modules) if 'topaz' in s or 'peridot' in s]
    for iface in utils.get_ifaces():
        path = os.readlink(utils.inject_file_root("sys/class/net", iface))
        iface_path = utils.inject_file_root("sys/class/net", iface)
        macaddr = utils.get_first_line(os.path.join(iface_path, "address")).strip()
        if "d0032004.mdio-mii" in path:
            # MDIO bus on MOXTET - for switches
            port_label = utils.get_iface_label(iface_path)
            switch_id = _get_switch_id(iface_path)
            switch_no = switch_idxs[switch_id]  # Mox module number based on the actual module topology
            if port_label == "SFP":
                sfp_seq = get_module_rank("sfp")
                append_iface(iface, "eth", "sfp", sfp_seq, port_label, macaddr)
            else:  # everything else should be ethernet
                append_iface(iface, "eth", "eth", switch_no, port_label, macaddr)
        elif "d0030000.ethernet" in path:
            # ethernet port on the CPU board
            append_iface(iface, "eth", "eth", 0, "ETH0", macaddr)
        elif "d0040000.ethernet" in path:
            # ethernet on the MOXTET connector
            # when some switches are connected, it shouldn't be touched (it's
            # "connected to switches"). However, if only SFP is connected, it's
            # actually the SFP interface
            sfp_seq = get_module_rank("sfp")
            if not switch_idxs and sfp_seq:
                append_iface(iface, "eth", "sfp", sfp_seq, "SFP", macaddr)
        elif "d00d0000.sdhci" in path:
            # SDIO on the CPU board
            append_iface(iface, "wifi", "sdio", 0, "0", macaddr)
        elif "d0070000.pcie" in path:
            # PCIe on the MOXTET connector
            # can be PCI (B) or USB3.0 (F) module
            if "usb3" in path:
                m = re.search('/3-([0-4])/', path)
                if m:
                    usb_seq = get_module_rank("usb3.0")
                    port = m.group(1)
                    append_iface(iface, utils.find_iface_type(iface), "usb", usb_seq, port, macaddr)
                else:
                    logger.warning("unknown port on USB3.0 module")
            else:  # PCI module
                pci_seq = get_module_rank("pci")
                append_iface(iface, utils.find_iface_type(iface), "pci", pci_seq, "0", macaddr)
        elif "d0058000.usb" in path:
            # USB on the CPU module
            append_iface(iface, utils.find_iface_type(iface), "usb", 0, "0", macaddr)
        elif "d005e000.usb" in path:
            # USB2.0 on the MOXTET connector
            # the only option now is USB device on PCI module
            pci_seq = get_module_rank("pci")
            append_iface(iface, utils.find_iface_type(iface), "pci", pci_seq, "0", macaddr)
        elif "virtual" in path:
            # virtual ifaces (loopback, bridges, ...) - we don't care about these
            pass
        else:
            logger.warning("unknown interface type: %s", iface)
    return ifaces
