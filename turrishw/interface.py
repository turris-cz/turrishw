# Copyright (c) 2025, CZ.NIC, z.s.p.o. (http://www.nic.cz/)
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
import re
import typing
from dataclasses import dataclass
from enum import Enum


class State(str, Enum):
    UP = "up"
    DOWN = "down"


@dataclass
class Interface:
    name: str
    type: str
    bus: str
    slot: str
    macaddr: str
    module_id: int = 0
    link_speed: int = 0
    state: State = State.DOWN
    vlan_id: typing.Optional[int] = None
    slot_path: typing.Optional[str] = None
    qmi_device: typing.Optional[str] = None
    vendor: typing.Optional[str] = None
    pci_id: typing.Optional[str] = None

    @property
    def sort_key(self):
        # lan1.200 -> ("lan", 1, 200)
        parts = [e for e in re.split(r"\.(\d+)$", self.name, maxsplit=1) if e]
        name, suffix = (parts[0], int(parts[1])) if len(parts) == 2 else (parts[0], -1)

        splitted = [e for e in re.split(r"(\d+)$", name, maxsplit=1) if e]
        if len(splitted) == 1:
            return splitted[0], -1, suffix  # eth preceeds eth0
        return splitted[0], int(splitted[1]), suffix
