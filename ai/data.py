import MetaTrader5 as mt5
import pandas as pd

def obter_dados(symbol="XAUUSD.pro", timeframe=mt5.TIMEFRAME_M15, bars=500):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
    if rates is None or len(rates) == 0:
        return pd.DataFrame()
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    return df

def obter_dados_reais(symbol="XAUUSD.pro", timeframe=mt5.TIMEFRAME_M15, bars=500):
    return obter_dados(symbol, timeframe, bars)