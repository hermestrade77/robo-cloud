def detect_choch(df):

    highs = df["high"]
    lows = df["low"]

    last_high = highs.iloc[-2]
    prev_high = highs.iloc[-5]

    last_low = lows.iloc[-2]
    prev_low = lows.iloc[-5]

    # bullish choch
    if last_high > prev_high:
        return "BUY"

    # bearish choch
    if last_low < prev_low:
        return "SELL"

    return "NONE"