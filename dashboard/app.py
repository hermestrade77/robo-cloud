from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# =========================================
# GLOBAL MEMORY
# =========================================

shared_data = {

    "signal": "WAIT",

    "confidence": 0,

    "market": "NONE",

    "price": 0,

    "atr": 0,

    "spread": 0,

    "news": "NONE",

    "session": "NONE",

    "analysis": "WAITING DATA",

    "reason": "WAITING IA",

    "buy_score": 0,

    "sell_score": 0,

    "winrate": 0,

    "trades": 0,

    "pnl": 0,

    "timestamp": "NONE"
}

# =========================================
# HOME
# =========================================

@app.route("/")

def home():

    signal_color = {

        "BUY": "#00ff99",

        "SELL": "#ff4444",

        "WAIT": "#ffaa00"

    }.get(

        shared_data["signal"],

        "white"
    )

    return f"""

    <html>

    <head>

        <meta http-equiv="refresh" content="2">

        <title>ROBO IA XAU/USD</title>

    </head>

    <body style="background:#0b0f1a;color:white;font-family:Arial;padding:30px">

        <h1>🔥 ROBO IA XAU/USD</h1>

        <hr>

        <h2>💰 PRICE: {shared_data["price"]}</h2>

        <h2>📊 MARKET: {shared_data["market"]}</h2>

        <h2>📉 ATR: {shared_data["atr"]}</h2>

        <h2>📡 SPREAD: {shared_data["spread"]}</h2>

        <h2>📰 NEWS: {shared_data["news"]}</h2>

        <h2>⏰ SESSION: {shared_data["session"]}</h2>

        <hr>

        <h1 style="color:{signal_color}">

            {shared_data["signal"]}

        </h1>

        <h2>

            🎯 CONFIDENCE:
            {shared_data["confidence"]}%

        </h2>

        <h2>

            🚀 BUY SCORE:
            {shared_data["buy_score"]}

        </h2>

        <h2>

            🔻 SELL SCORE:
            {shared_data["sell_score"]}

        </h2>

        <hr>

        <h2>🧠 ENTRY REASON</h2>

        <pre>

{shared_data["reason"]}

        </pre>

        <hr>

        <h2>🤖 AI ANALYSIS</h2>

        <pre>

{shared_data["analysis"]}

        </pre>

        <hr>

        <h2>📈 PERFORMANCE</h2>

        <h3>WINRATE: {shared_data["winrate"]}%</h3>

        <h3>TRADES: {shared_data["trades"]}</h3>

        <h3>PNL: {shared_data["pnl"]}</h3>

        <hr>

        <h3>🔄 LAST UPDATE</h3>

        <p>{shared_data["timestamp"]}</p>

    </body>

    </html>
    """

# =========================================
# UPDATE API
# =========================================

@app.route("/update", methods=["POST"])

def update():

    global shared_data

    try:

        data = request.json

        print("\n================================")
        print("📨 DADOS RECEBIDOS")
        print(data)

        shared_data.update(data)

        shared_data["timestamp"] = str(
            datetime.now()
        )

        return jsonify({

            "status": "success",

            "data": shared_data
        })

    except Exception as e:

        return jsonify({

            "status": "error",

            "message": str(e)
        })

# =========================================
# API
# =========================================

@app.route("/api")

def api():

    return jsonify(shared_data)

# =========================================
# START
# =========================================

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=8080
    )