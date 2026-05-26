import sqlite3
import pandas as pd

# =========================
# CONEXÃO
# =========================

conn = sqlite3.connect(
    "trading_data.db"
)

# =========================
# LER DADOS
# =========================

df = pd.read_sql(
    "SELECT * FROM trades",
    conn
)

# =========================
# SEM DADOS
# =========================

if len(df) == 0:

    print("Sem trades salvos")

    quit()

# =========================
# MÉTRICAS
# =========================

total_trades = len(df)

wins = len(
    df[df["result"] > 0]
)

losses = len(
    df[df["result"] <= 0]
)

win_rate = (
    wins / total_trades
) * 100

total_profit = (
    df["result"].sum()
)

average_profit = (
    df["result"].mean()
)

best_trade = (
    df["result"].max()
)

worst_trade = (
    df["result"].min()
)

# =========================
# PROFIT FACTOR
# =========================

gross_profit = (
    df[df["result"] > 0]
    ["result"]
    .sum()
)

gross_loss = abs(

    df[df["result"] < 0]
    ["result"]
    .sum()
)

if gross_loss > 0:

    profit_factor = (
        gross_profit / gross_loss
    )

else:

    profit_factor = 0

# =========================
# RESULTADOS
# =========================

print("\n====================")
print("ANALYTICS ROBO IA")
print("====================")

print(f"TOTAL TRADES: {total_trades}")

print(f"WINS: {wins}")

print(f"LOSSES: {losses}")

print(f"WIN RATE: {win_rate:.2f}%")

print(f"\nTOTAL PROFIT: {total_profit}")

print(
    f"AVERAGE PROFIT: {average_profit}"
)

print(f"BEST TRADE: {best_trade}")

print(f"WORST TRADE: {worst_trade}")

print(
    f"\nPROFIT FACTOR: {profit_factor:.2f}"
)

print("====================")

# =========================
# IA ANALYSIS
# =========================

print("\n====================")
print("IA ANALYSIS")
print("====================")

print(
    df["ai_signal"]
    .value_counts()
)

print("====================")

# =========================
# NEWS ANALYSIS
# =========================

print("\n====================")
print("NEWS ANALYSIS")
print("====================")

print(
    df["news_signal"]
    .value_counts()
)

print("====================")

# =========================
# SMART MONEY
# =========================

print("\n====================")
print("SMART MONEY")
print("====================")

print(
    df["structure_signal"]
    .value_counts()
)

print("====================")