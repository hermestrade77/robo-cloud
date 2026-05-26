def detect_bos(df):

    high_prev = df["high"].iloc[-3]
    low_prev = df["low"].iloc[-3]

    close = df["close"].iloc[-1]

    # bullish BOS
    if close > high_prev:
        return "BUY"

    # bearish BOS
    if close < low_prev:
        return "SELL"

    return "NONE"