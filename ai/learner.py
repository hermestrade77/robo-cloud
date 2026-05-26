import sqlite3
import pandas as pd

# =========================
# CARREGAR DADOS
# =========================

def load_data():

    conn = sqlite3.connect("trading_data.db")

    df = pd.read_sql("SELECT * FROM trades", conn)

    return df


# =========================
# CALCULAR PERFORMANCE
# =========================

def analyze_performance():

    df = load_data()

    if len(df) == 0:
        return None

    report = {}

    # =====================
    # SESSÕES
    # =====================

    report["asia_profit"] = df[df["signal"] != ""] .groupby(df["time"].str[:10])["result"].sum().mean()

    # =====================
    # IA PERFORMANCE
    # =====================

    report["ai_buy_winrate"] = len(
        df[(df["ai_signal"] == "BUY") & (df["result"] > 0)]
    ) / max(len(df[df["ai_signal"] == "BUY"]), 1)

    report["ai_sell_winrate"] = len(
        df[(df["ai_signal"] == "SELL") & (df["result"] > 0)]
    ) / max(len(df[df["ai_signal"] == "SELL"]), 1)

    # =====================
    # NEWS IMPACT
    # =====================

    report["news_winrate"] = len(
        df[(df["news_signal"] == "BUY") & (df["result"] > 0)]
    ) / max(len(df[df["news_signal"] != ""]), 1)

    return report