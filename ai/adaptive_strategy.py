from ai.learner import analyze_performance

# =========================
# PESOS DINÂMICOS
# =========================

def get_dynamic_weights():

    report = analyze_performance()

    if report is None:

        return {
            "ai_weight": 1.0,
            "news_weight": 1.0,
            "smc_weight": 1.0
        }

    # =====================
    # AJUSTE IA
    # =====================

    ai_weight = 1.0

    if report["ai_buy_winrate"] < 0.45:
        ai_weight = 0.7

    if report["ai_buy_winrate"] > 0.60:
        ai_weight = 1.3

    # =====================
    # NEWS WEIGHT
    # =====================

    news_weight = 1.0

    if report["news_winrate"] < 0.5:
        news_weight = 0.6

    # =====================
    # SMC WEIGHT
    # =====================

    smc_weight = 1.0

    return {

        "ai_weight": ai_weight,
        "news_weight": news_weight,
        "smc_weight": smc_weight
    }