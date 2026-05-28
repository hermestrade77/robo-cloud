from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# =====================================
# MEMÓRIA GLOBAL (valores iniciais)
# =====================================
shared_data = {
    "signal": "WAIT",
    "confidence": 0,
    "market": "NONE",
    "price": 0,
    "atr": 0,
    "spread": 0,
    "news": "NONE",
    "session": "NONE",
    "analysis": "AGUARDANDO DADOS...",
    "reason": "AGUARDANDO IA...",
    "buy_score": 0,
    "sell_score": 0,
    "winrate": 0,
    "trades": 0,
    "pnl": 0,
    "timestamp": "NONE"
}

# =====================================
# HOME - Dashboard com refresh automático
# =====================================
@app.route("/")
def home():
    signal_color = {
        "BUY": "#00ff99",
        "SELL": "#ff4444",
        "WAIT": "#ffaa00"
    }.get(shared_data["signal"], "white")

    # Formata o ATR para duas casas decimais (evita mostrar o np.float64 cru)
    atr_str = f"{shared_data['atr']:.2f}" if isinstance(shared_data['atr'], (int, float)) else shared_data['atr']
    price_str = shared_data['price']
    spread_str = shared_data['spread']

    return f"""
    <!DOCTYPE html>
    <html lang="pt">
    <head>
        <meta charset="UTF-8">
        <meta http-equiv="refresh" content="2">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ROBO IA XAU/USD</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                background: #0b0f1a;
                color: #e0e0e0;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                padding: 20px;
                max-width: 700px;
                margin: auto;
            }}
            h1 {{
                text-align: center;
                color: #ffaa00;
                margin-bottom: 20px;
                font-size: 2rem;
            }}
            .card {{
                background: #131a2b;
                border-radius: 12px;
                padding: 15px 20px;
                margin-bottom: 15px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.4);
            }}
            .signal {{
                font-size: 3rem;
                font-weight: bold;
                text-align: center;
                padding: 10px;
            }}
            .row {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin: 8px 0;
                font-size: 1.1rem;
            }}
            .label {{ color: #aaa; }}
            .value {{ font-weight: bold; }}
            pre {{
                background: #0a0f1a;
                padding: 10px;
                border-radius: 8px;
                white-space: pre-wrap;
                font-size: 0.95rem;
                margin-top: 10px;
            }}
            hr {{ border-color: #222; margin: 15px 0; }}
            .timestamp {{
                text-align: right;
                font-size: 0.8rem;
                color: #666;
                margin-top: 10px;
            }}
        </style>
    </head>
    <body>
        <h1>🔥 ROBO IA XAU/USD</h1>

        <div class="card">
            <div class="row">
                <span class="label">💰 PREÇO</span>
                <span class="value">{price_str}</span>
            </div>
            <div class="row">
                <span class="label">📊 MARKET</span>
                <span class="value">{shared_data["market"]}</span>
            </div>
            <div class="row">
                <span class="label">📉 ATR</span>
                <span class="value">{atr_str}</span>
            </div>
            <div class="row">
                <span class="label">📡 SPREAD</span>
                <span class="value">{spread_str}</span>
            </div>
            <div class="row">
                <span class="label">📰 NEWS</span>
                <span class="value">{shared_data["news"]}</span>
            </div>
            <div class="row">
                <span class="label">⏰ SESSION</span>
                <span class="value">{shared_data["session"]}</span>
            </div>
        </div>

        <div class="card">
            <div class="signal" style="color:{signal_color}">{shared_data["signal"]}</div>
            <div class="row">
                <span class="label">🎯 CONFIDENCE</span>
                <span class="value">{shared_data["confidence"]}%</span>
            </div>
            <div class="row">
                <span class="label">🚀 BUY SCORE</span>
                <span class="value">{shared_data["buy_score"]}</span>
            </div>
            <div class="row">
                <span class="label">🔻 SELL SCORE</span>
                <span class="value">{shared_data["sell_score"]}</span>
            </div>
        </div>

        <div class="card">
            <h3>🧠 MOTIVO DA ENTRADA</h3>
            <pre>{shared_data["reason"]}</pre>
        </div>

        <div class="card">
            <h3>🤖 ANÁLISE DA IA</h3>
            <pre>{shared_data["analysis"]}</pre>
        </div>

        <div class="card">
            <h3>📈 PERFORMANCE</h3>
            <div class="row">
                <span class="label">WINRATE</span>
                <span class="value">{shared_data["winrate"]}%</span>
            </div>
            <div class="row">
                <span class="label">TRADES</span>
                <span class="value">{shared_data["trades"]}</span>
            </div>
            <div class="row">
                <span class="label">PNL</span>
                <span class="value">{shared_data["pnl"]}</span>
            </div>
        </div>

        <div class="timestamp">🔄 Última atualização: {shared_data["timestamp"]}</div>
    </body>
    </html>
    """

# =====================================
# API para polling (caso necessário)
# =====================================
@app.route("/data")
def data():
    return jsonify(shared_data)

# =====================================
# Rota extra para evitar 404
# =====================================
@app.route("/api/analysis")
def api_analysis():
    return jsonify(shared_data)

# =====================================
# UPDATE - Recebe dados do robô
# =====================================
@app.route("/update", methods=["POST"])
def update():
    global shared_data
    try:
        data = request.json
        print(f"\n📨 DADOS RECEBIDOS EM {datetime.now().strftime('%H:%M:%S')}")
        print(data)

        shared_data.update(data)
        shared_data["timestamp"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        return jsonify({"status": "success", "data": shared_data})
    except Exception as e:
        print(f"❌ ERRO NO /update: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400

# =====================================
# START
# =====================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)