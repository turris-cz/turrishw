# Copyright (c) 2018-2025, CZ.NIC, z.s.p.o. (http://www.nic.cz/)
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
from pathlib import Path

from . import utils
from .interface import Interface

logger = logging.getLogger(__name__)


def _get_modules():
    modules = os.listdir(utils.inject_file_root("sys/bus/moxtet/devices"))
    # modules in /sys/bus/moxtet/devices/ are named moxtet-NAME.SEQUENCE
    modules = sorted(modules, key=lambda x: x.split(".")[-1])
    return modules


def _get_switch_id(iface_path: Path) -> int:
    """Get id (number) of ethernet switch based on given interface path.

    This is Mox specific function as other Turris devices have fixed ethernet ports layout.

    It is useful to be able to figure out which switch the port belongs to
    and use that information to determine which physical Mox module that port belongs to.

    Read switch name from the result of `readlink /sys/class/net/<iface>/device/of_node`,
    and try to match the `switchX@Y` pattern in path.
    These `switchX@Y` identifiers should remain stable because they are defined in kernel DTS.
    """
    link_path = os.readlink(iface_path / "device/of_node")
    m = re.search(r"switch([0-2])@[0-9]+$", link_path)  # maximum of three ethernet switches is supported in Mox
    if not m:
        return 0  # fallback to 0 (first switch)

    return int(m.group(1))


def get_interfaces() -> typing.List[Interface]:
    def get_module_rank(name):
        seq = [i + 1 for i, s in enumerate(modules) if name in s]
        if seq:
            return seq[0]
        else:
            return 0

    modules = _get_modules()
    ifaces: typing.List[Interface] = []
    switch_idxs = [i + 1 for i, s in enumerate(modules) if "topaz" in s or "peridot" in s]

    virtual_ifaces: typing.List[typing.Dict[str, str]] = []
    vlan_ifaces: typing.List[str] = utils.get_vlan_interfaces()

    for iface_name in utils.get_ifaces():
        iface_path: Path = utils.inject_file_root("sys/class/net", iface_name)
        iface_abspath: Path = iface_path.resolve()
        iface_path_str = str(iface_abspath)
        iface_type = utils.find_iface_type(iface_name)
        macaddr = utils.get_first_line(iface_path / "address").strip()

        if "d0032004.mdio-mii" in iface_path_str:
            # MDIO bus on MOXTET - for switches
            port_label = utils.get_iface_label(iface_path)
            switch_id = _get_switch_id(iface_path)
            switch_no = switch_idxs[switch_id]  # Mox module number based on the actual module topology
            if port_label == "SFP":
                sfp_seq = get_module_rank("sfp")
                ifaces.append(utils.make_iface(iface_name, "eth", "sfp", port_label, macaddr, module_seq=sfp_seq))
            else:  # everything else should be ethernet
                ifaces.append(utils.make_iface(iface_name, "eth", "eth", port_label, macaddr, module_seq=switch_no))
        elif "d0030000.ethernet" in iface_path_str:
            # ethernet port on the CPU board
            ifaces.append(utils.make_iface(iface_name, "eth", "eth", "ETH0", macaddr, module_seq=0))
        elif "d0040000.ethernet" in iface_path_str:
            # ethernet on the MOXTET connector
            # when some switches are connected, it shouldn't be touched (it's
            # "connected to switches"). However, if only SFP is connected, it's
            # actually the SFP interface
            sfp_seq = get_module_rank("sfp")
            if not switch_idxs and sfp_seq:
                ifaces.append(utils.make_iface(iface_name, "eth", "sfp", "SFP", macaddr, module_seq=sfp_seq))
        elif "d00d0000.sdhci" in iface_path_str:
            # SDIO on the CPU board
            ifaces.append(
                utils.make_iface(iface_name, "wifi", "sdio", "0", macaddr, module_seq=0, slot_path=iface_path_str)
            )
        elif "d0070000.pcie" in iface_path_str:
            # PCIe on the MOXTET connector
            # can be PCI (B) or USB3.0 (F) module
            if "usb3" in iface_path_str:
                m = re.search("/3-([0-4])/", iface_path_str)
                if m:
                    usb_seq = get_module_rank("usb3.0")
                    port = m.group(1)
                    ifaces.append(
                        utils.make_iface(
                            iface_name,
                            iface_type,
                            "usb",
                            port,
                            macaddr,
                            module_seq=usb_seq,
                            slot_path=iface_path_str,
                            parent_device_abs_path=iface_abspath,
                        )
                    )
                else:
                    logger.warning("unknown port on USB3.0 module")
            else:  # PCI module
                pci_seq = get_module_rank("pci")
                ifaces.append(
                    utils.make_iface(
                        iface_name, iface_type, "pci", "0", macaddr, module_seq=pci_seq, slot_path=iface_path_str
                    )
                )
        elif "d0058000.usb" in iface_path_str:
            # USB on the CPU module
            ifaces.append(
                utils.make_iface(
                    iface_name,
                    iface_type,
                    "usb",
                    "0",
                    macaddr,
                    module_seq=0,
                    slot_path=iface_path_str,
                    parent_device_abs_path=iface_abspath,
                )
            )
        elif "d005e000.usb" in iface_path_str:
            # USB2.0 on the MOXTET connector
            # the only option now is USB device on PCI module
            pci_seq = get_module_rank("pci")
            ifaces.append(
                utils.make_iface(
                    iface_name,
                    iface_type,
                    "pci",
                    "0",
                    macaddr,
                    module_seq=pci_seq,
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
