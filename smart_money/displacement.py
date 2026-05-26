def detect_displacement(df):

    candle = abs(
        df["close"].iloc[-1]
        -
        df["open"].iloc[-1]
    )

    avg = abs(
        df["close"] - df["open"]
    ).rolling(20).mean().iloc[-1]

    if candle > avg * 2:

        if df["close"].iloc[-1] > df["open"].iloc[-1]:
            return "BUY"

        return "SELL"

    return "NONE"