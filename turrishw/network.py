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
from ._utils import sysstrip as _sysstrip

__P_NET__ = "/sys/class/net"


class Interface:
    """Network interface representation.
    """
    def __init__(self, name, syspath):
        self._name = name
        self._syspath = syspath

    def name(self):
        """Name of network interface.
        """
        return self._name

    def hwaddr(self):
        """Hardware address (MAC address)
        """
        with open(os.path.join(self._syspath, 'address')) as file:
            return _sysstrip(file.read())

    def type(self):
        """Returns string representing type of network interface. This is just
        limited detection and can return following strings:
          "ethernet" in case of ethernet
          "unknown" in all other cases
        """
        if not self.virtual():
            return self.device().dev_type()
        return "unknown"

    def virtual(self):
        """Returns True if this interface is virtual. False is returned if
        there is some device associated with this interface.
        """
        return not os.path.islink(os.path.join(self._syspath, 'device'))

    def device(self):
        """Returns device associated with this network interface.
        """
        if not self.virtual():
            from .device import sys_device
            return sys_device(os.path.join(self._syspath, 'device'))
        return None

    def _all(self, res):
        inter = dict()
        inter['type'] = self.type()
        inter['virtual'] = self.virtual()
        if not self.virtual():
            inter['device'] = self.device().dev_id()
            inter['hwaddr'] = self.hwaddr()
        res[self._name] = inter


def all_interfaces():
    """Returns dictionary with all available interfaces. Key is name of interface
    and value is object representing interface in TurrisHW.
    """
    res = dict()
    for inter in os.listdir(__P_NET__):
        res[inter] = Interface(inter, os.path.join(__P_NET__, inter))
    return res


def _all(res):
    res['net'] = dict()
    for _, inter in all_interfaces().items():
        inter._all(res['net'])
