import yfinance as yf
import ta

def analisar_xauusd():

    gold = yf.download(
        "GC=F",
        period="5d",
        interval="5m",
        progress=False
    )

    gold["EMA20"] = ta.trend.EMAIndicator(
        gold["Close"],
        window=20
    ).ema_indicator()

    gold["EMA50"] = ta.trend.EMAIndicator(
        gold["Close"],
        window=50
    ).ema_indicator()

    gold["RSI"] = ta.momentum.RSIIndicator(
        gold["Close"]
    ).rsi()

    macd = ta.trend.MACD(gold["Close"])

    gold["MACD"] = macd.macd()
    gold["MACD_SIGNAL"] = macd.macd_signal()

    ultimo = gold.iloc[-1]

    return {

        "price": round(float(ultimo["Close"]), 2),

        "rsi": round(float(ultimo["RSI"]), 2),

        "ema20": round(float(ultimo["EMA20"]), 2),

        "ema50": round(float(ultimo["EMA50"]), 2),

        "macd": round(float(ultimo["MACD"]), 2),

        "macd_signal": round(
            float(ultimo["MACD_SIGNAL"]),
            2
        )

    }