# main.py
import os
import logging
from flask import Flask, request, jsonify, abort
from threading import Lock
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("robo-cloud")

app = Flask(__name__)
_state = {}
_state_lock = Lock()

def validate_update_payload(payload):
    # ajuste conforme o formato real que o robô envia
    required = ["symbol", "timestamp", "signal", "confidence", "model_version"]
    for k in required:
        if k not in payload:
            return False, f"missing {k}"
    return True, None

@app.route("/update", methods=["POST"])
def update():
    data = request.get_json(force=True, silent=True)
    if not data:
        logger.warning("Empty or invalid JSON in /update")
        abort(400, "invalid json")
    ok, err = validate_update_payload(data)
    if not ok:
        logger.warning("Invalid payload: %s", err)
        abort(400, err)
    # basic anti-spam / rate limiting could be added here
    with _state_lock:
        # store last update per symbol
        symbol = data["symbol"]
        _state[symbol] = {
            "last_update": datetime.utcnow().isoformat() + "Z",
            "payload": data
        }
    logger.info("State updated for %s", symbol)
    return jsonify({"status": "ok"}), 200

@app.route("/data", methods=["GET"])
@app.route("/api", methods=["GET"])
def get_data():
    with _state_lock:
        return jsonify(_state)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info("Starting dashboard on port %d", port)
    app.run(host="0.0.0.0", port=port)
