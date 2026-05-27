from flask import (
    Flask,
    render_template,
    request,
    jsonify
)

from datetime import datetime

app = Flask(__name__)

# ======================================
# MEMÓRIA GLOBAL
# ======================================

shared_data = {

    "signal": "WAIT",

    "confidence": 0,

    "market": "NONE",

    "price": 0,

    "atr": 0,

    "reason": "WAITING DATA",

    "analysis": "NONE",

    "news": "NONE",

    "session": "NONE",

    "winrate": 0,

    "trades": 0,

    "pnl": 0,

    "last_update": "NONE"
}

# ======================================
# HOME
# ======================================

@app.route("/")

def home():

    return f"""

    <html>

    <head>

        <meta http-equiv="refresh" content="2">

    </head>

    <body style="background:#0b0f1a;color:white;font-family:Arial;padding:30px">

        <h1>🔥 ROBO IA XAU/USD</h1>

        <hr>

        <h2>💰 PREÇO: {shared_data["price"]}</h2>

        <h1>📈 SIGNAL: {shared_data["signal"]}</h1>

        <h2>🎯 CONFIDENCE: {shared_data["confidence"]}</h2>

        <h2>📊 MARKET: {shared_data["market"]}</h2>

        <h2>📉 ATR: {shared_data["atr"]}</h2>

        <h2>📰 NEWS: {shared_data["news"]}</h2>

        <h2>⏰ SESSION: {shared_data["session"]}</h2>

        <h2>📈 WINRATE: {shared_data["winrate"]}%</h2>

        <h2>💵 PNL: {shared_data["pnl"]}</h2>

        <h2>📊 TRADES: {shared_data["trades"]}</h2>

        <hr>

        <h2>🧠 MOTIVO:</h2>

        <pre>{shared_data["reason"]}</pre>

        <hr>

        <h2>🤖 IA ANALISANDO:</h2>

        <pre>{shared_data["analysis"]}</pre>

        <hr>

        <h3>🔄 ÚLTIMA ATUALIZAÇÃO:</h3>

        <p>{shared_data["last_update"]}</p>

    </body>

    </html>
    """

# ======================================
# UPDATE API
# ======================================

@app.route("/update", methods=["POST"])

def update():

    global shared_data

    try:

        data = request.json

        print("\n====================")
        print("📨 DADOS RECEBIDOS")
        print(data)

        shared_data.update(data)

        shared_data["last_update"] = str(
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

# ======================================
# API
# ======================================

@app.route("/api")

def api():

    return jsonify(shared_data)

# ======================================
# START
# ======================================

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=8080
    )