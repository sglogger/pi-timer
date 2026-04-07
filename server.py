#!/usr/bin/env python3
import sys, pathlib, shlex, subprocess, time, datetime as dt, threading, yaml
from flask import Flask, render_template, jsonify

# Bluetooth
import asyncio
from bleak import BleakScanner, BleakClient

SERVICE_UUID = "48593a1c-333e-469b-8664-d1303867d341"
CHARACTERISTIC_UUID = "9f3c7b34-8c34-4503-b91d-06900f917531"

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

# Globale State-Variablen
active_jobs = []
end_timestamp_ms = None

# --- Bluetooth Logik ---
class BluetoothManager(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.loop = asyncio.new_event_loop()
        self.device_name = "Nicht verbunden"
        self.client = None
        self.command_queue = asyncio.Queue()

    def run(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.main_loop())

    async def main_loop(self):
        while True:
            try:
                if not self.client or not self.client.is_connected:
                    self.device_name = "Suche..."
                    
                    def filter_handler(device, ad):
                        name = device.name or ""
                        has_uuid = SERVICE_UUID.lower() in [s.lower() for s in ad.service_uuids]
                        return "SWINOG" in name.upper() or has_uuid

                    device = await BleakScanner.find_device_by_filter(filter_handler, timeout=5.0)
                    
                    if device:
                        self.client = BleakClient(device)
                        await self.client.connect()
                        self.device_name = device.name or device.address
                        print(f"BT verbunden: {self.device_name}")
                    else:
                        await asyncio.sleep(5)
                        continue

                # Warte auf Befehle aus der Queue
                cmd = await self.command_queue.get()
                if self.client and self.client.is_connected:
                    await self.client.write_gatt_char(CHARACTERISTIC_UUID, cmd.encode(), response=True)
                    print(f"BT gesendet: {cmd}")
                
            except Exception as e:
                print(f"BT Fehler: {e}")
                self.device_name = "Fehler / Suche..."
                self.client = None
                await asyncio.sleep(2)

    def send_cmd(self, cmd):
        self.loop.call_soon_threadsafe(self.command_queue.put_nowait, cmd)

# Manager starten
bt_manager = BluetoothManager()
bt_manager.start()

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

    # NEU: Sende via Bluetooth (Sekunden)
    bt_manager.send_cmd(f"START:{mins * 60}")
    
    # 1) sofort grün
    run(CONFIG["commands"]["start"])


    now = time.monotonic()
    plan = [
        (mins - 5, CONFIG["commands"].get("t_minus_5")),
        (mins - 1, CONFIG["commands"].get("t_minus_1")),
        (mins     , CONFIG["commands"].get("zero")),
        (mins + 0.5 , CONFIG["commands"].get("overdue")),
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
    cancel_all()
    schedule(minutes)
    return jsonify(end=end_timestamp_ms)

@app.get("/stop")
def stop():
    cancel_all()
    run(CONFIG["commands"]["stop"])
    bt_manager.send_cmd("STOP") # NEU: BT Stop
    return jsonify(status="stopped")

@app.get("/bt_status")
def bt_status():
    return jsonify(connected_with=bt_manager.device_name)

# -------------------------
if __name__ == "__main__":
    # Auf allen Interfaces (Touch-Browser ruft localhost auf)
    app.run(host="0.0.0.0", port=8000, debug=False)

