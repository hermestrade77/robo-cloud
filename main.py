from flask import Flask, jsonify
from ai.model import treinar_modelo, prever
from datetime import datetime

app = Flask(__name__)

print("🧠 Treinando IA XGBoost...")
model, features = treinar_modelo()
print("✅ IA pronta!")

@app.route("/")
def home():

    result = prever(model, features)

    return f"""
    <html>
    <head>
        <title>XGBOOST TRADING AI</title>
        <meta http-equiv="refresh" content="10">
        <style>
            body {{
                background:#0b0f1a;
                color:white;
                font-family:Arial;
                padding:30px;
            }}
            .card {{
                background:#111827;
                padding:20px;
                margin:10px;
                border-radius:15px;
            }}
            .buy {{ color:green; font-size:40px; }}
            .sell {{ color:red; font-size:40px; }}
            .wait {{ color:orange; font-size:40px; }}
        </style>
    </head>

    <body>

        <h1>🔥 XGBOOST AI TRADER</h1>

        <div class="card">
            <h2>PRICE</h2>
            <p>{result['price']}</p>
        </div>

        <div class="card">
            <h2>SIGNAL</h2>
            <p class="{result['signal'].lower()}">
                {result['signal']}
            </p>
        </div>

        <div class="card">
            <h2>PROBABILITY UP</h2>
            <p>{result['probability_up']}</p>
        </div>

        <div class="card">
            <p>⏰ {datetime.now()}</p>
        </div>

    </body>
    </html>
    """

@app.route("/api")
def api():

    return jsonify(prever(model, features))

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=8080, debug=True)