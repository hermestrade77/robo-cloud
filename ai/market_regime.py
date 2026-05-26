import numpy as np

def detect_market_regime(df):

    # volatilidade simples
    atr = (df["high"] - df["low"]).rolling(14).mean().iloc[-1]

    # direção
    ema_fast = df["close"].ewm(span=20).mean().iloc[-1]
    ema_slow = df["close"].ewm(span=50).mean().iloc[-1]

    trend_strength = abs(ema_fast - ema_slow)

    # range detection
    recent_high = df["high"].rolling(20).max().iloc[-1]
    recent_low = df["low"].rolling(20).min().iloc[-1]
    range_size = recent_high - recent_low

    # =========================
    # CLASSIFICAÇÃO
    # =========================

    if atr > range_size * 0.6:
        return "VOLATILE"

    if trend_strength > atr * 1.2:
        return "TRENDING"

    if range_size < atr * 1.5:
        return "RANGING"

    return "ACCUMULATION"