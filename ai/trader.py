import MetaTrader5 as mt5

mt5.initialize()

SYMBOL = "XAUUSD.pro"


def executar_trade(signal, atr):

    if not mt5.symbol_select(SYMBOL, True):
        print("Erro símbolo")
        return

    tick = mt5.symbol_info_tick(SYMBOL)

    if tick is None:
        return

    lot = 0.01

    price = tick.ask if signal == "BUY" else tick.bid

    # 🧠 ATR baseado em pontos reais
    sl_distance = atr * 1.5   # stop loss inteligente
    tp_distance = atr * 3.0   # take profit dinâmico

    if signal == "BUY":

        sl = price - sl_distance
        tp = price + tp_distance
        order_type = mt5.ORDER_TYPE_BUY

    else:

        sl = price + sl_distance
        tp = price - tp_distance
        order_type = mt5.ORDER_TYPE_SELL

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": SYMBOL,
        "volume": lot,
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 20,
        "magic": 777001,
        "comment": "AI ATR SYSTEM",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)

    print("💰 Trade enviado:", result)