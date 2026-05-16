#!/usr/bin/env python3

"""
DTMF control helper for SvxLink-Dash-V3.

Writes DTMF command strings to the configured SvxLink control PTY.
"""

from pathlib import Path
import re


DTMF_CONTROL_PATH = Path("/var/run/svxlink/dtmf_svx")


def validate_dtmf(command):
    """
    Allow only digits, star and hash.
    """

    return bool(re.fullmatch(r"[0-9*#]+", command))


def send_dtmf(command):
    """
    Send a DTMF command to SvxLink control PTY.
    """

    if not validate_dtmf(command):
        raise ValueError("Invalid DTMF command.")

    if not DTMF_CONTROL_PATH.exists():
        raise FileNotFoundError(
            f"DTMF control path not found: {DTMF_CONTROL_PATH}"
        )

    with DTMF_CONTROL_PATH.open("w", encoding="utf-8") as handle:
        handle.write(command)

    return command