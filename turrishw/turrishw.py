import logging

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

    model = utils.get_first_line(utils.inject_file_root('sys/firmware/devicetree/base/model'))
    model = model.rstrip("\x00")

    return MODEL_MAP.get(model, "")


def get_ifaces():
    MODEL_MAP = {
        "MOX": mox,
        "OMNIA": omnia,
        "TURRIS1X": turris1x,
    }

    hw_model = get_model()
    model = MODEL_MAP.get(hw_model)

    if model is None:
        logger.warning("Unsupported model: %s", hw_model)
        return {}

    return utils.ifaces_array2dict(model.get_interfaces())
