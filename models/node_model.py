#!/usr/bin/env python3

"""
SvxLink-Dash-V3 node model.

This file defines the authoritative configuration model used by:
- Flask setup pages
- validation logic
- svxlink.conf renderers
- future dashboard editing
"""

from copy import deepcopy
from email import errors


SUPPORTED_NODE_TYPES = {"simplex", "repeater"}

SUPPORTED_IDENT_MODES = {
    "none",
    "cw",
    "voice",
    "both",
}

SUPPORTED_ROGER_MODES = {
    "none",
    "beep",
    "morse_t",
    "morse_k",
}

SUPPORTED_SQUELCH_METHODS = {
    "gpiod",
    "ctcss",
    "gpiod_ctcss",
}
SUPPORTED_INTERFACE_MODES = {
    "gpiod",
    "hidraw",
    "hybrid",
}
DEFAULT_MODEL = {
    "schema_version": 1,

    "platform": {
        "id": None,
        "name": None,
        "supported": False,
    },

    "node": {
        "type": None,
        "callsign": None,
        "language": "en_US",
    },
    "interface": {
        "mode": None,
        "sql_source": None,
        "ptt_source": None,
    },
    "reflector": {
        "enabled": False,
        "name": None,
        "host": None,
        "port": None,
        "auth_key": None,
    },

    "ident": {
        "short": {
            "mode": "cw",
            "interval": 15,
        },
        "long": {
            "mode": "voice",
            "interval": 60,
        },
    },

    "roger": {
        "mode": "none",
    },

    "squelch": {
        "method": "gpiod",
        "ctcss_freq": None,
        "ctcss_tx": False,
    },

    "modules": {
        "enabled": [
            "ModuleHelp",
            "ModuleParrot",
        ],
    },
}



def new_node_model(platform=None):
    """
    Return a fresh node model.

    platform may be a dict from the platform detection layer.
    """

    model = deepcopy(DEFAULT_MODEL)

    if platform is not None:
        model["platform"] = {
            "id": platform.get("id"),
            "name": platform.get("name"),
            "supported": bool(platform.get("supported")),
        }

    return model


def validate_model(model):
    """
    Validate high-level model consistency.

    Returns:
        list[str]: validation error messages.
    """

    errors = []

    node_type = model.get("node", {}).get("type")
    callsign = model.get("node", {}).get("callsign")

    if node_type not in SUPPORTED_NODE_TYPES:
        errors.append("Node type must be simplex or repeater.")

    if not callsign:
        errors.append("Callsign is required.")

    short_ident = model.get("ident", {}).get("short", {})
    long_ident = model.get("ident", {}).get("long", {})

    if short_ident.get("mode") not in SUPPORTED_IDENT_MODES:
        errors.append("Short ident mode is invalid.")

    if long_ident.get("mode") not in SUPPORTED_IDENT_MODES:
        errors.append("Long ident mode is invalid.")

    for ident_name, ident_data in (
        ("Short", short_ident),
        ("Long", long_ident),
    ):
        interval = ident_data.get("interval")

        if not isinstance(interval, int):
            errors.append(f"{ident_name} ident interval must be a number.")
        elif interval < 1:
            errors.append(f"{ident_name} ident interval must be at least 1 minute.")

    roger_mode = model.get("roger", {}).get("mode")

    if roger_mode not in SUPPORTED_ROGER_MODES:
        errors.append("Roger tone mode is invalid.")

    if node_type == "repeater" and roger_mode == "none":
        errors.append("Repeater mode requires a roger tone.")
        
    interface_mode = model.get("interface", {}).get("mode")

    if interface_mode not in SUPPORTED_INTERFACE_MODES:
        errors.append("Interface mode is invalid.")
        
    squelch_method = model.get("squelch", {}).get("method")

    if squelch_method not in SUPPORTED_SQUELCH_METHODS:
        errors.append("Squelch method is invalid.")

    reflector = model.get("reflector", {})

    if reflector.get("enabled"):
        if not reflector.get("host"):
            errors.append("Reflector host is required.")
        if not reflector.get("port"):
            errors.append("Reflector port is required.")
        if not reflector.get("auth_key"):
            errors.append("Reflector authentication key is required.")
        elif len(str(reflector.get("auth_key"))) != 16:
            errors.append("Reflector authentication key must be 16 characters.")

    return errors


def set_node_identity(model, node_type, callsign):
    """
    Set basic node identity.
    """

    model["node"]["type"] = node_type
    model["node"]["callsign"] = callsign.strip().upper()
    return model


def set_ident(model, short_mode, short_interval, long_mode, long_interval):
    """
    Set short and long identification behaviour.
    """

    model["ident"]["short"]["mode"] = short_mode
    model["ident"]["short"]["interval"] = int(short_interval)

    model["ident"]["long"]["mode"] = long_mode
    model["ident"]["long"]["interval"] = int(long_interval)

    return model


def set_roger(model, roger_mode):
    """
    Set roger tone mode.

    Repeater enforcement is validated separately.
    """

    model["roger"]["mode"] = roger_mode
    return model

def set_interface_mode(model, mode):
    """
    Set physical SQL/PTT control interface.

    gpiod:
        SQL = GPIOD
        PTT = GPIOD

    hidraw:
        SQL = HIDRAW
        PTT = HIDRAW

    hybrid:
        SQL = GPIOD
        PTT = HIDRAW
    """

    if mode == "gpiod":
        model["interface"] = {
            "mode": "gpiod",
            "sql_source": "gpiod",
            "ptt_source": "gpiod",
        }

    elif mode == "hidraw":
        model["interface"] = {
            "mode": "hidraw",
            "sql_source": "hidraw",
            "ptt_source": "hidraw",
        }

    elif mode == "hybrid":
        model["interface"] = {
            "mode": "hybrid",
            "sql_source": "gpiod",
            "ptt_source": "hidraw",
        }

    else:
        raise ValueError(f"Unsupported interface mode: {mode}")

    return model

def set_squelch(model, method, ctcss_freq=None, ctcss_tx=False):
    """
    Set squelch configuration.
    """

    model["squelch"]["method"] = method
    model["squelch"]["ctcss_freq"] = ctcss_freq
    model["squelch"]["ctcss_tx"] = bool(ctcss_tx)

    return model


def enable_reflector(model, name, host, port, auth_key):
    """
    Enable reflector configuration.
    """

    model["reflector"] = {
        "enabled": True,
        "name": name,
        "host": host,
        "port": int(port),
        "auth_key": auth_key,
    }

    return model


def disable_reflector(model):
    """
    Disable reflector configuration.
    """

    model["reflector"] = {
        "enabled": False,
        "name": None,
        "host": None,
        "port": None,
        "auth_key": None,
    }

    return model


def enable_module(model, module_name):
    """
    Enable a SvxLink module by name.
    """

    modules = model["modules"]["enabled"]

    if module_name not in modules:
        modules.append(module_name)

    return model


def disable_module(model, module_name):
    """
    Disable a SvxLink module by name.
    """

    modules = model["modules"]["enabled"]

    if module_name in modules:
        modules.remove(module_name)

    return model