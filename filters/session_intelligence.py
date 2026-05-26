from datetime import datetime

def get_session_intelligence():

    hour = datetime.utcnow().hour

    # =========================
    # ÁSIA
    # =========================

    if 0 <= hour < 6:

        return {
            "session": "ASIA",
            "volatility": "LOW",
            "strategy": "scalp_only",
            "risk": 0.4,
            "min_confluence": 3,
            "allow_trades": True,
            "notes": "mercado lateral, pegar apenas micro movimentos"
        }

    # =========================
    # LONDRES
    # =========================

    elif 7 <= hour < 12:

        return {
            "session": "LONDON",
            "volatility": "HIGH",
            "strategy": "breakout_trend",
            "risk": 1.0,
            "min_confluence": 2,
            "allow_trades": True,
            "notes": "melhor sessão de tendência e rompimento"
        }

    # =========================
    # NEW YORK
    # =========================

    elif 13 <= hour < 18:

        return {
            "session": "NEW_YORK",
            "volatility": "VERY_HIGH",
            "strategy": "continuation_reversal",
            "risk": 0.8,
            "min_confluence": 2,
            "allow_trades": True,
            "notes": "movimentos fortes e reversões rápidas"
        }

    # =========================
    # OFF
    # =========================

    else:

        return {
            "session": "OFF",
            "volatility": "LOW",
            "strategy": "no_trade",
            "risk": 0.2,
            "min_confluence": 99,
            "allow_trades": False,
            "notes": "mercado sem direção"
        }