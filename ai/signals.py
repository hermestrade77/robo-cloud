def gerar_sinal(data):

    if (
        data["rsi"] < 35 and
        data["ema20"] > data["ema50"] and
        data["macd"] > data["macd_signal"]
    ):
        return "BUY"

    elif (
        data["rsi"] > 65 and
        data["ema20"] < data["ema50"] and
        data["macd"] < data["macd_signal"]
    ):
        return "SELL"

    else:
        return "WAIT"