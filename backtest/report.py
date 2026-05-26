def print_report(metrics):

    print("\n====================")
    print("BACKTEST REPORT")
    print("====================")

    print(
        "TOTAL:",
        metrics["total_trades"]
    )

    print(
        "WINS:",
        metrics["wins"]
    )

    print(
        "LOSSES:",
        metrics["losses"]
    )

    print(
        "WINRATE:",
        metrics["winrate"],
        "%"
    )

    print(
        "PROFIT:",
        metrics["profit"]
    )

    print(
        "MAX DD:",
        metrics["max_drawdown"]
    )