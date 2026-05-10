#!/usr/bin/env python3

from flask import Flask, render_template, request, redirect, url_for
from pathlib import Path
import subprocess
import platform


# =========================================================
# Core paths
# =========================================================

APP_ROOT = Path("/opt/dashboard")
TEMPLATE_DIR = APP_ROOT / "templates"
STATIC_DIR = APP_ROOT / "static"

CONFIG_DIR = APP_ROOT / "config"
MODEL_FILE = CONFIG_DIR / "node_model.json"

# =========================================================
# SvxLink paths
# =========================================================

SVXLINK_CONF = Path("/etc/svxlink/svxlink.conf")

MODULE_DIR = Path("/etc/svxlink/svxlink.d")

LOGIC_DIR_SRC = Path("/usr/share/svxlink/events.d")

LOGIC_DIR_DST = Path("/usr/share/svxlink/events.d/local")

# =========================================================
# Flask app
# =========================================================

app = Flask(
    __name__,
    template_folder=str(TEMPLATE_DIR),
    static_folder=str(STATIC_DIR),
    static_url_path="/static"
)


# =========================================================
# Platform detection
# =========================================================

def detect_platform():
    """
    Detect supported hardware profile.

    Initial supported targets:
    - raspberry_pi
    - nanopi_neo

    Anything else is unsupported unless later proven compatible.
    """

    model_text = ""

    try:
        model_text = Path("/proc/device-tree/model").read_text(errors="ignore").lower()
    except FileNotFoundError:
        pass

    if "raspberry pi" in model_text:
        return {
            "id": "raspberry_pi",
            "name": "Raspberry Pi",
            "supported": True,
        }

    if "nanopi neo" in model_text or "friendlyarm nanopi" in model_text:
        return {
            "id": "nanopi_neo",
            "name": "NanoPi-Neo",
            "supported": True,
        }

    return {
        "id": "unknown",
        "name": platform.machine(),
        "supported": False,
    }


# =========================================================
# Node model defaults
# =========================================================

def default_node_model():
    """
    This is the authoritative in-memory model.
    svxlink.conf should eventually be generated from this.
    """

    return {
        "platform": detect_platform(),
        "node_type": None,          # simplex | repeater
        "callsign": None,
        "language": "en_US",

        "reflector": {
            "enabled": False,
            "name": None,
            "host": None,
            "port": None,
            "auth_key": None,
        },

        "ident": {
            "short": {
                "mode": None,       # none | cw | voice | both
                "interval": 15,
            },
            "long": {
                "mode": None,       # none | cw | voice | both
                "interval": 60,
            },
        },

        "roger": {
            "mode": "none",         # none | beep | morse_t | morse_k
        },

        "squelch": {
            "method": None,         # gpiod | ctcss
            "ctcss_freq": None,
            "ctcss_tx": False,
        },

        "modules": [
            "ModuleHelp",
            "ModuleParrot",
        ],
    }


# =========================================================
# Model persistence
# =========================================================

def ensure_dirs():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def save_node_model(model):
    """
    Placeholder for JSON persistence.
    JSON support will be added when we formalise the model module.
    """
    ensure_dirs()

    import json
    MODEL_FILE.write_text(
        json.dumps(model, indent=4),
        encoding="utf-8"
    )


def load_node_model():
    import json

    if not MODEL_FILE.exists():
        model = default_node_model()
        save_node_model(model)
        return model

    return json.loads(MODEL_FILE.read_text(encoding="utf-8"))


# =========================================================
# SvxLink service wrapper
# =========================================================

def restart_svxlink():
    """
    Uses existing sudoers.d permission.

    Flask itself runs as svxlink.
    Only this controlled command uses sudo.
    """

    subprocess.run(
        ["sudo", "systemctl", "restart", "svxlink"],
        check=True
    )


def svxlink_status():
    result = subprocess.run(
        ["systemctl", "is-active", "svxlink"],
        text=True,
        capture_output=True
    )

    return result.stdout.strip()


# =========================================================
# Routes
# =========================================================

@app.route("/", methods=["GET"])
def index():
    return redirect(url_for("setup"))


@app.route("/setup", methods=["GET", "POST"])
def setup():
    error = None
    model = load_node_model()

    if request.method == "POST":
        callsign = request.form.get("callsign", "").strip().upper()
        node_type = request.form.get("node_type")

        if not callsign:
            error = "Please enter a callsign."
        elif node_type not in ("simplex", "repeater"):
            error = "Please select Simplex or Repeater."
        else:
            model["callsign"] = callsign
            model["node_type"] = node_type

            save_node_model(model)
            return redirect(url_for("ident"))

    return render_template(
        "setup.html",
        error=error,
        model=model,
    )


@app.route("/ident", methods=["GET", "POST"])
def ident():
    error = None
    model = load_node_model()

    if request.method == "POST":
        short_mode = request.form.get("short_ident_mode")
        long_mode = request.form.get("long_ident_mode")

        try:
            short_interval = int(request.form.get("short_ident_interval", "15"))
            long_interval = int(request.form.get("long_ident_interval", "60"))
        except ValueError:
            error = "Identification intervals must be numbers."
        else:
            valid_modes = {"none", "cw", "voice", "both"}

            if short_mode not in valid_modes:
                error = "Please select a valid short identification mode."
            elif long_mode not in valid_modes:
                error = "Please select a valid long identification mode."
            else:
                model["ident"]["short"]["mode"] = short_mode
                model["ident"]["short"]["interval"] = short_interval
                model["ident"]["long"]["mode"] = long_mode
                model["ident"]["long"]["interval"] = long_interval

                save_node_model(model)
                return redirect(url_for("roger"))

    return render_template(
        "ident.html",
        error=error,
        model=model,
    )


@app.route("/roger", methods=["GET", "POST"])
def roger():
    error = None
    model = load_node_model()

    if request.method == "POST":
        roger_mode = request.form.get("roger_mode")

        valid_modes = {"none", "beep", "morse_t", "morse_k"}

        if roger_mode not in valid_modes:
            error = "Please select a valid roger tone option."
        else:
            # Repeater policy: roger tone is mandatory.
            if model["node_type"] == "repeater" and roger_mode == "none":
                error = "Repeater mode requires a roger tone."
            else:
                model["roger"]["mode"] = roger_mode
                save_node_model(model)
                return redirect(url_for("connect"))

    return render_template(
        "roger.html",
        error=error,
        model=model,
    )


@app.route("/connect", methods=["GET", "POST"])
def connect():
    error = None
    model = load_node_model()

    reflectors = {
        "north_america": {
            "name": "North America Reflector",
            "host": "north.america.svxlink.net",
            "port": 35300,
            "url": "https://north.america.svxlink.net",
        },
        "ukwide": {
            "name": "UKWide Reflector",
            "host": "uk.wide.svxlink.uk",
            "port": 35300,
            "url": "https://ukwide.svxlink.net",
        },
        "australia_nz": {
            "name": "Australia / New Zealand Reflector",
            "host": "australia.svxlink.net",
            "port": 35300,
            "url": "https://au.svxlink.net",
        },
        "yorkshire": {
            "name": "YorkshireNet Reflector",
            "host": "yorkshire.svxlink.uk",
            "port": 5310,
            "url": "https://svxlink.qsos.uk/",
        },
    }

    if request.method == "POST":
        connect_answer = request.form.get("connect")
        reflector_id = request.form.get("reflector")
        password = request.form.get("password", "").strip()

        if connect_answer == "no":
            model["reflector"]["enabled"] = False
            save_node_model(model)
            return redirect(url_for("done"))

        if reflector_id not in reflectors:
            error = "Please select a reflector."
        elif not password:
            error = "Please enter the reflector subscription password."
        elif len(password) != 16:
            error = "Password must be exactly 16 characters long."
        else:
            selected = reflectors[reflector_id]

            model["reflector"] = {
                "enabled": True,
                "name": selected["name"],
                "host": selected["host"],
                "port": selected["port"],
                "auth_key": password,
            }

            save_node_model(model)
            return redirect(url_for("done"))

    return render_template(
        "connect.html",
        error=error,
        model=model,
        reflectors=reflectors,
    )


@app.route("/done", methods=["GET"])
def done():
    model = load_node_model()
    status = svxlink_status()

    return render_template(
        "done.html",
        model=model,
        svxlink_status=status,
    )


@app.route("/launch", methods=["POST"])
def launch():
    try:
        restart_svxlink()
    except subprocess.CalledProcessError as exc:
        return render_template(
            "done.html",
            model=load_node_model(),
            svxlink_status="restart failed",
            error=f"Failed to restart SvxLink: {exc}",
        )

    return redirect(url_for("done"))


# =========================================================
# Development entry point
# systemd may call this directly.
# =========================================================

if __name__ == "__main__":
    ensure_dirs()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
    )