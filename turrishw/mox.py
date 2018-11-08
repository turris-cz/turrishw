# Copyright (c) 2018, CZ.NIC, z.s.p.o. (http://www.nic.cz/)
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
from . import utils
from turrishw import __P_ROOT__

logger = logging.getLogger("turrishw")


def _get_modules():
    modules = os.listdir(os.path.join(__P_ROOT__, 'sys/bus/moxtet/devices'))
    # modules in /sys/bus/moxtet/devices/ are named moxtet-NAME.SEQUENCE
    modules = sorted(modules, key=lambda x: x.split('.')[-1])
    return modules

# unfortunatelly, AFAIK there is no way how one can determine module on
# which a specific interface resides. So sadly we must resort to our
# knowledge which features/interfaces are provided by which module...


def _get_sfp_interface(modules):
    peridot_cnt = sum(1 for m in modules if "peridot" in m)
    sfp_cnt = sum(1 for m in modules if "sfp" in m)
    if sfp_cnt == 1:
        # +1 because modules are indexed from 0, but we consider 0 to be CPU
        sfp_seq = [i + 1 for i, s in enumerate(modules) if 'sfp' in s][0]
        # TODO: determine whether there is metalic or fiber module
        sfp_type = "eth"
        if peridot_cnt == 0:
            # if there is no peridot module, SPF is eth1
            return [utils.iface_info("eth1", sfp_type, "sfp", sfp_seq, "0")]
        else:
            # if there is peridot (switch) module (closer to CPU), SPF is
            # considered to be part of that switch. And it's called spf.
            return [utils.iface_info("sfp", sfp_type, "sfp", sfp_seq, "0")]
    return []


def _get_eth_interfaces(modules):
    ifaces = []
    ifaces.append(utils.iface_info("eth0", "eth", "eth", 0, "0"))
    lan_idx = 1
    for peridot in [idx + 1 for idx, s in enumerate(modules) if 'peridot' in s]:
        print("peridot", peridot)
        for i in range(8):
            ifaces.append(utils.iface_info("lan{}".format(lan_idx), "eth",
                                           "eth", peridot, str(i)))
            lan_idx += 1

    for topaz in [idx + 1 for idx, s in enumerate(modules) if 'topaz' in s]:
        print("topaz", topaz)
        for i in range(4):
            ifaces.append(utils.iface_info("lan{}".format(lan_idx), "eth",
                                           "eth", topaz, str(i)))
            lan_idx += 1
    # TODO: detect external (just USB?) ethernet interfaces
    return ifaces


def _get_wifi_interfaces(modules):
    ifaces = []
    for iface in utils.get_wifi_ifaces():
        path = os.readlink(os.path.join(__P_ROOT__, "sys/class/net", iface))
        if "pci0000:00/0000:00:00.0" in path:
            # so far only the non-passthrough PCI module is ready. So if we see
            # PCI card, we know it may only be on that module. When the
            # passthrough PCI module will be ready, this will have to be changed.
            pci_seq = [i + 1 for i, s in enumerate(modules) if 'pci' in s]
            if not pci_seq:
                logger.warn("detected PCI wifi card, but no PCI module found")
                continue
            ifaces.append(utils.iface_info(iface, "wifi", "pci", pci_seq[0], "0"))
        elif "mmc0:0001" in path:
            ifaces.append(utils.iface_info(iface, "wifi", "sdio", 0, "0"))
        else:
            # TODO: detect external (just USB?) wifi interfaces
            logger.warn("unrecognized type of wifi interface %s: path %s", iface, path)
    return ifaces


def get_interfaces():
    modules = _get_modules()
    ifaces = _get_sfp_interface(modules)
    ifaces = ifaces + _get_eth_interfaces(modules)
    ifaces = ifaces + _get_wifi_interfaces(modules)
    return ifaces
