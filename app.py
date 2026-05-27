from flask import Flask, request, jsonify, render_template
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
# HOME - Dashboard principal
# =====================================
@app.route("/")
def home():
    return render_template("index.html")

# =====================================
# API para o frontend (polling)
# =====================================
@app.route("/data")
def data():
    return jsonify(shared_data)

# =====================================
# UPDATE - Recebe dados do robô
# =====================================
@app.route("/update", methods=["POST"])
def update():
    global shared_data
    try:
        data = request.json
        print("\n================================")
        print(f"📨 DADOS RECEBIDOS EM {datetime.now().strftime('%H:%M:%S')}")
        print(data)

        # Atualiza apenas as chaves enviadas
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