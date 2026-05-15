#!/usr/bin/env python3

"""
Runtime monitoring helpers for SvxLink-Dash-V3.

Read-only status collection only.
No control functions belong here.
"""

from pathlib import Path
import subprocess
import time

from services.svxlink_service import svxlink_status

UPTIME_FILE = Path("/proc/uptime")


def get_system_uptime():
    """
    Return human-readable system uptime.
    """

    try:
        uptime_seconds = float(
            UPTIME_FILE.read_text().split()[0]
        )

    except Exception:
        return "unknown"

    days = int(uptime_seconds // 86400)
    hours = int((uptime_seconds % 86400) // 3600)
    minutes = int((uptime_seconds % 3600) // 60)

    parts = []

    if days:
        parts.append(f"{days}d")

    if hours:
        parts.append(f"{hours}h")

    parts.append(f"{minutes}m")

    return " ".join(parts)


def get_connected_reflector(model=None):
    """
    Determine reflector connection state.
    """

    log_file = Path("/var/log/svxlink.log")

    reflector_name = "Unknown"

    if model:
        reflector_name = (
            model.get("reflector", {})
            .get("name", "Unknown")
        )

    if not log_file.exists():
        return "unknown"

    try:
        lines = log_file.read_text(
            encoding="utf-8",
            errors="ignore"
        ).splitlines()

    except Exception:
        return "unknown"

    for line in reversed(lines[-500:]):

        lower = line.lower()

        if "reflectorlogic" not in lower:
            continue

        if (
            "disconnected" in lower
            or "connection failed" in lower
        ):
            return "not connected"

        if "authentication ok" in lower:
            return f"Connected ({reflector_name})"

    return "not connected"

def get_runtime_status(model):
    """
    Collect dashboard runtime information.
    """

    return {
        "callsign": model.get("node", {}).get(
            "callsign",
            "unknown"
        ),

        "node_type": model.get("node", {}).get(
            "type",
            "unknown"
        ),

        "service_status": svxlink_status(),

        "uptime": get_system_uptime(),

        "reflector": get_connected_reflector(model),

        "modules": model.get("modules", {}).get(
            "enabled",
            []
        ),
        "recent_log": get_recent_log_lines(),
    }
def get_recent_log_lines(limit=40):
    """
    Return recent SvxLink log lines for dashboard display.
    """

    log_file = Path("/var/log/svxlink.log")

    if not log_file.exists():
        return ["Log file not found: /var/log/svxlink.log"]

    try:
        lines = log_file.read_text(
            encoding="utf-8",
            errors="ignore"
        ).splitlines()

    except Exception as exc:
        return [f"Unable to read log file: {exc}"]

    return lines[-limit:]    