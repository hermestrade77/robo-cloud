def detect_liquidity_sweep(df):

    if len(df) < 10:

        return False

    last_high = df["high"].iloc[-2]

    current_high = df["high"].iloc[-1]

    last_low = df["low"].iloc[-2]

    current_low = df["low"].iloc[-1]

    # sweep acima
    if current_high > last_high:

        return True

    # sweep abaixo
    if current_low < last_low:

        return True

    return False