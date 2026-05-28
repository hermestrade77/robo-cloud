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
    "timestamp": "NENHUM",
    "gold_news": []   # lista de objetos {headline, time}
}

@app.route("/")
def home():
    return """
    <!DOCTYPE html>
    <html lang="pt">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ROBO IA XAU/USD</title>
        <style>
            body { background:#0b0f1a; color:#e0e0e0; font-family:'Segoe UI',sans-serif; margin:20px; }
            h1 { color:#ffaa00; }
            .grid { display:flex; gap:20px; flex-wrap:wrap; }
            .card { background:#131a2b; border-radius:12px; padding:15px; margin-bottom:20px; flex:1; min-width:280px; }
            .sinal { font-size:2.5rem; font-weight:bold; text-align:center; padding:10px; }
            pre { background:#0a0f1a; padding:10px; border-radius:8px; white-space:pre-wrap; }
            .buy { color:#00ff99; } .sell { color:#ff4444; } .wait { color:#ffaa00; }
            .news-item { background:#1a2235; margin:8px 0; padding:10px; border-radius:8px; font-size:0.9rem; }
            .news-time { color:#aaa; font-size:0.8rem; }
        </style>
    </head>
    <body>
        <h1>🔥 ROBO IA XAU/USD</h1>
        <div class="grid">
            <div class="card">
                <h2>📊 Gráfico ao vivo</h2>
                <div class="tradingview-widget-container">
                    <div id="tradingview_chart"></div>
                </div>
                <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
                <script type="text/javascript">
                    new TradingView.widget({
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
                    });
                </script>
            </div>
            <div class="card">
                <h2>🧠 Sinal da IA</h2>
                <div class="sinal" id="sinal">WAIT</div>
                <p>🎯 Confiança: <span id="confianca">0</span>%</p>
                <p>💰 Preço: <span id="preco">0</span></p>
                <p>📊 Market: <span id="market">NENHUM</span></p>
                <p>📉 ATR: <span id="atr">0</span></p>
                <p>📡 Spread: <span id="spread">0</span></p>
                <p>📰 Notícia: <span id="news">NENHUMA</span></p>
                <p>⏰ Sessão: <span id="session">NENHUMA</span></p>
                <hr>
                <h3>🧠 Motivo</h3>
                <pre id="reason">AGUARDANDO IA...</pre>
                <h3>📈 Performance</h3>
                <p>Winrate: <span id="winrate">0</span>% | Trades: <span id="trades">0</span></p>
                <p>PnL: <span id="pnl">0</span></p>
                <p>🔄 Atualizado: <span id="timestamp">NENHUM</span></p>
            </div>
        </div>
        <div class="card">
            <h2>📰 Últimas notícias do Ouro</h2>
            <div id="gold_news_container">
                <p>🔍 Buscando notícias...</p>
            </div>
        </div>
        <div class="card">
            <h2>🤖 Análise da IA (com SHAP)</h2>
            <pre id="analysis">AGUARDANDO DADOS...</pre>
        </div>

        <script>
            async function atualizarDados() {
                try {
                    const res = await fetch('/data');
                    if (!res.ok) throw new Error('Erro HTTP ' + res.status);
                    const data = await res.json();

                    // Atualiza campos básicos
                    document.getElementById('sinal').textContent = data.signal;
                    const sinalEl = document.getElementById('sinal');
                    sinalEl.className = 'sinal ' + (data.signal === 'COMPRA' ? 'buy' : data.signal === 'VENDA' ? 'sell' : 'wait');
                    document.getElementById('confianca').textContent = data.confidence;
                    document.getElementById('preco').textContent = data.price;
                    document.getElementById('market').textContent = data.market;
                    document.getElementById('atr').textContent = data.atr;
                    document.getElementById('spread').textContent = data.spread;
                    document.getElementById('news').textContent = data.news;
                    document.getElementById('session').textContent = data.session;
                    document.getElementById('reason').textContent = data.reason;
                    document.getElementById('winrate').textContent = data.winrate;
                    document.getElementById('trades').textContent = data.trades;
                    document.getElementById('pnl').textContent = data.pnl;
                    document.getElementById('timestamp').textContent = data.timestamp;
                    document.getElementById('analysis').textContent = data.analysis;

                    // Atualiza lista de notícias do ouro
                    const newsContainer = document.getElementById('gold_news_container');
                    if (data.gold_news && data.gold_news.length > 0) {
                        let html = '';
                        data.gold_news.forEach(item => {
                            html += `<div class="news-item">
                                <div>${item.headline}</div>
                                <div class="news-time">${item.time || ''}</div>
                            </div>`;
                        });
                        newsContainer.innerHTML = html;
                    } else {
                        newsContainer.innerHTML = '<p>Nenhuma notícia recente encontrada.</p>';
                    }

                } catch (err) {
                    console.error('Erro ao atualizar dados:', err);
                    // Mostra erro visualmente (opcional)
                    document.getElementById('timestamp').textContent = 'ERRO AO ATUALIZAR';
                }
            }

            setInterval(atualizarDados, 2000);
            atualizarDados();
        </script>
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