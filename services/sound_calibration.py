#!/usr/bin/env python3

import subprocess
from typing import Any, Dict, List


SVXLINK_SERVICE = "svxlink.service"


def run_cmd(cmd: List[str], timeout: int = 30) -> Dict[str, Any]:
    result = subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )

    return {
        "command": " ".join(cmd),
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }

def get_svxlink_service_state() -> Dict[str, Any]:
    return run_cmd(["/usr/bin/systemctl", "is-active", SVXLINK_SERVICE], timeout=10)


def stop_svxlink_for_calibration() -> Dict[str, Any]:
    return run_cmd(["sudo", "/usr/bin/systemctl", "stop", SVXLINK_SERVICE], timeout=20)


def restart_svxlink_after_calibration() -> Dict[str, Any]:
    return run_cmd(["sudo", "/usr/bin/systemctl", "restart", SVXLINK_SERVICE], timeout=30)

def run_devcal(
    config_file: str,
    section: str,
    mode: str,
    modfqs: str,
    caldev: str,
    maxdev: str,
    headroom: str,
    audiodev: str = "",
    flat: bool = False,
    wide: bool = False,
) -> Dict[str, Any]:
    config_file = (config_file or "/etc/svxlink/svxlink.conf").strip()
    section = (section or "").strip()
    mode = (mode or "").strip()

    if not section:
        raise ValueError("No SvxLink Tx/Rx section selected.")

    cmd = [
        "sudo",
        "/usr/bin/devcal",
        config_file,
        section,
    ]

    if mode == "txcal":
        cmd.append("--txcal")
    elif mode == "rxcal":
        cmd.append("--rxcal")
    elif mode == "measure":
        cmd.append("--measure")
    else:
        raise ValueError("Invalid devcal mode selected.")

    if modfqs:
        cmd.extend(["--modfqs", str(modfqs)])

    if caldev:
        cmd.extend(["--caldev", str(caldev)])

    if maxdev:
        cmd.extend(["--maxdev", str(maxdev)])

    if headroom:
        cmd.extend(["--headroom", str(headroom)])

    if audiodev:
        cmd.extend(["--audiodev", audiodev])

    if flat:
        cmd.append("--flat")

    if wide:
        cmd.append("--wide")

    return run_cmd(cmd, timeout=180)
