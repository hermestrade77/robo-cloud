def premium_discount(df):

    high = df["high"].rolling(50).max().iloc[-1]
    low = df["low"].rolling(50).min().iloc[-1]

    eq = (high + low) / 2

    current = df["close"].iloc[-1]

    if current < eq:
        return "DISCOUNT"

    return "PREMIUM"