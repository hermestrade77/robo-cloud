import ta
import joblib
import pandas as pd

# =========================
# CARREGAR MODELO IA
# =========================

model = joblib.load("ai/model.pkl")

# =========================
# PREVISÃO IA
# =========================

def predict_signal(df):

    # =====================
    # INDICADORES
    # =====================

    df["rsi"] = ta.momentum.RSIIndicator(
        close=df["close"],
        window=14
    ).rsi()

    df["ema20"] = ta.trend.EMAIndicator(
        close=df["close"],
        window=20
    ).ema_indicator()

    df["ema50"] = ta.trend.EMAIndicator(
        close=df["close"],
        window=50
    ).ema_indicator()

    macd = ta.trend.MACD(
        close=df["close"]
    )

    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()

    df["atr"] = ta.volatility.AverageTrueRange(
        high=df["high"],
        low=df["low"],
        close=df["close"],
        window=14
    ).average_true_range()

    df["volatility"] = (
        df["high"] - df["low"]
    )

    # =====================
    # LIMPEZA
    # =====================

    df.dropna(inplace=True)

    latest = df.iloc[-1]

    # =====================
    # FEATURES IA
    # =====================

    features = [[
        latest["rsi"],
        latest["ema20"],
        latest["ema50"],
        latest["macd"],
        latest["atr"],
        latest["tick_volume"],
        latest["volatility"]
    ]]

    # =====================
    # PREVISÃO IA
    # =====================

    prediction = model.predict(features)[0]

    # =====================
    # SCORE
    # =====================

    buy_score = 0
    sell_score = 0

    reasons = []

    # =====================
    # RSI
    # =====================

    if latest["rsi"] > 60:

        buy_score += 20
        reasons.append("RSI bullish")

    elif latest["rsi"] < 40:

        sell_score += 20
        reasons.append("RSI bearish")

    # =====================
    # EMA
    # =====================

    if latest["ema20"] > latest["ema50"]:

        buy_score += 25
        reasons.append("EMA tendência alta")

    else:

        sell_score += 25
        reasons.append("EMA tendência baixa")

    # =====================
    # MACD
    # =====================

    if latest["macd"] > latest["macd_signal"]:

        buy_score += 20
        reasons.append("MACD bullish")

    else:

        sell_score += 20
        reasons.append("MACD bearish")

    # =====================
    # VOLUME
    # =====================

    volume_mean = (
        df["tick_volume"]
        .tail(20)
        .mean()
    )

    if latest["tick_volume"] > volume_mean:

        buy_score += 10
        sell_score += 10

        reasons.append("Volume forte")

    # =====================
    # VOLATILIDADE
    # =====================

    if latest["atr"] > df["atr"].tail(20).mean():

        buy_score += 10
        sell_score += 10

        reasons.append("Alta volatilidade")

    # =====================
    # IA
    # =====================

    if prediction == 2:

        buy_score += 30
        reasons.append("IA prevê BUY")

    elif prediction == 0:

        sell_score += 30
        reasons.append("IA prevê SELL")

    else:

        reasons.append("IA neutra")

    # =====================
    # DECISÃO FINAL
    # =====================

    if buy_score > sell_score:

        signal = "BUY"
        confidence = buy_score

    elif sell_score > buy_score:

        signal = "SELL"
        confidence = sell_score

    else:

        signal = "HOLD"
        confidence = 50

    # =====================
    # LIMITAR %
    # =====================

    confidence = min(confidence, 100)

    # =====================
    # LOGS
    # =====================

    print("\n====================")
    print("ANÁLISE IA")
    print("====================")

    print(f"RSI: {latest['rsi']:.2f}")
    print(f"EMA20: {latest['ema20']:.2f}")
    print(f"EMA50: {latest['ema50']:.2f}")

    print(f"\nBUY SCORE: {buy_score}")
    print(f"SELL SCORE: {sell_score}")

    print(f"\nCONFIDENCE: {confidence}%")

    print("\nMOTIVOS:")

    for r in reasons:

        print(f"- {r}")

    print("====================")

    return signal