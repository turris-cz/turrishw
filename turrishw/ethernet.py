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
from . import network
from ._utils import path_soc as _path_soc
from ._utils import sysstrip as _sysstrip


class Ethernet:
    """Ethernet socket representation.
    """
    def __init__(self, syspath):
        assert self.syspath_is(syspath)
        self._syspath = syspath

    @staticmethod
    def dev_type():
        """Common device function returning device type as a string.
        """
        return "Ethernet"

    @staticmethod
    def syspath_is(syspath):
        """Common identification function of devices. It returns True if
        syspath points to ethernet socket/device. Otherwise returns False.
        """
        return os.path.realpath(syspath).endswith('.ethernet')

    @property
    def dev_id(self):
        """Returns unique ethernet socket id.
        """
        return os.path.basename(os.path.realpath(self._syspath))

    @property
    def speed(self):
        """Currently negotiated speed in MB.
        """
        # It's reported in network interface not in ethernet device because of
        # that we are going to net directory. Also there seems to be no
        # situation when there is more then one interface directly associated
        # with one device.
        upper = os.path.join(self._syspath, 'net')
        interface = os.listdir(upper)[0]
        with open(os.path.join(upper, interface, 'speed')) as file:
            return int(_sysstrip(file.read()))

    @property
    def interfaces(self):
        """Returns dict of associated network interfaces key being name of
        interface and value interface objec.
        """
        res = dict()
        netpath = os.path.join(self._syspath, 'net')
        for link in os.listdir(netpath):
            res[link] = network.Interface(link, os.path.join(netpath, link))
        return res

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
        eth['speed'] = self.speed
        eth['net'] = []
        for link in self.interfaces:
            eth['net'].append(link)
        eth['paired'] = self.paired
        if self.paired:
            eth['another'] = self.another
        res[self.dev_id] = eth


class Switch:
    """Ethernet switch representation.
    """
    def __init__(self):
        pass


def all_sockets():
    """Returns list of all ethernet sockets managed by Turris router.
    """
    return []


def cpu_sockets():
    """Returns dictionary of CPU ethernet sockets where keys are ethernet
    socket identifiers and values are objects representing ethernet sockets.
    """
    res = dict()
    psoc = _path_soc()
    for reg in os.listdir(psoc):
        if reg.endswith('.ethernet'):
            eth = Ethernet(os.path.join(psoc, reg))
            res[eth.dev_id] = eth
    return res


def switches():
    """Returns list of all switch chips configurable from Turris router.
    """
    return []


def _all(res):
    res['ethernet'] = dict()
    for _, eth in cpu_sockets().items():
        eth._all(res['ethernet'])
