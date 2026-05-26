def detect_mitigation(df):

    last_close = df["close"].iloc[-1]

    prev_high = df["high"].iloc[-5]
    prev_low = df["low"].iloc[-5]

    # mitigação bullish
    if prev_low < last_close < prev_high:
        return "BUY"

    # mitigação bearish
    if prev_high > last_close > prev_low:
        return "SELL"

    return "NONE"