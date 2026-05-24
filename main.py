from flask import Flask
import random
import os
from datetime import datetime

app = Flask(__name__)

# =========================================
# DADOS FAKE IA
# =========================================

def gerar_sinal():

    sinais = [

        "BUY",

        "SELL",

        "WAIT"

    ]

    return random.choice(sinais)

def gerar_noticia():

    noticias = [

        "FED mantém juros altos",

        "Ouro sobe com medo de recessão",

        "Dólar ganha força global",

        "Mercado espera decisão do FOMC",

        "Inflação preocupa investidores"

    ]

    return random.choice(noticias)

# =========================================
# DASHBOARD HTML
# =========================================

@app.route("/")
def dashboard():

    sinal = gerar_sinal()

    noticia = gerar_noticia()

    score = round(

        random.uniform(0.70, 0.99),

        2

    )

    html = f"""

    <html>

    <head>

    <title>ROBO IA XAUUSD</title>

    <style>

    body {{

        background: #0f172a;

        color: white;

        font-family: Arial;

        padding: 30px;

    }}

    .card {{

        background: #1e293b;

        border-radius: 20px;

        padding: 20px;

        margin-bottom: 20px;

        box-shadow: 0 0 20px rgba(0,0,0,0.5);

    }}

    h1 {{

        color: gold;

    }}

    .buy {{

        color: #00ff99;

        font-size: 40px;

        font-weight: bold;

    }}

    .sell {{

        color: #ff4d4d;

        font-size: 40px;

        font-weight: bold;

    }}

    .wait {{

        color: orange;

        font-size: 40px;

        font-weight: bold;

    }}

    </style>

    </head>

    <body>

    <h1>🔥 ROBO IA XAUUSD</h1>

    <div class="card">

        <h2>STATUS</h2>

        <p>🟢 ONLINE</p>

        <p>🤖 FINBERT ACTIVE</p>

        <p>📡 CLOUD ACTIVE</p>

        <p>⏰ {datetime.now()}</p>

    </div>

    <div class="card">

        <h2>SINAL IA</h2>

    """

    if sinal == "BUY":

        html += f"<p class='buy'>{sinal}</p>"

    elif sinal == "SELL":

        html += f"<p class='sell'>{sinal}</p>"

    else:

        html += f"<p class='wait'>{sinal}</p>"

    html += f"""

        <p>🎯 SCORE IA: {score}</p>

        <p>📊 ESTRATÉGIA: SMART MONEY + IA</p>

    </div>

    <div class="card">

        <h2>NOTÍCIA FORTE</h2>

        <p>📰 {noticia}</p>

    </div>

    <div class="card">

        <h2>MERCADO</h2>

        <p>🥇 XAUUSD</p>

        <p>💵 DXY MONITORADO</p>

        <p>🥈 PRATA MONITORADA</p>

        <p>🏦 FLUXO INSTITUCIONAL</p>

    </div>

    </body>

    </html>

    """

    return html

# =========================================
# STATUS API
# =========================================

@app.route("/status")
def status():

    return {

        "status": "ONLINE",

        "ia": "FINBERT ACTIVE",

        "market": "XAUUSD",

        "time": str(datetime.now())

    }

# =========================================
# SIGNAL API
# =========================================

@app.route("/signal")
def signal():

    return {

        "signal": gerar_sinal(),

        "confidence": round(

            random.uniform(0.70, 0.99),

            2

        ),

        "strategy": "SMART MONEY + IA"

    }

# =========================================
# NEWS API
# =========================================

@app.route("/news")
def news():

    return {

        "headline": gerar_noticia(),

        "impact": "HIGH"

    }

# =========================================
# START
# =========================================

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