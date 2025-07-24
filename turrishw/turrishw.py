import logging
import typing

from . import mox, omnia, turris1x, utils

logger = logging.getLogger(__name__)


def get_model():
    MODEL_MAP = {
        "CZ.NIC Turris Mox Board": "MOX",
        "Turris Omnia": "OMNIA",
        "Turris": "TURRIS1X",  # model name on TOS 5.3.x and older
        "Turris 1.x": "TURRIS1X",  # new model name for Turris 1.x from DTS
        "Turris 1.0": "TURRIS1X",
        "Turris 1.1": "TURRIS1X",
        # we might get blue Turris exact version from u-boot, so keep the model mapping future-proof
    }

    model = utils.get_first_line(utils.inject_file_root("sys/firmware/devicetree/base/model"))
    model = model.rstrip("\x00")

    return MODEL_MAP.get(model, "")


def get_ifaces(filter_types: typing.Optional[list[str]] = None):
    MODEL_MAP = {"MOX": mox, "OMNIA": omnia, "TURRIS1X": turris1x}

    hw_model = get_model()
    model = MODEL_MAP.get(hw_model)

    if model is None:
        logger.warning("Unsupported model: %s", hw_model)
        return {}

    ifaces = model.get_interfaces()
    if filter_types is not None:
        ifaces = {if_name: if_data for if_name, if_data in ifaces.items() if if_data["type"] in filter_types}

    # Reading interfaces from /sys might return them in different order based on tool used.
    # See difference between order of items for `os.listdir()` vs `ls` in shell.
    #
    # It will be more useful for consumer of `turrishw` to get interfaces sorted in resulting dictionary
    # to avoid dealing with the possibly random order of interfaces.

    return utils.sort_by_natural_order(ifaces)
