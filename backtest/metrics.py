def calculate_metrics(results):

    total = len(results)

    wins = len(
        [r for r in results if r > 0]
    )

    losses = len(
        [r for r in results if r <= 0]
    )

    profit = sum(results)

    winrate = (
        wins / total * 100
        if total > 0 else 0
    )

    drawdown = min(results) if results else 0

    return {

        "total_trades": total,

        "wins": wins,

        "losses": losses,

        "winrate": round(winrate, 2),

        "profit": round(profit, 2),

        "max_drawdown": round(drawdown, 2)
    }