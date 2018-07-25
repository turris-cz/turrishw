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

__KNOWN_MODELS__ = {"Turris", "Turris Omnia"}
__P_MODEL__ = "/sys/firmware/devicetree/base/model"

__SERIAL_CMD__ = ['atsha204cmd', 'serial-number']

__P_PROC_MEMINFO__ = '/proc/meminfo'


def name():
    """
    Returns board name. You can expect following values:
      "Turris": For Turris 1.x boards
      "Turris Omnia": For Turris Omnia
      "unknown": If board is unknown or detection failed
    """
    if os.path.isfile(__P_MODEL__):
        with open(__P_MODEL__, 'r') as file:
            cont = file.read().strip().rstrip('\0')
        if cont in __KNOWN_MODELS__:
            return cont
    return "unknown"


def supported():
    """
    Returns True or False depending on if current host is supported by
    turrishw.
    In reality it is simple wrapper around name()
    """
    return name() != "unknown"


def serial():
    """
    Returns serial number of board.
    """
    return int(
        subprocess.check_output(__SERIAL_CMD__).decode('utf-8').strip(),
        16)


def memory():
    """
    Returns amount of system memory available in megabytes.
    """
    with open(__P_PROC_MEMINFO__) as file:
        total_l = file.readline()  # Total amount should be on first line
    assert total_l.startswith('MemTotal:')
    # TODO round to more common 2^n number?
    return int(total_l.split()[1])//1000


def _all(res):
    res['name'] = name()
    res['serial'] = serial()
    res['memory'] = memory()
