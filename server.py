#!/usr/bin/env python3
import sys, pathlib, shlex, subprocess, time, datetime as dt, threading, yaml
from flask import Flask, render_template, jsonify




app = Flask(__name__, template_folder="templates")

# -------------------------
# Konfiguration einlesen
# -------------------------
with open("config.yaml") as f:
    CONFIG = yaml.safe_load(f)

BASE_DIR = pathlib.Path(__file__).parent          # Verzeichnis von server.py
PYTHON   = sys.executable                         # Interpreter der aktiven venv


# Globale State-Variablen
active_jobs: list[threading.Timer] = []      # geplante Aktionen
end_timestamp_ms: int | None = None          # liefert API dem Frontend

# -------------------------
# Hilfsfunktionen
# -------------------------
def run(cmd: str | None):
    """
    Führt einen Befehl aus.
    • Wenn das erste Token eine *.py*-Datei ist, wird automatisch
      `sys.executable` davor­gesetzt → immer dasselbe venv.
    • cwd = BASE_DIR, damit relative Pfade stimmen.
    """
    if not cmd:
        return

    parts = shlex.split(cmd)
    exe   = parts[0]

    # .py-Dateien immer mit demselben Interpreter starten
    if exe.endswith(".py"):
        parts.insert(0, PYTHON)
        # absolute Pfadangabe, damit systemd es später auch findet
        parts[1] = str((BASE_DIR / exe).resolve())

    subprocess.Popen(parts, cwd=BASE_DIR)
    print("▶", " ".join(parts), flush=True)


def cancel_all():
    """Alle aktuell laufenden Timer abbrechen."""
    global active_jobs, end_timestamp_ms
    for job in active_jobs:
        job.cancel()
    active_jobs.clear()
    end_timestamp_ms = None

def schedule(mins: int):
    """Aktionen (grün → gelb → orange → rot → rot blinkend) planen."""
    global end_timestamp_ms, active_jobs
    cancel_all()

    # 1) sofort grün
    run(CONFIG["commands"]["start"])

    now = time.monotonic()
    plan = [
        (mins - 5, CONFIG["commands"].get("t_minus_5")),
        (mins - 1, CONFIG["commands"].get("t_minus_1")),
        (mins     , CONFIG["commands"].get("zero")),
        (mins + 1 , CONFIG["commands"].get("overdue")),
    ]

    for rel_min, cmd in plan:
        sec = rel_min * 60
        if sec < 0:
            # negative Werte nur für "overdue"
            continue
        job = threading.Timer(sec, run, args=(cmd,))
        job.daemon = True
        job.start()
        active_jobs.append(job)

    # Endzeit an Frontend schicken (ms seit 1970, damit JS damit rechnen kann)
    #end_timestamp_ms = int((dt.datetime.utcnow() + dt.timedelta(minutes=mins)).timestamp() * 1000)
    end_timestamp_ms = int((time.time() + mins * 60) * 1000)

# -------------------------
# HTTP-Routen
# -------------------------
@app.route("/")
def index():
    return render_template("index.html", timers=CONFIG["timers"])

@app.get("/start/<int:minutes>")
def start(minutes):
    schedule(minutes)
    return jsonify(end=end_timestamp_ms)

@app.get("/stop")
def stop():
    cancel_all()
    run(CONFIG["commands"]["stop"])
    return jsonify(status="stopped")

# -------------------------
if __name__ == "__main__":
    # Auf allen Interfaces (Touch-Browser ruft localhost auf)
    app.run(host="0.0.0.0", port=8000, debug=False)

