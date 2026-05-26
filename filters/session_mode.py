from datetime import datetime

# =========================
# SESSION MODE ENGINE
# =========================

def get_session_mode():

    hour = datetime.utcnow().hour

    # =====================
    # ÁSIA (00–06)
    # =====================

    if 0 <= hour < 6:

        return {
            "name": "ASIA",
            "risk": 0.5,
            "strategy": "scalp",
            "aggression": "low"
        }

    # =====================
    # LONDRES (07–12)
    # =====================

    elif 7 <= hour < 12:

        return {
            "name": "LONDON",
            "risk": 1.0,
            "strategy": "trend_breakout",
            "aggression": "high"
        }

    # =====================
    # NY (13–18)
    # =====================

    elif 13 <= hour < 18:

        return {
            "name": "NEW_YORK",
            "risk": 0.8,
            "strategy": "continuation_reversal",
            "aggression": "high"
        }

    # =====================
    # LATERAL / OFF PEAK
    # =====================

    else:

        return {
            "name": "OFF",
            "risk": 0.3,
            "strategy": "filter_only",
            "aggression": "low"
        }