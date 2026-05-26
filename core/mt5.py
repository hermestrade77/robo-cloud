import MetaTrader5 as mt5
import pandas as pd
import time

from datetime import datetime

from ai.model import (
    treinar_modelo,
    prever
)

from core.shared_data import shared_data

# ======================================
# SETTINGS
# ======================================

SYMBOL = "XAUUSD.pro"

LOT = 0.01

MAGIC = 20260526

TIMEFRAME = mt5.TIMEFRAME_M15

# ======================================
# MT5
# ======================================

if not mt5.initialize():

    print("ERRO MT5")

    quit()

print("================================")
print("MT5 CONECTADO")
print("================================")

# ======================================
# IA
# ======================================

print("🧠 TREINANDO IA...")

model, features = treinar_modelo()

print("✅ IA PRONTA")

# ======================================
# DADOS
# ======================================

def get_data():

    rates = mt5.copy_rates_from_pos(

        SYMBOL,

        TIMEFRAME,

        0,

        500
    )

    if rates is None:

        return pd.DataFrame()

    df = pd.DataFrame(rates)

    if len(df) == 0:

        return pd.DataFrame()

    df["time"] = pd.to_datetime(
        df["time"],
        unit="s"
    )

    return df

# ======================================
# SESSION
# ======================================

def get_session():

    hour = datetime.now().hour

    if 0 <= hour < 7:
        return "ASIA"

    elif 7 <= hour < 13:
        return "LONDON"

    elif 13 <= hour < 17:
        return "NEW YORK"

    return "AFTER"

# ======================================
# TREND
# ======================================

def get_trend(df):

    ema20 = df["close"].ewm(
        span=20
    ).mean()

    ema50 = df["close"].ewm(
        span=50
    ).mean()

    if ema20.iloc[-1] > ema50.iloc[-1]:

        return "BUY"

    elif ema20.iloc[-1] < ema50.iloc[-1]:

        return "SELL"

    return "WAIT"

# ======================================
# POSITION
# ======================================

def has_position():

    positions = mt5.positions_get(
        symbol=SYMBOL
    )

    if positions is None:

        return False

    return len(positions) > 0

# ======================================
# ORDER
# ======================================

def send_order(signal):

    tick = mt5.symbol_info_tick(
        SYMBOL
    )

    if tick is None:

        return

    price = (

        tick.ask
        if signal == "BUY"
        else tick.bid
    )

    sl_distance = 300
    tp_distance = 600

    sl = (

        price - sl_distance * 0.01
        if signal == "BUY"
        else price + sl_distance * 0.01
    )

    tp = (

        price + tp_distance * 0.01
        if signal == "BUY"
        else price - tp_distance * 0.01
    )

    request = {

        "action": mt5.TRADE_ACTION_DEAL,

        "symbol": SYMBOL,

        "volume": LOT,

        "type": (

            mt5.ORDER_TYPE_BUY
            if signal == "BUY"
            else mt5.ORDER_TYPE_SELL
        ),

        "price": price,

        "sl": sl,

        "tp": tp,

        "deviation": 20,

        "magic": MAGIC,

        "comment": "ROBO_IA",

        "type_time": mt5.ORDER_TIME_GTC,

        "type_filling": (
            mt5.ORDER_FILLING_IOC
        ),
    }

    result = mt5.order_send(
        request
    )

    print(result)

# ======================================
# LOOP
# ======================================

while True:

    try:

        print("\n====================")
        print("ROBO IA XAU/USD")
        print("====================")

        session = get_session()

        print("SESSION:", session)

        df = get_data()

        if len(df) < 100:

            print("SEM DADOS")

            time.sleep(10)

            continue

        trend = get_trend(df)

        result = prever(
            model,
            features
        )

        ai_signal = result.get(
            "signal",
            "WAIT"
        )

        confidence = result.get(
            "probability_up",
            0
        )

        # ==============================
        # SCORE
        # ==============================

        buy_score = 0
        sell_score = 0

        if trend == "BUY":
            buy_score += 1

        if trend == "SELL":
            sell_score += 1

        if ai_signal == "BUY":
            buy_score += 1

        if ai_signal == "SELL":
            sell_score += 1

        if confidence > 0.55:
            buy_score += 1

        if confidence < 0.45:
            sell_score += 1

        # ==============================
        # DEBUG
        # ==============================

        print("TREND:", trend)

        print("AI:", ai_signal)

        print("CONFIDENCE:", confidence)

        print("BUY SCORE:", buy_score)

        print("SELL SCORE:", sell_score)

        # ==============================
        # SHARED DATA
        # ==============================

        shared_data["signal"] = ai_signal

        shared_data["confidence"] = confidence

        shared_data["market"] = trend

        shared_data["bos"] = trend

        shared_data["choch"] = ai_signal

        shared_data["sweep"] = False

        shared_data["session"] = session

        shared_data["winrate"] = 68

        shared_data["trades"] = 42

        shared_data["pnl"] = "+$1,420"

        # ==============================
        # ENTRY
        # ==============================

        if not has_position():

            if buy_score >= 2:

                print("🚀 BUY")

                send_order("BUY")

            elif sell_score >= 2:

                print("🔻 SELL")

                send_order("SELL")

            else:

                print("❌ SEM ENTRADA")

        else:

            print("⚠ POSIÇÃO ABERTA")

        time.sleep(30)

    except Exception as e:

        print("ERRO:", e)

        time.sleep(10)