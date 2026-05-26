import pandas as pd
import numpy as np

def criar_features(data):

    df = pd.DataFrame(data)

    df["ema"] = df["close"].ewm(span=14).mean()
    df["rsi"] = 100 - (100 / (1 + df["close"].pct_change().rolling(14).mean()))

    df = df.dropna()

    X = df[["close", "ema", "rsi"]].values

    # alvo simples (subiu ou caiu)
    y = (df["close"].shift(-1) > df["close"]).astype(int).dropna()

    return X[:-1], y