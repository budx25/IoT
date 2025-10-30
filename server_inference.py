from flask import Flask, request, jsonify
import joblib
import numpy as np
import argparse

app = Flask(__name__)
model = None

@app.route("/inference", methods=["POST"])
def inference():
    data = request.get_json(force=True)
    ldr = float(data.get("ldr", 0))
    ldr_ma5 = ldr  # placeholder: bisa diganti moving avg realtime
    X = np.array([[ldr, ldr_ma5]])
    pred = model.predict(X)
    angle = int(max(0, min(180, round(pred[0]))))
    return jsonify({"angle": angle})

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="model_joblib.pkl")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()
    model = joblib.load(args.model)
    print("Model loaded. Starting server...")
    app.run(host=args.host, port=args.port)
