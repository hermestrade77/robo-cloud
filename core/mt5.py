import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time
import requests
from datetime import datetime, timedelta

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
# RAILWAY API (servidor do dashboard)
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
# FUNÇÕES AUXILIARES
# =========================================

def get_data(symbol=SYMBOL, timeframe=TIMEFRAME, bars=500):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
    if rates is None:
        return pd.DataFrame()
    df = pd.DataFrame(rates)
    if len(df) == 0:
        return pd.DataFrame()
    df["time"] = pd.to_datetime(df["time"], unit="s")
    return df

def get_session():
    hour = datetime.now().hour
    if 0 <= hour < 7:
        return "ASIA"
    elif 7 <= hour < 13:
        return "LONDON"
    elif 13 <= hour < 17:
        return "NEW YORK"
    return "AFTER"

def get_trend(df):
    ema20 = df["close"].ewm(span=20).mean()
    ema50 = df["close"].ewm(span=50).mean()
    if ema20.iloc[-1] > ema50.iloc[-1]:
        return "BUY"
    elif ema20.iloc[-1] < ema50.iloc[-1]:
        return "SELL"
    return "WAIT"

def calculate_atr(df, period=14):
    high_low = df["high"] - df["low"]
    high_close = np.abs(df["high"] - df["close"].shift())
    low_close = np.abs(df["low"] - df["close"].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    atr = pd.Series(true_range).rolling(period).mean()
    return atr.iloc[-1]

def has_position():
    positions = mt5.positions_get(symbol=SYMBOL)
    if positions is None:
        return False
    return len(positions) > 0

def send_order(signal, atr):
    tick = mt5.symbol_info_tick(SYMBOL)
    if tick is None:
        print("❌ SEM TICK")
        return

    price = tick.ask if signal == "BUY" else tick.bid
    sl_distance = atr * 2
    tp_distance = atr * 4

    sl = price - sl_distance if signal == "BUY" else price + sl_distance
    tp = price + tp_distance if signal == "BUY" else price - tp_distance

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": SYMBOL,
        "volume": LOT,
        "type": mt5.ORDER_TYPE_BUY if signal == "BUY" else mt5.ORDER_TYPE_SELL,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 20,
        "magic": MAGIC,
        "comment": "ROBO_IA_XAUUSD",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)
    print("\n================================")
    print("📈 ORDEM ENVIADA")
    print(result)
    print("================================")

def send_dashboard_data(data):
    print("\n================================")
    print("🌐 ENVIANDO DADOS")
    print(data)
    try:
        response = requests.post(RAILWAY_API, json=data, timeout=15)
        print("✅ STATUS:", response.status_code)
        print("📨 RESPOSTA:", response.text)
    except Exception as e:
        print("❌ ERRO API:", e)

# =========================================
# MÉTRICAS DA CONTA (DINÂMICAS)
# =========================================

def get_account_profit():
    """Lucro flutuante da conta"""
    acc = mt5.account_info()
    if acc is None:
        return 0.0
    return acc.profit

def get_total_trades():
    """Total de negócios fechados nos últimos 30 dias (ou desde sempre)"""
    # Pega histórico dos últimos 30 dias para não sobrecarregar
    from_date = datetime.now() - timedelta(days=30)
    deals = mt5.history_deals_get(from_date, datetime.now())
    if deals is None:
        return 0
    # Conta apenas deals com entrada/saída (DEAL_ENTRY_IN ou DEAL_ENTRY_OUT conforme necessário)
    # Simplificando: conta total de deals (inclui entradas e saídas). Para trades fechados, melhor usar history_orders.
    # Usarei history_orders para contar ordens fechadas.
    orders = mt5.history_orders_get(from_date, datetime.now())
    if orders is None:
        return 0
    # Filtra ordens fechadas (state == ORDER_STATE_FILLED ou similar)
    # Simplificação: conta todas as ordens com tipo de fechamento.
    return len(orders)

def get_winrate():
    """Winrate baseada no histórico de ordens fechadas (ganhadoras / total)"""
    from_date = datetime.now() - timedelta(days=30)
    history = mt5.history_deals_get(from_date, datetime.now())
    if history is None or len(history) == 0:
        return 0

    df = pd.DataFrame(list(history), columns=history[0]._asdict().keys())
    # Filtra apenas deals de saída (entry=1 é saída?)
    # Melhor abordagem: usar history_orders para ordens fechadas e ver lucro.
    orders = mt5.history_orders_get(from_date, datetime.now())
    if orders is None or len(orders) == 0:
        return 0
    df_orders = pd.DataFrame(list(orders), columns=orders[0]._asdict().keys())
    # Considera apenas ordens fechadas com lucro != 0 (ou todas com lucro conhecido)
    closed = df_orders[df_orders['profit'] != 0] if 'profit' in df_orders.columns else df_orders
    if len(closed) == 0:
        return 0
    winners = len(closed[closed['profit'] > 0])
    return round((winners / len(closed)) * 100, 2)

# =========================================
# MAIN LOOP
# =========================================
while True:
    try:
        print("\n================================")
        print("🤖 ROBO IA XAU/USD")
        print("================================")

        session = get_session()
        print("⏰ SESSION:", session)

        df = get_data()
        if len(df) < 100:
            print("❌ SEM DADOS")
            time.sleep(10)
            continue

        trend = get_trend(df)
        atr = calculate_atr(df)
        print("📊 ATR:", atr)

        # IA
        try:
            X_new, _ = criar_features(df)
            if hasattr(X_new, 'iloc'):
                current_features = X_new.iloc[-1:].values.flatten()
            else:
                current_features = X_new[-1]
            result = prever(model, current_features)
        except Exception as e:
            print("❌ Erro na IA:", e)
            result = None

        if result is None:
            result = {"signal": "WAIT", "probability_up": 0, "probability_down": 1}

        ai_signal = result.get("signal", "WAIT")
        confidence = round(float(result.get("probability_up", 0)) * 100, 2)  # em %

        # News
        news = analyze_news()
        if news is None:
            news = {"signal": "WAIT", "confidence": 0, "event": "NONE"}
        news_signal = news["signal"]
        news_event = news["event"]

        # Scores
        buy_score = 0
        sell_score = 0
        if trend == "BUY": buy_score += 1
        if trend == "SELL": sell_score += 1
        if ai_signal == "BUY": buy_score += 1
        if ai_signal == "SELL": sell_score += 1
        if confidence > 60: buy_score += 1
        if confidence < 40: sell_score += 1
        if news_signal == "BUY": buy_score += 1
        if news_signal == "SELL": sell_score += 1

        # Tick para preço e spread
        tick = mt5.symbol_info_tick(SYMBOL)
        price = tick.ask if tick else 0
        spread = tick.spread if tick else 0

        # Métricas da conta
        pnl = get_account_profit()
        trades = get_total_trades()
        winrate = get_winrate()

        # Strings de análise
        reason = "EMA20 acima EMA50" if trend == "BUY" else "EMA20 abaixo EMA50" if trend == "SELL" else "Indefinido"
        analysis = f"""
📊 ANÁLISE DE MERCADO
Trend: {trend}
AI Signal: {ai_signal}
Confidence: {confidence}%
News: {news_event}
News Signal: {news_signal}
ATR: {atr:.2f}
Session: {session}
Buy Score: {buy_score}
Sell Score: {sell_score}
"""

        # Dados para o dashboard
        dashboard_data = {
            "signal": ai_signal,
            "confidence": confidence,
            "market": trend,
            "price": price,
            "atr": round(atr, 2),
            "spread": spread,
            "news": news_event,
            "news_signal": news_signal,
            "session": session,
            "analysis": analysis,
            "reason": reason,
            "buy_score": buy_score,
            "sell_score": sell_score,
            "winrate": winrate,
            "trades": trades,
            "pnl": f"${pnl:.2f}"
        }

        send_dashboard_data(dashboard_data)

        print("📊 TREND:", trend)
        print("🧠 AI:", ai_signal)
        print("🎯 CONFIDENCE:", confidence, "%")
        print("📰 NEWS:", news_event)
        print("🚀 BUY SCORE:", buy_score)
        print("🔻 SELL SCORE:", sell_score)

        # Entrada
        if not has_position():
            if buy_score >= 3:
                print("🚀 BUY FORTE")
                send_order("BUY", atr)
            elif sell_score >= 3:
                print("🔻 SELL FORTE")
                send_order("SELL", atr)
            else:
                print("❌ SEM ENTRADA")
        else:
            print("⚠ POSIÇÃO ABERTA")

        time.sleep(30)

    except Exception as e:
        print("❌ ERRO LOOP:", e)
        time.sleep(10)