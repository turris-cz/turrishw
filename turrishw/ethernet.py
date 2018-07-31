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
import subprocess
from . import device, network, board
from ._utils import path_soc as _path_soc
from ._utils import sysstrip as _sysstrip

__P_ETH0__ = '/sys/class/net/eth0/device'
__P_ETH1__ = '/sys/class/net/eth1/device'
__P_ETH2__ = '/sys/class/net/eth2/device'


class Ethernet(device.Device):
    """Ethernet port representation.
    """
    @staticmethod
    def dev_type():
        return "Ethernet"

    def speed(self):
        """Currently negotiated speed in MB.
        """
        raise NotImplementedError()

    def interfaces(self):
        """Returns dict of associated network interfaces key being name of
        interface and value interface object.

        This method explicitly returns None when swconfig is used as in such
        case there are no network interfaces associated with ethernet port.
        """
        raise NotImplementedError()

    def plugged(self):
        """Returns True if port is in use (wire is connected). Otherwise
        returns False.
        """
        raise NotImplementedError()

    def switch(self):
        """Returns switch instance it belongs to. It returns None if this
        port does not belongs to switch (in such case it belongs to CPU).
        """
        raise NotImplementedError()

    def paired(self):
        """Returns True or False when opposite ethernet port is or isn't also
        managed by this system. If it is then it can be received by `another`.
        """
        return self.another() is not None

    def another(self):
        """Returns ethernet port that is managed by system that is directly
        connected to other side of this ethernet port. If there is no such
        known port then it returns None;
        """
        pmap = {
            "Turris": {
                "ffe24000.ethernet": EthernetSWConfig(6),
                "ffe25000.ethernet": EthernetSWConfig(0),
                "swconfig-switch0-6": EthernetCPU(__P_ETH2__),
                "swconfig-switch0-0": EthernetCPU(__P_ETH1__)
                },
            "Turris Omnia": {
                "f1030000.ethernet": EthernetSWConfig(5),
                "f1070000.ethernet": EthernetSWConfig(6),
                "swconfig-switch0-5": EthernetCPU(__P_ETH0__),
                "swconfig-switch0-6": EthernetCPU(__P_ETH2__)
                }
            }
        bname = board.name()
        did = self.dev_id()
        if bname in pmap and did in pmap[bname]:
            return pmap[bname][did]
        return None

    def _all(self, res):
        eth = dict()
        eth['speed'] = self.speed()
        eth['net'] = []
        for link in self.interfaces():
            eth['net'].append(link)
        eth['plugged'] = self.plugged()
        eth['paired'] = self.paired()
        if self.paired():
            eth['another'] = self.another().dev_id()
        res[self.dev_id()] = eth


class EthernetCPU(Ethernet):
    """Representation of ethernet port in CPU.
    """
    def __init__(self, syspath):
        assert self.syspath_is(syspath)
        self._syspath = syspath

    @staticmethod
    def syspath_is(syspath):
        return os.path.realpath(syspath).endswith('.ethernet')

    def dev_id(self):
        return os.path.basename(os.path.realpath(self._syspath))

    def _from_net(self, fname):
        """Most of the information are reported in network link and not in
        device it self. This helps with sourcing that.
        Only one network interface is expected to be present. And even if there
        is some tagged sub-interface associated with device main interface
        should always be first in alphabet and first in dir listing.
        """
        upper = os.path.join(self._syspath, 'net')
        interface = os.listdir(upper)[0]
        with open(os.path.join(upper, interface, fname)) as file:
            return _sysstrip(file.read())

    def speed(self):
        return int(self._from_net('speed'))

    def interfaces(self):
        res = dict()
        netpath = os.path.join(self._syspath, 'net')
        for link in os.listdir(netpath):
            res[link] = network.Interface(link, os.path.join(netpath, link))
        return res

    def plugged(self):
        return self._from_net('operstate') == 'up'

    def switch(self):
        return None


class EthernetSWConfig(Ethernet):
    """Representation of ethernet port from swconfig switch.
    """
    def __init__(self, port):
        self._port = port

    @staticmethod
    def syspath_is(_):
        """Common identification function of devices. It returns always False
        for this object as swconfig is not represented in /sys.
        """
        return False

    def dev_id(self):
        """Returns unique ethernet port id.
        """
        return 'swconfig-switch0-' + str(self._port)

    def _get_link(self, field):
        # Expected format:
        # Port 4:
        # ...
        #   link: port:4 link:up speed:1000baseT full-duplex
        linkln = None
        for line in subprocess.check_output(
                ['swconfig', 'dev', 'switch0', 'port', str(self._port), 'show']
        ).decode('utf-8').splitlines()[1:]:
            if line.startswith('\tlink: '):
                linkln = line[6:].strip()
                break
        for opt in linkln.split():
            if ':' in opt:
                splt = opt.split(':', 1)
                if splt[0] == field:
                    return splt[1].strip()
        return None

    def speed(self):
        spd = self._get_link('speed')
        if spd is not None:
            return spd[:-5]  # remote baseT from end
        return "1000"  # As a falback we are 1Gb router

    def interfaces(self):
        # TODO what should we return here when there are no interfaces
        return []

    def plugged(self):
        return self._get_link('link') == 'up'

    def switch(self):
        return SwitchSWConfig()


class Switch(device.Device):
    """Ethernet switch representation.
    """
    @staticmethod
    def dev_type():
        return "Switch"

    def ports(self):
        """Returns dictionary of all ethernet ports of this swich. Keys are
        unique ethernet port identifiers and values are objects representing
        given ports.
        """
        raise NotImplementedError()

    def _all(self, res):
        switch = dict()
        switch['ports'] = dict()
        for _, sock in self.ports().items():
            sock._all(switch['ports'])
        res[self.dev_id()] = switch


class SwitchSWConfig(Switch):
    """swconfig switch representation.
    Don't expect too much, parsing swconfig output is nightmare and would be
    prone to error instead this uses device detection and just fakes output.
    """
    @staticmethod
    def syspath_is(_):
        # Just to have this common function. Although there is swconfig switch
        # representation in /sys it contains no identification and is useless.
        return False

    @staticmethod
    def is_present():
        """Returns either True if swconfig is used and its configuration
        supported or False if swconfig is either not present or for given host
        there is no known configuration.
        """
        name = board.name()
        if name == "Turris" or name == "Turris Omnia":
            with open(os.devnull, 'w') as devnull:
                return subprocess.call(
                    ['which', 'swconfig'],
                    stdout=devnull, stderr=devnull) == 0
        return False

    def dev_id(self):
        return "swconfig-switch0"

    def ports(self):
        res = dict()
        for i in range(7):
            eth = EthernetSWConfig(i)
            res[eth.dev_id()] = eth
        return res


# TODO DSA switch


def all_ports():
    """Returns dictionary of all ethernet ports managed by Turris router. Keys
    are port identifiers and values are objects representing given ethernet
    port.
    """
    res = dict()
    res.update(cpu_ports())
    for _, switch in switches().items():
        res.update(switch.ports())
    return res


def outside_ports():
    """Returns dictionary of all ethernet ports that are externally accessible
    (not terminated to some other port on board). Keys in returned dictionary
    are ports identifiers and values are objects representing given ethernet
    port.
    """
    res = dict()
    for soc_id, obj in all_ports().items():
        if not obj.paired():
            res[soc_id] = obj
    return res


def cpu_ports():
    """Returns dictionary of CPU ethernet ports where keys are ethernet
    port identifiers and values are objects representing ethernet ports.
    """
    res = dict()
    psoc = _path_soc()
    for reg in os.listdir(psoc):
        pth = os.path.join(psoc, reg)
        if EthernetCPU.syspath_is(pth):
            eth = EthernetCPU(pth)
            res[eth.dev_id] = eth
    return res


def switches():
    """Returns dictionary of all switch chips configurable from Turris router.
    Keys are uniq identifiers of switch and values are objects representing
    given device.
    """
    res = dict()
    if SwitchSWConfig.is_present():
        switch = SwitchSWConfig()
        res[switch.dev_id()] = switch
    return res


def _all(res):
    res['ethernet'] = dict()
    res['ethernet']['cpu'] = dict()
    for _, eth in cpu_ports().items():
        eth._all(res['ethernet']['cpu'])
    res['ethernet']['switch'] = dict()
    for _, switch in switches().items():
        switch._all(res['ethernet']['switch'])
