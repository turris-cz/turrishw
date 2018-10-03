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
import pprint
from . import utils

__P_ROOT__ = os.getenv("TURRISHW_ROOT", default="/")

def get_model():
    with open(os.path.join(__P_ROOT__, 'sys/firmware/devicetree/base/model'), 'r') as f:
        model = f.read()
        if "Mox" in model:
            return "MOX"
        elif "Omnia" in model:
            return "OMNIA"
        elif "Turris":
            return "TURRIS"
        else:
            return ""


def get_ifaces():
    from . import mox, omnia
    model = get_model()
    ifaces = []
    if model == "MOX":
        ifaces = mox.get_interfaces()
    elif model == "OMNIA":
        major_version = utils.get_TOS_major_version()
        if major_version >= 4:
            ifaces = omnia.get_interfaces()
        else:
            print("unsupported TOs version")
    else:
        print("unsupported model")
    return utils.ifaces_array2dict(ifaces)
    
