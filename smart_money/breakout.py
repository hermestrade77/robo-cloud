# =========================
# BREAKOUT
# =========================

def detect_breakout(df):

    recent_high = (
        df["high"]
        .tail(20)
        .max()
    )

    recent_low = (
        df["low"]
        .tail(20)
        .min()
    )

    current_close = (
        df["close"]
        .iloc[-1]
    )

    # =====================
    # BREAKOUT BUY
    # =====================

    if current_close > recent_high:

        print("\n====================")
        print("BREAKOUT BUY")
        print("====================")

        return "BUY"

    # =====================
    # BREAKOUT SELL
    # =====================

    elif current_close < recent_low:

        print("\n====================")
        print("BREAKOUT SELL")
        print("====================")

        return "SELL"

    return "NONE"