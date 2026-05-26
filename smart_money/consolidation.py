import numpy as np

# =========================
# CONSOLIDAÇÃO
# =========================

def detect_consolidation(df):

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

    range_size = (
        recent_high - recent_low
    )

    average_candle = np.mean(

        df["high"].tail(20)

        -

        df["low"].tail(20)
    )

    # =====================
    # CONSOLIDAÇÃO
    # =====================

    if range_size < (
        average_candle * 3
    ):

        print("\n====================")
        print("CONSOLIDAÇÃO")
        print("====================")

        print(
            f"RANGE: {range_size}"
        )

        return True

    return False