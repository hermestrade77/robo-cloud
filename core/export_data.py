import MetaTrader5 as mt5
import pandas as pd

# =========================
# INICIAR MT5
# =========================

if not mt5.initialize():

    print("ERRO AO INICIAR MT5")
    print(mt5.last_error())

    quit()

print("MT5 iniciado")

# =========================
# SÍMBOLO
# =========================

symbol = "XAUUSD.pro"

# mostra símbolos disponíveis
symbols = mt5.symbols_get()

available = [s.name for s in symbols]

if symbol not in available:

    print(f"{symbol} não encontrado")
    print("Possíveis nomes:")

    for s in available:
        if "XAU" in s:
            print(s)

    quit()

# ativa símbolo
mt5.symbol_select(symbol, True)

# =========================
# PEGAR DADOS
# =========================

rates = mt5.copy_rates_from_pos(
    symbol,
    mt5.TIMEFRAME_M15,
    0,
    5000
)

# =========================
# VALIDAR
# =========================

if rates is None:

    print("Erro ao obter candles")
    print(mt5.last_error())

    quit()

if len(rates) == 0:

    print("Nenhum candle retornado")

    quit()

# =========================
# DATAFRAME
# =========================

df = pd.DataFrame(rates)

print(df.head())

# =========================
# CONVERTER TEMPO
# =========================

df["time"] = pd.to_datetime(
    df["time"],
    unit="s"
)

# =========================
# SALVAR CSV
# =========================

df.to_csv(
    "data/xauusd.csv",
    index=False
)

print("CSV exportado com sucesso")