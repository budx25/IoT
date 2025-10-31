import os, csv, threading, argparse
from datetime import datetime
from flask import Flask, request, jsonify, render_template
import joblib
import numpy as np
import pandas as pd
from collections import deque
import math

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(APP_ROOT, "logs.csv")

app = Flask(__name__, template_folder="templates", static_folder="static")

WINDOW_SIZE = 15
device_windows = {} 

log_lock = threading.Lock()

if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp","device","ldr","angle","source"])

model_bundle = None
model = None
feature_cols = None

def append_log(device, ldr, angle, source="auto_ml"):
    ts = datetime.utcnow().isoformat()
    with log_lock:
        with open(LOG_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([ts, device, int(ldr), int(angle), source])

def compute_features(device, ldr):
    """Compute streaming features similar to preprocessing."""
    if device not in device_windows:
        device_windows[device] = deque(maxlen=WINDOW_SIZE)
    dq = device_windows[device]
    dq.append(float(ldr))
    arr = np.array(dq)
    try:
        ma3 = float(pd.Series(arr).rolling(3, min_periods=1).mean().iloc[-1])
        ma5 = float(pd.Series(arr).rolling(5, min_periods=1).mean().iloc[-1])
        ma15 = float(pd.Series(arr).rolling(15, min_periods=1).mean().iloc[-1])
    except Exception:
        ma3 = ma5 = ma15 = float(ldr)
    delta1 = float(ldr - (arr[-2] if len(arr) >= 2 else 0.0))
    seconds = datetime.utcnow().hour*3600 + datetime.utcnow().minute*60 + datetime.utcnow().second
    tod_sin = math.sin(2*math.pi*seconds/86400)
    tod_cos = math.cos(2*math.pi*seconds/86400)
    feat = {
        'ldr': float(ldr),
        'ldr_ma3': ma3,
        'ldr_ma5': ma5,
        'ldr_ma15': ma15,
        'ldr_delta1': delta1,
        'tod_sin': tod_sin,
        'tod_cos': tod_cos
    }
    return feat

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/data")
def data():
    limit = int(request.args.get("limit", 500))
    rows = []
    if not os.path.exists(LOG_FILE):
        return jsonify({"timestamps":[], "ldr":[], "angle":[]})
    with log_lock:
        with open(LOG_FILE, "r") as f:
            reader = list(csv.DictReader(f))
            for r in reader[-limit:]:
                rows.append(r)
    timestamps = [r['timestamp'] for r in rows]
    ldrs = [int(r['ldr']) for r in rows]
    angles = [int(r['angle']) for r in rows]
    return jsonify({"timestamps": timestamps, "ldr": ldrs, "angle": angles})

@app.route("/inference", methods=["POST"])
def inference():
    """POST JSON: {"ldr": <int>, "device": "id", "source": "sim"}"""
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error":"invalid json, send Content-Type: application/json"}), 400

    ldr = float(data.get("ldr", 0))
    device = data.get("device", "sim")
    source = data.get("source", "simulator")

    feats = compute_features(device, ldr)

    if feature_cols and model is not None:
        X = np.array([[feats.get(c, 0.0) for c in feature_cols]])
        try:
            pred = model.predict(X)
            angle = int(max(0, min(180, round(float(pred[0])))))
            append_log(device, ldr, angle, source)
            return jsonify({"angle": angle})
        except Exception as e:
            fallback = int(max(0, min(180, round((4095 - ldr) * 180.0 / 4095.0))))
            append_log(device, ldr, fallback, "fallback")
            return jsonify({"angle": fallback, "error": str(e)}), 200
    else:
        fallback = int(max(0, min(180, round((4095 - ldr) * 180.0 / 4095.0))))
        append_log(device, ldr, fallback, "fallback")
        return jsonify({"angle": fallback})

@app.route("/clear_logs", methods=["POST"])
def clear_logs():
    with log_lock:
        with open(LOG_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp","device","ldr","angle","source"])
    return jsonify({"ok": True, "msg": "logs cleared"})

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="model_joblib.pkl")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()

    if os.path.exists(args.model):
        model_bundle = joblib.load(args.model)
        if isinstance(model_bundle, dict) and 'model' in model_bundle:
            model = model_bundle['model']
            feature_cols = model_bundle.get('features')
        else:
            model = model_bundle
            feature_cols = None
        print("Loaded model. feature_cols:", feature_cols)
    else:
        print("Model not found. Running with fallback mapping.")

    print(f"Starting Flask: http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=True)
