import pandas as pd
import numpy as np

def build_features(df):

    # =========================
    # RESULTADO (TARGET)
    # =========================

    df["target"] = (df["result"] > 0).astype(int)

    # =========================
    # FEATURES IMPORTANTES
    # =========================

    df["lot"] = df["lot"]

    df["sl_tp_ratio"] = (
        abs(df["stop_loss"] - df["entry_price"]) /
        abs(df["take_profit"] - df["entry_price"] + 0.00001)
    )

    # signals encoding
    df["ai_signal"] = df["ai_signal"].map({"BUY": 1, "SELL": -1, "NONE": 0})
    df["news_signal"] = df["news_signal"].map({"BUY": 1, "SELL": -1, "NONE": 0})
    df["structure_signal"] = df["structure_signal"].map({"BUY": 1, "SELL": -1, "NONE": 0})
    df["liquidity_signal"] = df["liquidity_signal"].map({"BUY": 1, "SELL": -1, "NONE": 0})

    df = df.dropna()

    features = [

        "lot",
        "sl_tp_ratio",
        "ai_signal",
        "news_signal",
        "structure_signal",
        "liquidity_signal"
    ]

    X = df[features]
    y = df["target"]

    return X, y