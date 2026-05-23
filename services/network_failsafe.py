#!/usr/bin/env python3

import subprocess


HOTSPOT_NAME = "Hotspot"


def nmcli(args):
    result = subprocess.run(
        ["sudo", "-n", "nmcli"] + args,
        text=True,
        capture_output=True,
    )

    return result.stdout.strip()


def is_wired_connected():
    output = nmcli(["-t", "-f", "DEVICE,TYPE,STATE", "device"])

    for line in output.splitlines():
        parts = line.split(":")
        if len(parts) >= 3:
            device, dev_type, state = parts[:3]
            if dev_type == "ethernet" and state == "connected":
                return True

    return False


def is_wifi_connected():
    output = nmcli(["-t", "-f", "DEVICE,TYPE,STATE", "device"])

    for line in output.splitlines():
        parts = line.split(":")
        if len(parts) >= 3:
            device, dev_type, state = parts[:3]
            if dev_type == "wifi" and state == "connected":
                return True

    return False


def hotspot_active():
    output = nmcli([
        "-t",
        "-f",
        "NAME,TYPE,DEVICE",
        "connection",
        "show",
        "--active",
    ])

    for line in output.splitlines():
        parts = line.split(":")
        if len(parts) >= 2:
            name, con_type = parts[:2]
            if name == HOTSPOT_NAME and con_type == "wifi":
                return True

    return False


def start_hotspot_if_needed():
    nmcli(["radio", "wifi", "on"])

    if is_wired_connected():
        return "wired connection active; hotspot not started"

    if is_wifi_connected():
        return "wifi connection active; hotspot not started"

    if hotspot_active():
        return "hotspot already active"

    subprocess.run(
        ["sudo", "-n", "nmcli", "connection", "up", HOTSPOT_NAME],
        text=True,
        capture_output=True,
        check=False,
    )

    return "hotspot start requested"


if __name__ == "__main__":
    print(start_hotspot_if_needed())