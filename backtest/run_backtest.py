import MetaTrader5 as mt5
import pandas as pd

from backtest.engine import (
    get_historical_data
)

from backtest.metrics import (
    calculate_metrics
)

from backtest.report import (
    print_report
)

from ai.signals import predict_signal


# =========================
# INIT MT5
# =========================

mt5.initialize()


# =========================
# DATA
# =========================

df = get_historical_data()

results = []


# =========================
# LOOP
# =========================

for i in range(100, len(df)-1):

    current = df.iloc[:i]

    signal = predict_signal(current)

    entry = df.iloc[i]["close"]

    next_close = df.iloc[i+1]["close"]

    # =====================
    # BUY
    # =====================

    if signal == "BUY":

        pnl = next_close - entry

        results.append(pnl)

    # =====================
    # SELL
    # =====================

    elif signal == "SELL":

        pnl = entry - next_close

        results.append(pnl)


# =========================
# REPORT
# =========================

metrics = calculate_metrics(
    results
)

print_report(metrics)