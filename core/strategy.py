import pandas as pd
import ta
from ai.signals import predict_signal

class Strategy:

    def __init__(self):
        pass

    # =========================
    # TENDÊNCIA
    # =========================
    def trend_filter(self, df):

        ema20 = ta.trend.EMAIndicator(
            close=df["close"],
            window=20
        ).ema_indicator()

        ema50 = ta.trend.EMAIndicator(
            close=df["close"],
            window=50
        ).ema_indicator()

        if ema20.iloc[-1] > ema50.iloc[-1]:
            return "BUY"

        elif ema20.iloc[-1] < ema50.iloc[-1]:
            return "SELL"

        return "HOLD"

    # =========================
    # RSI
    # =========================
    def rsi_filter(self, df):

        rsi = ta.momentum.RSIIndicator(
            close=df["close"],
            window=14
        ).rsi()

        return rsi.iloc[-1]

    # =========================
    # PRICE ACTION
    # =========================
    def candle_strength(self, df):

        last = df.iloc[-1]

        body = abs(
            last["close"] - last["open"]
        )

        candle_range = (
            last["high"] - last["low"]
        )

        if candle_range == 0:
            return 0

        strength = body / candle_range

        return strength

    # =========================
    # VOLUME
    # =========================
    def volume_filter(self, df):

        volume_mean = (
            df["tick_volume"]
            .tail(20)
            .mean()
        )

        current_volume = (
            df["tick_volume"]
            .iloc[-1]
        )

        return current_volume > volume_mean

    # =========================
    # SCORE FINAL
    # =========================
    def generate_signal(
        self,
        df,
        sentiment_score,
        news_score
    ):

        trend = self.trend_filter(df)

        rsi = self.rsi_filter(df)

        candle = self.candle_strength(df)

        volume_ok = self.volume_filter(df)

        ai_signal = predict_signal(df)

        score_buy = 0
        score_sell = 0

        # =====================
        # TENDÊNCIA
        # =====================

        if trend == "BUY":
            score_buy += 20

        elif trend == "SELL":
            score_sell += 20

        # =====================
        # RSI
        # =====================

        if rsi > 55:
            score_buy += 10

        elif rsi < 45:
            score_sell += 10

        # =====================
        # CANDLE
        # =====================

        if candle > 0.6:
            score_buy += 10

        # =====================
        # VOLUME
        # =====================

        if volume_ok:
            score_buy += 10
            score_sell += 10

        # =====================
        # SENTIMENTO
        # =====================

        if sentiment_score > 0:
            score_buy += 20

        elif sentiment_score < 0:
            score_sell += 20

        # =====================
        # NOTÍCIAS
        # =====================

        if news_score > 0:
            score_buy += 10

        elif news_score < 0:
            score_sell += 10

        # =====================
        # IA
        # =====================

        if ai_signal == "BUY":
            score_buy += 20

        elif ai_signal == "SELL":
            score_sell += 20

        # =====================
        # DECISÃO FINAL
        # =====================

        if score_buy >= 70:
            return "BUY"

        elif score_sell >= 70:
            return "SELL"

        return "HOLD"