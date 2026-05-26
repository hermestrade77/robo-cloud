from flask import (
    Flask,
    jsonify,
    render_template
)

from core.shared_data import (
    shared_data
)

app = Flask(__name__)

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
# API
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

        port=8080,

        debug=True
    )