import MetaTrader5 as mt5
import pandas as pd


def get_historical_data(

    symbol="XAUUSD.pro",

    timeframe=mt5.TIMEFRAME_M15,

    bars=5000
):

    rates = mt5.copy_rates_from_pos(
        symbol,
        timeframe,
        0,
        bars
    )

    df = pd.DataFrame(rates)

    df["time"] = pd.to_datetime(
        df["time"],
        unit="s"
    )

    return df