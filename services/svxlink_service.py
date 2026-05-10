#!/usr/bin/env python3

"""
SvxLink service and file deployment helpers for SvxLink-Dash-V3.

This module owns:
- svxlink service status
- svxlink service restart
- volatile config backups
- safe file writes

It does NOT generate svxlink.conf.
Rendering belongs in /renderers.
"""

from pathlib import Path
from datetime import datetime
import shutil
import subprocess


# =========================================================
# Paths
# =========================================================

APP_ROOT = Path("/opt/dashboard")

SVXLINK_CONF = Path("/etc/svxlink/svxlink.conf")
MODULE_DIR = Path("/etc/svxlink/svxlink.d")

LOGIC_DIR_SRC = Path("/usr/share/svxlink/events.d")
LOGIC_DIR_DST = Path("/usr/share/svxlink/events.d/local")

BACKUP_DIR = APP_ROOT / "backups"


# =========================================================
# Service control
# =========================================================

def svxlink_status():
    """
    Return systemd active state for svxlink.

    Typical results:
    - active
    - inactive
    - failed
    - unknown
    """

    result = subprocess.run(
        ["systemctl", "is-active", "svxlink"],
        text=True,
        capture_output=True,
    )

    status = result.stdout.strip()

    if not status:
        return "unknown"

    return status


def restart_svxlink():
    """
    Restart SvxLink using sudoers.d permission.

    The dashboard is expected to run as user svxlink.
    """

    subprocess.run(
        ["sudo", "systemctl", "restart", "svxlink"],
        check=True,
    )


# =========================================================
# Backup helpers
# =========================================================

def timestamp():
    """
    Return filesystem-safe timestamp.
    """

    return datetime.now().strftime("%Y%m%d-%H%M%S")


def ensure_backup_dir():
    """
    Ensure backup directory exists.
    """

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def backup_file(path):
    """
    Back up a single file if it exists.

    Returns:
        Path | None
    """

    path = Path(path)

    if not path.exists() or not path.is_file():
        return None

    ensure_backup_dir()

    backup_name = f"{path.name}.{timestamp()}.bak"
    backup_path = BACKUP_DIR / backup_name

    shutil.copy2(path, backup_path)

    return backup_path


def backup_active_config():
    """
    Back up volatile active SvxLink config files.

    Backed up:
    - /etc/svxlink/svxlink.conf
    - /etc/svxlink/svxlink.d/*.conf

    Not backed up:
    - /usr/share/svxlink/events.d/local/*
      because this is V3-managed generated output.
    """

    backups = []

    svxlink_backup = backup_file(SVXLINK_CONF)
    if svxlink_backup:
        backups.append(svxlink_backup)

    if MODULE_DIR.exists():
        for conf_file in sorted(MODULE_DIR.glob("*.conf")):
            backup = backup_file(conf_file)
            if backup:
                backups.append(backup)

    return backups


# =========================================================
# Safe write helpers
# =========================================================

def write_text_file(path, content):
    """
    Write text content to a file.

    Parent directory is created if required.
    """

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(content, encoding="utf-8")


def copy_file(src, dst):
    """
    Copy a file, preserving metadata where possible.
    """

    src = Path(src)
    dst = Path(dst)

    if not src.exists():
        raise FileNotFoundError(f"Source file does not exist: {src}")

    dst.parent.mkdir(parents=True, exist_ok=True)

    shutil.copy2(src, dst)

    return dst


def deploy_logic_file(filename):
    """
    Copy a logic/event file from LOGIC_DIR_SRC to LOGIC_DIR_DST.

    This intentionally overwrites the destination every time.
    """

    src = LOGIC_DIR_SRC / filename
    dst = LOGIC_DIR_DST / filename

    return copy_file(src, dst)


def deploy_required_logic_files():
    """
    Deploy known local override logic files.

    These are managed outputs and are not backed up.
    """

    deployed = []

    for filename in (
        "Logic.tcl",
        "RepeaterLogicType.tcl",
    ):
        deployed.append(deploy_logic_file(filename))

    return deployed
