import argparse, time, random, csv
import json as _json
import urllib.request
import urllib.error

try:
    import requests  
except Exception:
    class _Response:
        def __init__(self, status_code, content):
            self.status_code = status_code
            self._content = content

        def raise_for_status(self):
            if 400 <= self.status_code:
                raise Exception(f"HTTP {self.status_code}: {self._content.decode('utf-8', errors='replace')}")

        def json(self):
            return _json.loads(self._content.decode('utf-8'))

    class _RequestsFallback:
        @staticmethod
        def post(url, json=None, timeout=None, headers=None):
            data = None
            if json is not None:
                data = _json.dumps(json).encode('utf-8')
            hdrs = {'Content-Type': 'application/json'}
            if headers:
                hdrs.update(headers)
            req = urllib.request.Request(url, data=data, headers=hdrs, method='POST')
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    content = resp.read()
                    status = resp.getcode()
            except urllib.error.HTTPError as e:
                try:
                    content = e.read()
                except Exception:
                    content = b''
                status = getattr(e, 'code', 500)
            return _Response(status, content)

    requests = _RequestsFallback()
from datetime import datetime
import pandas as pd

def send(server, ldr, device="sim", source="simulator"):
    payload = {"ldr": int(ldr), "device": device, "source": source}
    try:
        r = requests.post(server, json=payload, timeout=5)
        r.raise_for_status()
        j = r.json()
        angle = j.get("angle")
        return True, angle, j
    except Exception as e:
        return False, None, {"error": str(e)}

def random_stream(server, interval, count=None):
    i = 0
    while True:
        ldr = random.randint(0, 4095)
        ok, angle, resp = send(server, ldr)
        print(f"{datetime.utcnow().isoformat()} LDR={ldr} -> angle={angle} ok={ok}")
        i += 1
        if count and i >= count:
            break
        time.sleep(interval)

def csv_replay(server, csvfile, interval, loop):
    df = pd.read_csv(csvfile)
    col = None
    for c in ('ldr','ldr_value','value'):
        if c in df.columns:
            col = c; break
    if col is None:
        for c in df.columns:
            if pd.api.types.is_numeric_dtype(df[c]):
                col = c; break
    if col is None:
        raise SystemExit("No numeric column for LDR found in CSV")
    idx = 0
    n = len(df)
    while True:
        ldr = int(df.iloc[idx][col])
        ok, angle, resp = send(server, ldr)
        print(f"{datetime.utcnow().isoformat()} LDR={ldr} -> angle={angle} ok={ok}")
        idx += 1
        if idx >= n:
            if loop:
                idx = 0
            else:
                break
        time.sleep(interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", "-s", required=True, help="inference endpoint e.g. http://127.0.0.1:5000/inference")
    parser.add_argument("--interval", "-i", type=float, default=1.0)
    parser.add_argument("--mode", choices=("random","csv"), default="random")
    parser.add_argument("--csv", help="CSV file path for csv mode")
    parser.add_argument("--count", type=int, default=None)
    parser.add_argument("--loop", action="store_true")
    args = parser.parse_args()

    if args.mode == "random":
        random_stream(args.server, args.interval, count=args.count)
    else:
        if not args.csv:
            raise SystemExit("CSV mode requires --csv")
        csv_replay(args.server, args.csv, args.interval, args.loop)
