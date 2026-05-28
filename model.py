def prever(model, features):

    prediction = model.predict([features])[0]
    prob = model.predict_proba([features])[0][1]

    signal = "BUY" if prediction == 1 else "SELL"

    return {
        "signal": signal,
        "probability_up": float(prob),
        "price": float(features[0])
    }