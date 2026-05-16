#!/usr/bin/env python3

"""
Reset SvxLink-Dash dashboard credentials.

Run locally on the device if dashboard login credentials are forgotten.
"""

import json
from pathlib import Path
from werkzeug.security import generate_password_hash


MODEL_FILE = Path("/opt/dashboard/config/node_model.json")


def main():
    if not MODEL_FILE.exists():
        raise FileNotFoundError(f"Model file not found: {MODEL_FILE}")

    model = json.loads(MODEL_FILE.read_text(encoding="utf-8"))

    username = input("New dashboard username: ").strip()
    password = input("New dashboard password: ").strip()

    if not username or not password:
        raise ValueError("Username and password are required.")

    model["dashboard_auth"] = {
        "username": username,
        "password_hash": generate_password_hash(password),
    }

    MODEL_FILE.write_text(
        json.dumps(model, indent=4),
        encoding="utf-8",
    )

    print("Dashboard credentials reset successfully.")


if __name__ == "__main__":
    main()