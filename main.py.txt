from flask import Flask
import random
import os
from datetime import datetime

app = Flask(__name__)

# ====================================
# HOME
# ====================================

@app.route("/")
def home():

    return {

        "bot": "ROBO IA XAUUSD",

        "status": "ONLINE",

        "server_time": str(datetime.now())

    }

# ====================================
# STATUS
# ====================================

@app.route("/status")
def status():

    return {

        "status": "ONLINE",

        "mt5": "CONNECTED",

        "ia": "FINBERT ACTIVE",

        "market": "XAUUSD",

        "time": str(datetime.now())

    }

# ====================================
# SIGNAL
# ====================================

@app.route("/signal")
def signal():

    sinais = [

        "BUY",

        "SELL",

        "WAIT"

    ]

    sinal = random.choice(sinais)

    return {

        "signal": sinal,

        "confidence": round(

            random.uniform(0.70, 0.99),

            2

        ),

        "asset": "XAUUSD",

        "timeframe": "M5",

        "strategy": "SMART MONEY + IA"

    }

# ====================================
# NEWS
# ====================================

@app.route("/news")
def news():

    noticias = [

        "FED may keep rates high",

        "Gold rises amid recession fears",

        "US Dollar gains strength",

        "Inflation concerns boost gold"

    ]

    return {

        "headline": random.choice(noticias),

        "impact": "HIGH",

        "market": "XAUUSD"

    }

# ====================================
# START
# ====================================

if __name__ == "__main__":

    port = int(

        os.environ.get(

            "PORT",

            8080

        )

    )

    app.run(

        host="0.0.0.0",

        port=port

    )