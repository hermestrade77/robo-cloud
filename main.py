from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

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

@app.route("/")
def home():
    sinal = dados_compartilhados["signal"]
    cor_sinal = {"COMPRA": "#00ff99", "VENDA": "#ff4444", "WAIT": "#ffaa00"}.get(sinal, "white")
    return f"""
    <!DOCTYPE html>
    <html lang="pt">
    <head>
        <meta charset="UTF-8">
        <meta http-equiv="refresh" content="2">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ROBO IA XAU/USD</title>
        <style>
            body {{ background:#0b0f1a; color:#e0e0e0; font-family:'Segoe UI',sans-serif; margin:20px; }}
            h1 {{ color:#ffaa00; }}
            .grid {{ display:flex; gap:20px; flex-wrap:wrap; }}
            .card {{ background:#131a2b; border-radius:12px; padding:15px; margin-bottom:20px; flex:1; min-width:280px; }}
            .sinal {{ font-size:2.5rem; font-weight:bold; text-align:center; padding:10px; }}
            pre {{ background:#0a0f1a; padding:10px; border-radius:8px; white-space:pre-wrap; }}
        </style>
    </head>
    <body>
        <h1>🔥 ROBO IA XAU/USD</h1>
        <div class="grid">
            <div class="card">
                <h2>📊 Gráfico ao vivo</h2>
                <div class="tradingview-widget-container">
                    <div id="tradingview_chart"></div>
                    <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
                    <script type="text/javascript">
                        new TradingView.widget({{
                            "width": "100%",
                            "height": 400,
                            "symbol": "OANDA:XAUUSD",
                            "interval": "15",
                            "timezone": "Etc/UTC",
                            "theme": "dark",
                            "style": "1",
                            "locale": "br",
                            "toolbar_bg": "#f1f3f6",
                            "enable_publishing": false,
                            "allow_symbol_change": true,
                            "container_id": "tradingview_chart"
                        }});
                    </script>
                </div>
            </div>
            <div class="card">
                <h2>🧠 Sinal da IA</h2>
                <div class="sinal" style="color:{cor_sinal}">{sinal}</div>
                <p>🎯 Confiança: {dados_compartilhados['confidence']}%</p>
                <p>💰 Preço: {dados_compartilhados['price']}</p>
                <p>📊 Market: {dados_compartilhados['market']}</p>
                <p>📉 ATR: {dados_compartilhados['atr']}</p>
                <p>📡 Spread: {dados_compartilhados['spread']}</p>
                <p>📰 Notícia: {dados_compartilhados['news']}</p>
                <p>⏰ Sessão: {dados_compartilhados['session']}</p>
                <hr>
                <h3>🧠 Motivo</h3>
                <pre>{dados_compartilhados['reason']}</pre>
                <h3>📈 Performance</h3>
                <p>Winrate: {dados_compartilhados['winrate']}% | Trades: {dados_compartilhados['trades']}</p>
                <p>PnL: {dados_compartilhados['pnl']}</p>
                <p>🔄 Atualizado: {dados_compartilhados['timestamp']}</p>
            </div>
        </div>
        <div class="card">
            <h2>🤖 Análise da IA (com SHAP)</h2>
            <pre>{dados_compartilhados['analysis']}</pre>
        </div>
    </body>
    </html>
    """

@app.route("/data")
def data():
    return jsonify(dados_compartilhados)

@app.route("/update", methods=["POST"])
def update():
    global dados_compartilhados
    try:
        dados = request.json
        print(f"\n📨 DADOS RECEBIDOS EM {datetime.now().strftime('%H:%M:%S')}")
        print(dados)
        dados_compartilhados.update(dados)
        dados_compartilhados["timestamp"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        return jsonify({"status": "success", "data": dados_compartilhados})
    except Exception as e:
        print(f"❌ ERRO NO /update: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)