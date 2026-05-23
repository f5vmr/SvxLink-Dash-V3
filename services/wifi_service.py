#!/usr/bin/env python3

import subprocess


def run_nmcli(args):
    result = subprocess.run(
        ["sudo", "-n", "nmcli"] + args,
        text=True,
        capture_output=True,
    )

    output = []

    if result.stdout:
        output.extend(result.stdout.strip().splitlines())

    if result.stderr:
        output.extend(result.stderr.strip().splitlines())

    return output

def wifi_scan():
    run_nmcli(["dev", "wifi", "rescan"])
    return run_nmcli(["dev", "wifi", "list"])


def connection_list():
    return run_nmcli(["con", "show", "--order", "type"])


def wifi_status():
    return run_nmcli(["radio"])


def wifi_on():
    run_nmcli(["radio", "wifi", "on"])
    return run_nmcli(["radio", "wifi"])