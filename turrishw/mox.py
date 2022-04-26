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

from . import utils

logger = logging.getLogger(__name__)


def _get_modules():
    modules = os.listdir(utils.inject_file_root('sys/bus/moxtet/devices'))
    # modules in /sys/bus/moxtet/devices/ are named moxtet-NAME.SEQUENCE
    modules = sorted(modules, key=lambda x: x.split('.')[-1])
    return modules


def get_interfaces():
    def append_iface(iface: str, if_type: str, bus: str, module_seq: int, port_label: str, macaddr: str):
        ifaces.append(utils.iface_info(iface, if_type, bus, module_seq, port_label, macaddr))

    def get_module_rank(name):
        seq = [i + 1 for i, s in enumerate(modules) if name in s]
        if seq:
            return seq[0]
        else:
            return 0

    modules = _get_modules()
    ifaces = []
    switch_idxs = [i + 1 for i, s in enumerate(modules) if 'topaz' in s or 'peridot' in s]
    for iface in utils.get_ifaces():
        path = os.readlink(utils.inject_file_root("sys/class/net", iface))
        iface_path = utils.inject_file_root("sys/class/net", iface)
        macaddr = utils.get_first_line(os.path.join(iface_path, "address")).strip()
        if "d0032004.mdio-mii" in path:
            # MDIO bus on MOXTET - for switches
            port_label = utils.get_iface_label(iface_path)
            switch_id = int(utils.get_first_line(os.path.join(iface_path, "phys_switch_id"))[0:2])
            # phys_switch_id is 0{sequence_num}000000, e.g. 00000000 for 1st
            # switch, 01000000 for 2nd and so on. Don't know why.
            # take just first 2 letters and convert to int
            switch_no = switch_idxs[switch_id]
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
