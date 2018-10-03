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


def get_iface_state(iface):
    from turrishw import __P_ROOT__
    with open(os.path.join(__P_ROOT__, 'sys/class/net/{}/operstate'.format(iface)), 'r') as f:
        operstate = f.read()
        if operstate[:-1] == "up":
            return "up"
        else:
            return "down"


def get_iface_speed(iface):
    from turrishw import __P_ROOT__
    with open(os.path.join(__P_ROOT__, 'sys/class/net/{}/speed'.format(iface)), 'r') as f:
        speed = f.readline()
        return int(speed)


def iface_info(iface, desc):
    return {"name": iface, "description": desc, "state": get_iface_state(iface),
            "link_speed": get_iface_speed(iface)}


def ifaces_array2dict(ifaces_array):
    d = {}
    for iface in ifaces_array:
        name = iface["name"]
        d[name] = {i:iface[i] for i in iface if i!='name'}
    return d
