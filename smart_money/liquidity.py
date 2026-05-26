import pandas as pd

# =========================
# DETECTAR LIQUIDEZ
# =========================

def detect_liquidity(df):

    latest = df.iloc[-1]

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

    signal = "NONE"

    # =====================
    # SWEEP TOPO
    # =====================

    if (
        latest["high"] > recent_high
        and latest["close"] < recent_high
    ):

        signal = "SELL"

        print("\n====================")
        print("LIQUIDEZ DETECTADA")
        print("====================")

        print("Sweep de topo detectado")

    # =====================
    # SWEEP FUNDO
    # =====================

    elif (
        latest["low"] < recent_low
        and latest["close"] > recent_low
    ):

        signal = "BUY"

        print("\n====================")
        print("LIQUIDEZ DETECTADA")
        print("====================")

        print("Sweep de fundo detectado")

    else:

        print("\nSem sweep de liquidez")

    return signal