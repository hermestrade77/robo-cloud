from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# =====================================
# MEMÓRIA GLOBAL
# =====================================
dados_compartilhados = {
    "signal": "WAIT",
    "confidence": 0,
    "market": "NENHUM",
    "price": 0,
    "atr": 0,
    "spread": 0,
    "news": "NENHUMA",
    "session": "NENHUMA",
    "analysis": "AGUARDANDO DADOS...",
    "reason": "AGUARDANDO IA...",
    "buy_score": 0,
    "sell_score": 0,
    "winrate": 0,
    "trades": 0,
    "pnl": 0,
    "timestamp": "NENHUM"
}

# =====================================
# PÁGINA INICIAL (dashboard)
# =====================================
@app.route("/")
def home():
    cor_sinal = {
        "COMPRA": "#00ff99",
        "VENDA": "#ff4444",
        "WAIT": "#ffaa00"
    }.get(dados_compartilhados["signal"], "white")

    atr_str = f"{dados_compartilhados['atr']:.2f}" if isinstance(dados_compartilhados['atr'], (int, float)) else dados_compartilhados['atr']
    preco_str = dados_compartilhados['price']
    spread_str = dados_compartilhados['spread']

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
            .sinal {{
                font-size: 3rem;
                font-weight: bold;
                text-align: center;
                padding: 10px;
            }}
            .linha {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin: 8px 0;
                font-size: 1.1rem;
            }}
            .rotulo {{ color: #aaa; }}
            .valor {{ font-weight: bold; }}
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
            <div class="linha">
                <span class="rotulo">💰 PREÇO</span>
                <span class="valor">{preco_str}</span>
            </div>
            <div class="linha">
                <span class="rotulo">📊 MERCADO</span>
                <span class="valor">{dados_compartilhados["market"]}</span>
            </div>
            <div class="linha">
                <span class="rotulo">📉 ATR</span>
                <span class="valor">{atr_str}</span>
            </div>
            <div class="linha">
                <span class="rotulo">📡 SPREAD</span>
                <span class="valor">{spread_str}</span>
            </div>
            <div class="linha">
                <span class="rotulo">📰 NOTÍCIAS</span>
                <span class="valor">{dados_compartilhados["news"]}</span>
            </div>
            <div class="linha">
                <span class="rotulo">⏰ SESSÃO</span>
                <span class="valor">{dados_compartilhados["session"]}</span>
            </div>
        </div>

        <div class="card">
            <div class="sinal" style="color:{cor_sinal}">{dados_compartilhados["signal"]}</div>
            <div class="linha">
                <span class="rotulo">🎯 CONFIANÇA</span>
                <span class="valor">{dados_compartilhados["confidence"]}%</span>
            </div>
            <div class="linha">
                <span class="rotulo">🚀 PONTOS COMPRA</span>
                <span class="valor">{dados_compartilhados["buy_score"]}</span>
            </div>
            <div class="linha">
                <span class="rotulo">🔻 PONTOS VENDA</span>
                <span class="valor">{dados_compartilhados["sell_score"]}</span>
            </div>
        </div>

        <div class="card">
            <h3>🧠 MOTIVO DA ENTRADA</h3>
            <pre>{dados_compartilhados["reason"]}</pre>
        </div>

        <div class="card">
            <h3>🤖 ANÁLISE DA IA</h3>
            <pre>{dados_compartilhados["analysis"]}</pre>
        </div>

        <div class="card">
            <h3>📈 PERFORMANCE</h3>
            <div class="linha">
                <span class="rotulo">WINRATE</span>
                <span class="valor">{dados_compartilhados["winrate"]}%</span>
            </div>
            <div class="linha">
                <span class="rotulo">TRADES</span>
                <span class="valor">{dados_compartilhados["trades"]}</span>
            </div>
            <div class="linha">
                <span class="rotulo">PNL</span>
                <span class="valor">{dados_compartilhados["pnl"]}</span>
            </div>
        </div>

        <div class="timestamp">🔄 Última atualização: {dados_compartilhados["timestamp"]}</div>
    </body>
    </html>
    """

# =====================================
# ROTAS DA API
# =====================================
@app.route("/data")
def dados():
    return jsonify(dados_compartilhados)

@app.route("/api/analysis")
def api_analise():
    return jsonify(dados_compartilhados)

@app.route("/update", methods=["POST"])
def atualizar():
    global dados_compartilhados
    try:
        dados = request.json
        print(f"\n📨 DADOS RECEBIDOS EM {datetime.now().strftime('%H:%M:%S')}")
        print(dados)

        dados_compartilhados.update(dados)
        dados_compartilhados["timestamp"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        return jsonify({"status": "sucesso", "data": dados_compartilhados})
    except Exception as e:
        print(f"❌ ERRO NO /update: {e}")
        return jsonify({"status": "erro", "message": str(e)}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)