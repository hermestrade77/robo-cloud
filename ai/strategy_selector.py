from ai.market_regime import detect_market_regime

def select_strategy(df):

    regime = detect_market_regime(df)

    if regime == "TRENDING":

        return {
            "name": "trend_follow",
            "use_breakout": True,
            "use_reversal": False,
            "risk": 1.0
        }

    elif regime == "RANGING":

        return {
            "name": "mean_reversion",
            "use_breakout": False,
            "use_reversal": True,
            "risk": 0.7
        }

    elif regime == "VOLATILE":

        return {
            "name": "safe_mode",
            "use_breakout": False,
            "use_reversal": False,
            "risk": 0.3
        }

    else:  # ACCUMULATION

        return {
            "name": "smart_money",
            "use_breakout": True,
            "use_reversal": True,
            "risk": 0.8
        }