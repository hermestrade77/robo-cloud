# =========================
# SMART MONEY STRUCTURE
# =========================

def detect_structure(df):

    signal = "NONE"

    # =====================
    # SWING HIGHS
    # =====================

    recent_high = (
        df["high"]
        .tail(20)
        .max()
    )

    previous_high = (
        df["high"]
        .tail(40)
        .head(20)
        .max()
    )

    # =====================
    # SWING LOWS
    # =====================

    recent_low = (
        df["low"]
        .tail(20)
        .min()
    )

    previous_low = (
        df["low"]
        .tail(40)
        .head(20)
        .min()
    )

    latest_close = (
        df["close"]
        .iloc[-1]
    )

    # =====================
    # BOS BULLISH
    # =====================

    if latest_close > previous_high:

        signal = "BUY"

        print("\n====================")
        print("SMART MONEY")
        print("====================")

        print("BOS Bullish confirmado")

    # =====================
    # BOS BEARISH
    # =====================

    elif latest_close < previous_low:

        signal = "SELL"

        print("\n====================")
        print("SMART MONEY")
        print("====================")

        print("BOS Bearish confirmado")

    # =====================
    # CHOCH
    # =====================

    if (
        recent_high < previous_high
        and latest_close < previous_low
    ):

        print("CHOCH Bearish")

    elif (
        recent_low > previous_low
        and latest_close > previous_high
    ):

        print("CHOCH Bullish")

    # =====================
    # DEBUG
    # =====================

    print("\n====================")
    print("ESTRUTURA")
    print("====================")

    print(f"Previous High: {previous_high}")
    print(f"Recent High: {recent_high}")

    print(f"\nPrevious Low: {previous_low}")
    print(f"Recent Low: {recent_low}")

    print(f"\nLatest Close: {latest_close}")

    print(f"\nSIGNAL: {signal}")

    print("====================")

    return signal