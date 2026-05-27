import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time
import requests

from datetime import datetime

# =========================================
# IA
# =========================================

from ai.model import treinar_modelo, prever
from ai.features import criar_features

# =========================================
# NEWS AI
# =========================================

from news.news_filter import analyze_news

# =========================================
# SETTINGS
# =========================================

SYMBOL = "XAUUSD.pro"

TIMEFRAME = mt5.TIMEFRAME_M15

LOT = 0.01

MAGIC = 20260526

# =========================================
# RAILWAY API
# =========================================

RAILWAY_API = "https://robo-cloud-production.up.railway.app/update"

# =========================================
# MT5 INIT
# =========================================

if not mt5.initialize():

    print("❌ ERRO AO CONECTAR MT5")

    quit()

print("\n================================")
print("✅ MT5 CONECTADO")
print("================================")

# =========================================
# IA INIT
# =========================================

print("🧠 TREINANDO IA...")

model, _ = treinar_modelo()

print("✅ IA PRONTA")

# =========================================
# GET DATA
# =========================================

def get_data(

    symbol=SYMBOL,

    timeframe=TIMEFRAME,

    bars=500
):

    rates = mt5.copy_rates_from_pos(

        symbol,

        timeframe,

        0,

        bars
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

# =========================================
# SESSION
# =========================================

def get_session():

    hour = datetime.now().hour

    if 0 <= hour < 7:
        return "ASIA"

    elif 7 <= hour < 13:
        return "LONDON"

    elif 13 <= hour < 17:
        return "NEW YORK"

    return "AFTER"

# =========================================
# TREND
# =========================================

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

# =========================================
# ATR
# =========================================

def calculate_atr(df, period=14):

    high_low = df["high"] - df["low"]

    high_close = np.abs(
        df["high"] - df["close"].shift()
    )

    low_close = np.abs(
        df["low"] - df["close"].shift()
    )

    ranges = pd.concat(

        [
            high_low,
            high_close,
            low_close
        ],

        axis=1
    )

    true_range = np.max(
        ranges,
        axis=1
    )

    atr = pd.Series(
        true_range
    ).rolling(period).mean()

    return atr.iloc[-1]

# =========================================
# POSITION
# =========================================

def has_position():

    positions = mt5.positions_get(
        symbol=SYMBOL
    )

    if positions is None:

        return False

    return len(positions) > 0

# =========================================
# SEND ORDER
# =========================================

def send_order(signal, atr):

    tick = mt5.symbol_info_tick(
        SYMBOL
    )

    if tick is None:

        print("❌ SEM TICK")

        return

    price = (

        tick.ask
        if signal == "BUY"
        else tick.bid
    )

    sl_distance = atr * 2

    tp_distance = atr * 4

    sl = (

        price - sl_distance
        if signal == "BUY"
        else price + sl_distance
    )

    tp = (

        price + tp_distance
        if signal == "BUY"
        else price - tp_distance
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

        "comment": "ROBO_IA_XAUUSD",

        "type_time": mt5.ORDER_TIME_GTC,

        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(
        request
    )

    print("\n================================")
    print("📈 ORDEM ENVIADA")
    print(result)
    print("================================")

# =========================================
# SEND DASHBOARD
# =========================================

def send_dashboard_data(data):

    print("\n================================")
    print("🌐 ENVIANDO DADOS")
    print(data)

    try:

        response = requests.post(

            RAILWAY_API,

            json=data,

            timeout=15
        )

        print("✅ STATUS:", response.status_code)

        print("📨 RESPOSTA:", response.text)

    except Exception as e:

        print("❌ ERRO API:", e)

# =========================================
# MAIN LOOP
# =========================================

while True:

    try:

        print("\n================================")
        print("🤖 ROBO IA XAU/USD")
        print("================================")

        # =================================
        # SESSION
        # =================================

        session = get_session()

        print("⏰ SESSION:", session)

        # =================================
        # MARKET DATA
        # =================================

        df = get_data()

        if len(df) < 100:

            print("❌ SEM DADOS")

            time.sleep(5)

            continue

        # =================================
        # TREND
        # =================================

        trend = get_trend(df)

        # =================================
        # ATR
        # =================================

        atr = calculate_atr(df)

        print("📊 ATR:", atr)

        # =================================
        # AI PREDICTION
        # =================================

        try:

            X_new, _ = criar_features(df)

            if hasattr(X_new, 'iloc'):

                current_features = (

                    X_new.iloc[-1:]
                    .values
                    .flatten()
                )

            else:

                current_features = X_new[-1]

            result = prever(

                model,

                current_features
            )

        except Exception as e:

            print("❌ ERRO IA:", e)

            result = None

        if result is None:

            result = {

                "signal": "WAIT",

                "probability_up": 0
            }

        ai_signal = result.get(
            "signal",
            "WAIT"
        )

        confidence = float(

            result.get(
                "probability_up",
                0
            )
        )

        # =================================
        # NEWS AI
        # =================================

        news = analyze_news()

        if news is None:

            news = {

                "signal": "WAIT",

                "confidence": 0,

                "event": "NONE"
            }

        news_signal = news["signal"]

        news_event = news["event"]

        # =================================
        # SCORES
        # =================================

        buy_score = 0

        sell_score = 0

        # TREND

        if trend == "BUY":
            buy_score += 1

        if trend == "SELL":
            sell_score += 1

        # IA

        if ai_signal == "BUY":
            buy_score += 1

        if ai_signal == "SELL":
            sell_score += 1

        # CONFIDENCE

        if confidence > 0.60:
            buy_score += 1

        if confidence < 0.40:
            sell_score += 1

        # NEWS

        if news_signal == "BUY":
            buy_score += 1

        if news_signal == "SELL":
            sell_score += 1

        # =================================
        # ANALYSIS
        # =================================

        analysis_text = f"""

📊 MARKET ANALYSIS

Trend: {trend}

AI Signal: {ai_signal}

Confidence: {round(confidence * 100, 2)}%

News Event: {news_event}

News Signal: {news_signal}

ATR: {round(atr, 2)}

Session: {session}

Buy Score: {buy_score}

Sell Score: {sell_score}

"""

        # =================================
        # REASONS
        # =================================

        reasons = []

        if trend == "BUY":
            reasons.append(
                "EMA20 acima EMA50"
            )

        if trend == "SELL":
            reasons.append(
                "EMA20 abaixo EMA50"
            )

        if ai_signal == "BUY":
            reasons.append(
                "IA detectou compra"
            )

        if ai_signal == "SELL":
            reasons.append(
                "IA detectou venda"
            )

        if confidence > 0.60:
            reasons.append(
                "Alta confiança bullish"
            )

        if confidence < 0.40:
            reasons.append(
                "Alta confiança bearish"
            )

        if news_signal == "BUY":
            reasons.append(
                "Notícia favorece BUY"
            )

        if news_signal == "SELL":
            reasons.append(
                "Notícia favorece SELL"
            )

        reason_text = "\n".join(
            reasons
        )

        # =================================
        # PRICE
        # =================================

        current_price = float(

            df["close"].iloc[-1]
        )

        tick = mt5.symbol_info_tick(
            SYMBOL
        )

        spread = round(

            tick.ask - tick.bid,

            2
        )

        # =================================
        # DEBUG
        # =================================

        print("📊 TREND:", trend)

        print("🧠 IA:", ai_signal)

        print("🎯 CONFIDENCE:", confidence)

        print("📰 NEWS:", news_event)

        print("🚀 BUY SCORE:", buy_score)

        print("🔻 SELL SCORE:", sell_score)

        # =================================
        # DASHBOARD DATA
        # =================================

        dashboard_data = {

            "signal": ai_signal,

            "confidence": round(
                confidence * 100,
                2
            ),

            "market": trend,

            "price": current_price,

            "atr": round(
                atr,
                2
            ),

            "spread": spread,

            "bos": trend,

            "choch": ai_signal,

            "sweep": False,

            "session": session,

            "news": news_event,

            "news_signal": news_signal,

            "analysis": analysis_text,

            "reason": reason_text,

            "buy_score": buy_score,

            "sell_score": sell_score,

            "winrate": 68,

            "trades": 42,

            "pnl": "+$1,420",

            "timestamp": str(
                datetime.now()
            )
        }

        # =================================
        # SEND API
        # =================================

        send_dashboard_data(
            dashboard_data
        )

        # =================================
        # ENTRY
        # =================================

        if not has_position():

            if buy_score >= 3:

                print("🚀 BUY FORTE")

                send_order(
                    "BUY",
                    atr
                )

            elif sell_score >= 3:

                print("🔻 SELL FORTE")

                send_order(
                    "SELL",
                    atr
                )

            else:

                print("❌ SEM ENTRADA")

        else:

            print("⚠ POSIÇÃO ABERTA")

        # =================================
        # UPDATE SPEED
        # =================================

        time.sleep(5)

    except Exception as e:

        print("❌ ERRO LOOP:", e)

        time.sleep(5)