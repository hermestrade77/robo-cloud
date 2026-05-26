from flask import (
    Flask,
    render_template,
    request,
    jsonify
)

app = Flask(__name__)

# ====================================
# DADOS
# ====================================

shared_data = {

    "signal": "WAIT",

    "confidence": 0,

    "market": "NONE",

    "bos": "NONE",

    "choch": "NONE",

    "sweep": False,

    "session": "NONE",

    "winrate": 0,

    "trades": 0,

    "pnl": 0
}

# ====================================
# DASHBOARD
# ====================================

@app.route("/")

def home():

    return render_template(

        "index.html",

        signal=shared_data["signal"],

        confidence=round(
            shared_data["confidence"] * 100,
            2
        ),

        market=shared_data["market"],

        bos=shared_data["bos"],

        choch=shared_data["choch"],

        sweep=shared_data["sweep"],

        bias=shared_data["market"],

        session=shared_data["session"],

        news="ACTIVE",

        volatility="HIGH",

        winrate=shared_data["winrate"],

        pnl=shared_data["pnl"],

        trades=shared_data["trades"]
    )

# ====================================
# API UPDATE
# ====================================

@app.route("/update", methods=["POST"])

def update():

    global shared_data

    shared_data = request.json

    return jsonify({

        "status": "ok"
    })

# ====================================
# API DATA
# ====================================

@app.route("/api")

def api():

    return jsonify(shared_data)

# ====================================
# START
# ====================================

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=8080
    )