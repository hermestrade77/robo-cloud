from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression

from ai.data import obter_dados_reais
from ai.features import criar_features


# =========================
# TREINO
# =========================
def treinar_modelo():

    data = obter_dados_reais()

    if len(data) < 150:
        raise Exception("Poucos dados MT5")

    X, y = criar_features(data)

    rf = RandomForestClassifier(n_estimators=300, max_depth=10, random_state=42)
    gb = GradientBoostingClassifier()
    lr = LogisticRegression(max_iter=2000)

    rf.fit(X, y)
    gb.fit(X, y)
    lr.fit(X, y)

    return (rf, gb, lr), X[-1]


# =========================
# PREVISÃO PROFISSIONAL
# =========================
def prever(models, features):

    rf, gb, lr = models

    p1 = rf.predict_proba([features])[0][1]
    p2 = gb.predict_proba([features])[0][1]
    p3 = lr.predict_proba([features])[0][1]

    prob = (p1 + p2 + p3) / 3

    # 🔥 ZONA PROFISSIONAL (evita mercado lixo)
    if prob > 0.68:
        signal = "BUY"
    elif prob < 0.32:
        signal = "SELL"
    else:
        signal = "WAIT"

    return {
        "signal": signal,
        "probability_up": float(prob),
        "models": [float(p1), float(p2), float(p3)],
        "price": float(features[0])
    }