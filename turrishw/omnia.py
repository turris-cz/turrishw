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

def _get_wifi_interfaces():
    ifaces = []
    for iface in utils.get_wifi_ifaces():
        path = os.readlink(os.path.join(__P_ROOT__, "sys/class/net", iface))
        if "pci0000:00/0000:00:01.0" in path:
            ifaces.append(utils.iface_info(iface, "wifi", "pci", 0, "1"))
        elif "pci0000:00/0000:00:02.0" in path:
            ifaces.append(utils.iface_info(iface, "wifi", "pci", 0, "2"))
        elif "pci0000:00/0000:00:03.0" in path:
            ifaces.append(utils.iface_info(iface, "wifi", "pci", 0, "3"))
        else:
            logger.warn("unrecognized type of wifi interface %s: path %s", iface, path)
    return ifaces


def get_interfaces():
    ifaces = []
    ifaces.append(utils.iface_info("eth2", "eth", "eth", 0, "WAN"))
    # SFP doesn't work at the moment
    ifaces.append(utils.iface_info("lan0", "eth", "eth", 0, "LAN0"))
    ifaces.append(utils.iface_info("lan1", "eth", "eth", 0, "LAN1"))
    ifaces.append(utils.iface_info("lan2", "eth", "eth", 0, "LAN2"))
    ifaces.append(utils.iface_info("lan3", "eth", "eth", 0, "LAN3"))
    ifaces.append(utils.iface_info("lan4", "eth", "eth", 0, "LAN4"))
    ifaces = ifaces + _get_wifi_interfaces()
    return ifaces
