from datetime import datetime

def analyze_news():

    hour = datetime.utcnow().hour

    # ====================================
    # EXEMPLO SIMPLES
    # ====================================

    # horário comum de notícias fortes USD

    if hour in [12, 13, 14]:

        return {

            "impact": "HIGH",

            "signal": "SELL",

            "confidence": 0.75,

            "event": "USD NEWS"
        }

    return {

        "impact": "LOW",

        "signal": "WAIT",

        "confidence": 0.50,

        "event": "NONE"
    }