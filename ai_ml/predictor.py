import os
import joblib
import numpy as np

MODEL_PATH = "ai_ml/model.pkl"

model = None

if os.path.exists(MODEL_PATH):
    model = joblib.load(MODEL_PATH)


def predict_ml(features):

    # se não tiver modelo ainda
    if model is None:
        return "NONE", 0.0

    prob = model.predict_proba([features])[0]

    buy_prob = prob[1]
    sell_prob = prob[0]

    if buy_prob > 0.6:
        return "BUY", buy_prob

    if sell_prob > 0.6:
        return "SELL", sell_prob

    return "NONE", max(prob)