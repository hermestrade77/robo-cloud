import MetaTrader5 as mt5
import ta

class RiskManager:

    def __init__(self):

        self.risk_per_trade = 0.5
        self.max_daily_loss = 3
        self.max_lot = 0.05

    # =========================
    # ATR STOP
    # =========================

    def calculate_atr_sl(
        self,
        df,
        multiplier=1.5
    ):

        atr = ta.volatility.AverageTrueRange(
            high=df["high"],
            low=df["low"],
            close=df["close"],
            window=14
        ).average_true_range()

        last_atr = atr.iloc[-1]

        sl_distance = last_atr * multiplier

        return round(sl_distance, 2)

    # =========================
    # TAKE PROFIT
    # =========================

    def calculate_tp(
        self,
        sl_distance,
        rr=2
    ):

        tp = sl_distance * rr

        return round(tp, 2)

    # =========================
    # LOTE SEGURO
    # =========================

    def calculate_lot_size(
        self,
        symbol,
        sl_distance
    ):

        account = mt5.account_info()

        balance = account.balance

        # risco financeiro
        risk_money = (
            balance *
            (self.risk_per_trade / 100)
        )

        # info símbolo
        symbol_info = mt5.symbol_info(symbol)

        # proteção
        if symbol_info is None:
            return 0.01

        tick_value = symbol_info.trade_tick_value

        if tick_value <= 0:
            tick_value = 1

        # cálculo lote
        lot = risk_money / (
            sl_distance * tick_value
        )

        # =====================
        # LIMITES
        # =====================

        if lot < 0.01:
            lot = 0.01

        if lot > self.max_lot:
            lot = self.max_lot

        return round(lot, 2)