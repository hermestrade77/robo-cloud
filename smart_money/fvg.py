# =========================
# FAIR VALUE GAP
# =========================

def detect_fvg(df):

    signal = "NONE"

    for i in range(2, len(df)):

        candle1_high = df["high"].iloc[i - 2]

        candle1_low = df["low"].iloc[i - 2]

        candle3_high = df["high"].iloc[i]

        candle3_low = df["low"].iloc[i]

        # =====================
        # BULLISH FVG
        # =====================

        if candle3_low > candle1_high:

            print("\n====================")
            print("FVG BULLISH")
            print("====================")

            print(
                f"Gap: {candle1_high} → {candle3_low}"
            )

            signal = "BUY"

        # =====================
        # BEARISH FVG
        # =====================

        elif candle3_high < candle1_low:

            print("\n====================")
            print("FVG BEARISH")
            print("====================")

            print(
                f"Gap: {candle3_high} → {candle1_low}"
            )

            signal = "SELL"

    return signal