# Copyright (c) 2018-2025, CZ.NIC, z.s.p.o. (http://www.nic.cz/)
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

import functools
import logging
import os
import re
import typing
from pathlib import Path

# ENV variable is needed for blackbox testing with foris-controller
TURRISHW_FILE_ROOT = os.getenv("TURRISHW_ROOT", "/")
WIFI_PATH_REGEX = re.compile(r"sys/devices/platform/(.*)$")
# matches mox and omnia
QMI_OMNIA_MOX_PATH = r"/sys/devices/platform/soc/soc:internal-regs" \
    r"(?:@[a-f0-9]{8})?/[a-f0-9]{8}.usb/usb\d/\d-1"
# matches turris1x
QMI_TURRIS_PATH = r"/sys/devices/platform/ffe08000.pcie/pci0002:00/" \
    r"0002:00:00.0/0002:01:00.0/usb[2,3]/[2,3]-[2,1]"

# combination of above (OR)
QMI_PATH_REGEX = re.compile(f"{QMI_TURRIS_PATH}|{QMI_OMNIA_MOX_PATH}")

# vendor regular expression
VENDOR = re.compile(r"0x([0-9a-z]+)$")

# vendor db path
PCI_VENDORS_DB = "/usr/share/hwdata/pci.ids"

logger = logging.getLogger(__name__)


@functools.lru_cache(200)
def get_vendor_from_db(ven: str) -> str:
    """Helper function for quries on file db
    containing information about PCI vendor and type"""
    with open(PCI_VENDORS_DB, "r") as f:
        for line in f.readlines():
            if line.startswith(ven):
                # the magic is because the string looks like:
                # `<ven> <full vendor name with spaces>`
                return line.split(" ", 1)[-1].strip() or ven
    # return the hex number as fallback
    return ven


def inject_file_root(*paths) -> Path:
    """Inject TURRISHW_FILE_ROOT prefix to file path(s)"""
    return Path(TURRISHW_FILE_ROOT, *paths)


def get_first_line(filename: Path) -> str:
    with open(filename, 'r') as f:
        return f.readline()


def get_iface_state(iface):
    operstate = get_first_line(inject_file_root('sys/class/net/{}/operstate'.format(iface)))
    if operstate.strip() == "up":
        return "up"
    else:
        return "down"


def get_iface_speed(iface):
    try:
        speed = get_first_line(inject_file_root('sys/class/net/{}/speed'.format(iface)))
        speed = int(speed)
        # sometimes we can get -1 from sysfs, meaning speed is not negotiated yet
        return max(speed, 0)
    except (OSError, ValueError):
        # can't read the file or can't convert value to int (file is empty)
        return 0


def get_iface_vendor(iface: str) -> typing.Optional[str]:
    try:
        # get base vendor string
        vendor = get_first_line(inject_file_root('sys/class/net/{}/device/vendor'.format(iface)))
        # strip vendor `0x` prefix
        vendor = VENDOR.match(vendor).groups()[0]
        return get_vendor_from_db(vendor)

    except FileNotFoundError:
        return None


def get_iface_label(iface_path: Path) -> str:
    """Get inteface label, e.g. lan1, by given interface path

    Search /sys subsystem for `<iface_path>/of_node/label`.
    """
    return get_first_line(iface_path / "of_node/label").rstrip("\x00").upper()


def get_qmi_modem_device(interface_path: Path) -> typing.Optional[str]:
    """Get the control device name (/dev/cdc-wdmX) for given qmi interface.

    interface_path could be for example:
    /sys/devices/platform/soc/soc:internal-regs@d0000000/d005e000.usb/usb1/1-1/1-1:1.4/net/wwan0
    => wwan0

    control device path could be for example:
    /sys/devices/platform/soc/soc:internal-regs@d0000000/d005e000.usb/usb1/1-1/1-1:1.4/usbmisc/cdc-wdm0
    => cdc-wdm0

    Basically try to find pair: wwan0 -> /dev/cdc-wdm0

    Please note that it is not guaranteed that interface number will match the
    control device number (wwanX <-> cdc-wdmX) every time.
    In case of multiple QMI devices, it can be paired in arbitrary order.

    For example:
    wwan0 -> cdc-wdm1
    wwan1 -> cdc-wdm0

    In case none device is found, return None.
    """
    # pathlib.Path object is necessary here, so we can resolve symlink to the real path on filesystem
    parent_dev_path = interface_path.resolve().parent.parent  # strip the 'net/wwanX' suffix

    # Do lookup among usb devices and try to find the device that share the same parent with interface path.
    # Basically the one that belongs to the same '/sys/class/.../usbX/<some_numbers>' parent.
    usb_sys_devices_path = inject_file_root("sys/class/usbmisc")
    for usbdev in usb_sys_devices_path.iterdir():
        # ignore anything other that symlinks to prevent accidental reading of garbage
        if usbdev.is_symlink():
            usbdev_abspath = usbdev.resolve()
            if parent_dev_path in usbdev_abspath.parents:
                return f"/dev/{usbdev_abspath.name}"

    return None


def find_iface_type(iface):
    path = inject_file_root('sys/class/net', iface)
    if path.joinpath("phy80211").is_dir():
        return "wifi"
    if path.joinpath("qmi").is_dir():
        return "wwan"
    # TODO: support other protocols of LTE modems
    return "eth"


def get_ifaces():
    path = inject_file_root('sys/class/net')
    for f in path.iterdir():
        # we only need links, not files
        if f.is_symlink():
            yield f.name


def get_vlan_interfaces() -> typing.List[str]:
    """Get name of all interfaces, which has VLAN id set.

    Take a look into `/proc/net/vlan/` provided by kernel.
    Based on the kernel documentation, there should be only only `config` and interface-like files
    (i.e. <interface_name>.<vlan_number>) in `/proc/net/vlan`.
    Ignore the `config` and fetch all interface-like looking files.

    For instance:

    ```
    # ls /proc/net/vlan/
    config    eth2.128
    ```

    Please note that alternative approach could be to parse `/proc/net/vlan/config` as single source of truth,
    to get all interfaces with VLAN id.
    But that would mean parsing text file, which formatting could be less stable between kernel versions
    than vlan interfaces representation on `/proc` subsystem.

    Return list of interfaces names.
    """

    path = inject_file_root("proc/net/vlan")
    if not path.is_dir():
        return []

    return [iface.name for iface in path.glob("*.*")]


def process_vlan_interfaces(
    first_pass_ifaces: typing.Dict[str, dict],
    second_pass_ifaces: typing.List[typing.Dict[str, str]]
) -> None:
    """Process virtual interfaces that have VLAN ID assigned.
    Reuse its parent interface properties and fill in the differences.

    For instance: eth2.100 should always be of the same type (wired ethernet) as its parent (eth2),
    but it could have a different MAC address.

    first_pass_ifaces: Physical interfaces detected in first pass processing.
    second_pass_ifaces: Virtual interfaces that need to be matched to their parent interfaces.
    """
    for virt_iface in second_pass_ifaces:
        iface_name = virt_iface["name"]
        macaddr = virt_iface["macaddr"]
        base_iface, vlan_id = iface_name.rsplit(".", maxsplit=1)
        vlan_id_no = int(vlan_id)

        # Parent interface (e.g. eth2) must be available and processed if we intend to reference it.
        # If we can't find the parent, ignore this interface.
        if base_iface in first_pass_ifaces:
            parent = first_pass_ifaces[base_iface]
            first_pass_ifaces[iface_name] = iface_info(
                iface_name, parent["type"], parent["bus"], parent["slot"], macaddr,
                vlan_id=vlan_id_no, module_id=parent["module_id"]
            )


def get_TOS_major_version():
    version = get_first_line(inject_file_root('etc/turris-version'))
    parts = version.split('.')
    return int(parts[0])


def append_iface(
    ifaces: typing.Dict[str, dict],
    name: str,
    if_type: str,
    bus: str,
    port_label: str,
    macaddr: str,
    slot_path: typing.Optional[str] = None,
    parent_device_abs_path: typing.Optional[Path] = None,
    module_seq: int = 0,
) -> None:
    """
    `slot_path` is optional argument, which is currently relevant only for wireless devices.
    If `slot_path` is reported by turrishw, then foris-controller can better match the present network devices
    to the uci configuration of wireless devices on Turris OS 6.0+.

    `parent_device_abs_path` is optional argument, useful only for additional processing of QMI devices data
    and usb devices in general.

    `module_id` is relevant only for Mox, fallback to 0 for other Turris models
    """
    if if_type == "wifi" and slot_path:
        ifaces[name] = iface_info(
            name, if_type, bus, port_label, macaddr, slot_path=wifi_strip_prefix(slot_path), module_id=module_seq
        )
    elif if_type == "wwan" and parent_device_abs_path:
        qmi_control_dev_path = get_qmi_modem_device(parent_device_abs_path)
        if not qmi_control_dev_path:
            logger.warning(f"Failed to find qmi control device for interface '{name}', ignoring the interface.")
            return

        ifaces[name] = iface_info(
            name, if_type, bus, port_label, macaddr, slot_path=qmi_filter_slot_path(slot_path), qmi_device=qmi_control_dev_path, module_id=module_seq
        )
    else:
        ifaces[name] = iface_info(name, if_type, bus, port_label, macaddr, module_id=module_seq)


def iface_info(
    iface_name: str,
    if_type: str,
    bus: str,
    port_label: str,
    macaddr: str,
    vlan_id: typing.Optional[int] = None,
    slot_path: typing.Optional[str] = None,
    qmi_device: typing.Optional[str] = None,
    module_id: int = 0,  # `module_id` is useful only for Mox, fallback to 0 for other HW
):
    state = get_iface_state(iface_name)
    iface_speed = get_iface_speed(iface_name) if state == "up" else 0
    vendor = get_iface_vendor(iface_name)
    res = {
        "type": if_type, "bus": bus, "state": state,
        "slot": port_label, "module_id": module_id, 'macaddr': macaddr,
        "link_speed": iface_speed
    }

    if vlan_id is not None:
        res["vlan_id"] = vlan_id

    if slot_path is not None:
        res["slot_path"] = slot_path

    if qmi_device is not None:
        res["qmi_device"] = qmi_device

    if vendor is not None:
        res["vendor"] = vendor

    return res


def sort_by_natural_order(interfaces: typing.Dict[str, dict]) -> typing.Dict[str, dict]:
    """Sort dictionary by keys in natural order."""
    return dict(
        sorted(
            interfaces.items(),
            key=lambda x: [int(s) if s.isdigit() else s.lower() for s in re.split(r"(\d+)", x[0])]
        )
    )


def wifi_strip_prefix(s: str) -> str:
    # Use re.search instead of re.match, because we can get various path prefixes ('/', '/tmp/pytest-of-user', ...),
    # based on environment (test vs on router).
    # Thus we are not always searching from the beginning of the string.
    res = WIFI_PATH_REGEX.search(s)
    if not res:
        return s  # when in doubt, return the original string and let the consumer handle it

    return res.group(1)


def qmi_filter_slot_path(s: str) -> str:
    # uci setting for device might be:
    #   `network.gsm.device='/sys/devices/platform/soc/soc:internal-regs/f1058000.usb/usb1/1-1'`
    # We need this as identificator to link physical device to the uci interface
    # yet we don't necessarily need to share whole path, which is:
    #    `/sys/devices/platform/soc/soc:internal-regs/f1058000.usb/usb1/1-1/1-1:1.4/net/wwan0`
    # and we also might want to strip prefix in testing environment.
    if res := QMI_PATH_REGEX.search(s):
        return res.group(0)
    else:
        return s
