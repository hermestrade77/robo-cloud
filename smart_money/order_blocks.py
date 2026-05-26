# =========================
# ORDER BLOCK
# =========================

def detect_order_block(df):

    latest = df.iloc[-1]

    previous = df.iloc[-2]

    signal = "NONE"

    # =====================
    # BULLISH OB
    # =====================

    if (

        previous["close"]
        < previous["open"]

        and

        latest["close"]
        > latest["open"]

        and

        latest["close"]
        > previous["high"]

    ):

        signal = "BUY"

        print("\n====================")
        print("ORDER BLOCK")
        print("====================")

        print("Bullish Order Block")

    # =====================
    # BEARISH OB
    # =====================

    elif (

        previous["close"]
        > previous["open"]

        and

        latest["close"]
        < latest["open"]

        and

        latest["close"]
        < previous["low"]

    ):

        signal = "SELL"

        print("\n====================")
        print("ORDER BLOCK")
        print("====================")

        print("Bearish Order Block")

    return signal