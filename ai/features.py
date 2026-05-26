import pandas as pd
import numpy as np


def criar_features(data):

    df = pd.DataFrame(data)

    # retorno real do mercado
    df["return"] = df["close"].pct_change()

    # volatilidade (risco)
    df["volatility"] = df["return"].rolling(10).std()

    # médias rápidas/lentas
    df["ema_fast"] = df["close"].ewm(span=9).mean()
    df["ema_slow"] = df["close"].ewm(span=21).mean()

    # tendência
    df["trend"] = df["ema_fast"] - df["ema_slow"]

    # força da tendência
    df["trend_strength"] = abs(df["trend"])

    # momentum
    df["momentum"] = df["close"] - df["close"].shift(5)

    # direção futura
    df["target"] = (df["close"].shift(-1) > df["close"]).astype(int)

    df = df.dropna()

    X = df[[
        "close",
        "return",
        "volatility",
        "trend",
        "trend_strength",
        "momentum"
    ]].values

    y = df["target"].values

    return X, y