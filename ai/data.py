import MetaTrader5 as mt5
import pandas as pd


# =====================================
# INIT MT5
# =====================================

if not mt5.initialize():

    print("ERRO MT5")

# =====================================
# DADOS
# =====================================

def obter_dados(

    symbol="XAUUSD.pro",

    timeframe=mt5.TIMEFRAME_M15,

    bars=500
):

    rates = mt5.copy_rates_from_pos(
        symbol,
        timeframe,
        0,
        bars
    )

    if rates is None:

        print("SEM DADOS MT5")

        return pd.DataFrame()

    df = pd.DataFrame(rates)

    if len(df) == 0:

        print("DATAFRAME VAZIO")

        return pd.DataFrame()

    df["time"] = pd.to_datetime(
        df["time"],
        unit="s"
    )

    return df


# =====================================
# DADOS REAIS
# =====================================

def obter_dados_reais(

    symbol="XAUUSD.pro",

    timeframe=mt5.TIMEFRAME_M15,

    bars=500
):

    return obter_dados(
        symbol,
        timeframe,
        bars
    )