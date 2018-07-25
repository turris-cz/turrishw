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
from ._utils import sysstrip

__P_SYS_PLATFORM__ = '/sys/devices/platform'
# Path with SOC identification directory on PowerPC
__P_SOC_INTERNAL_REGS__ = '/sys/devices/platform/soc/soc:internal-regs'


class _Ethernet:
    """
    Ethernet socket representation.
    """
    def __init__(self, name, syspath):
        self._name = name
        self._syspath = syspath

    @property
    def name(self):
        """Name of ethernet interface associated with this socket.
        """
        return self._name

    @property
    def hwaddr(self):
        """Hardware address (MAC address)
        """
        with open(os.path.join(self._syspath, 'address')) as file:
            return sysstrip(file.read())

    @property
    def speed(self):
        """Currently negotiated speed in MB.
        """
        with open(os.path.join(self._syspath, 'speed')) as file:
            return sysstrip(file.read())

    @property
    def switch(self):
        """Returns switch instance it belongs to. It returns None if this
        socket does not belongs to switch (in such case it belongs to CPU).
        """
        # TODO
        return None

    @property
    def paired(self):
        """Returns True or False when opposite ethernet socket is or isn't also
        managed by this system. If it is then it can be received by `another`.
        """
        # TODO
        return False

    @property
    def another(self):
        """Returns ethernet socket that is managed by system that is directly
        connected to other side of this ethernet socket. If there is no such
        known socket then it returns None;
        """
        # TODO
        return None

    def _all(self, res):
        eth = dict()
        eth['hwaddr'] = self.hwaddr
        eth['speed'] = self.speed
        res[self.name] = eth


class _Switch:
    """
    Ethernet switch representation.
    """
    def __init__(self):
        pass


def all_sockets():
    """
    Returns list of all ethernet sockets managed by Turris router.
    """
    return []


def cpu_sockets():
    """
    Returns list of CPU ethernet sockets.
    """
    lst = []

    def _ifether(reg, subpath):
        if reg.endswith('.ethernet'):
            name = os.listdir(subpath)[0]
            lst.append(_Ethernet(name, os.path.join(subpath, name)))

    if os.path.isdir(__P_SOC_INTERNAL_REGS__):
        for reg in os.listdir(__P_SOC_INTERNAL_REGS__):
            _ifether(reg, os.path.join(__P_SOC_INTERNAL_REGS__, reg, 'net'))
    else:
        soc = next(dv for dv in os.listdir(__P_SYS_PLATFORM__)
                   if dv.startswith('soc@'))
        soc_path = os.path.join(__P_SYS_PLATFORM__, soc)
        for reg in os.listdir(soc_path):
            _ifether(reg, os.path.join(soc_path, reg, 'net'))
    return lst


def switches():
    """
    Returns list of all switch chips configurable from Turris router.
    """
    return []


def _all(res):
    res['ethernet'] = dict()
    for eth in cpu_sockets():
        eth._all(res['ethernet'])
