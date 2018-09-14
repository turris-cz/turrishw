#!/usr/bin/env python3
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
from turrishw import __P_ROOT__
from . import _utils

def _get_modules():
    return os.listdir(__P_ROOT__+'sys/bus/moxtet/devices')


def get_interfaces():
    ifaces = {}
    _utils.iface_append(ifaces, "eth0", "E0")
    modules = _get_modules()
    peridot_cnt = sum(1 for m in modules if "peridot" in m)
    topaz_cnt = sum(1 for m in modules if "topaz" in m)
    ports_num = peridot_cnt * 8 + topaz_cnt * 4
    sfp_cnt = sum(1 for m in modules if "sfp" in m)
    if peridot_cnt == 0:
        if sfp_cnt == 1:
            _utils.iface_append(ifaces, "eth1", "SFP port")
    else:
        if sfp_cnt == 1:
            _utils.iface_append(ifaces, "sfp", "SFP port")
    for i in range(ports_num):
        _utils.iface_append(ifaces, "lan{}".format(i + 1),
                     "E{}-{}".format(int(i/4) + 1, i % 4 + 1))
    return ifaces
