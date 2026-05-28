import MetaTrader5 as mt5
from datetime import datetime, timedelta, timezone

# Eventos de alto impacto USD – datas reais de 2026
HIGH_IMPACT_EVENTS_2026 = [
    # FOMC (decisão de juros) – geralmente às 18:00 UTC
    (2026, 1, 28, 19, 0, "FOMC Decision", "SELL"),
    (2026, 3, 18, 18, 0, "FOMC Decision", "SELL"),
    (2026, 5, 6, 18, 0, "FOMC Decision", "SELL"),
    (2026, 6, 17, 18, 0, "FOMC Decision", "SELL"),
    (2026, 7, 29, 18, 0, "FOMC Decision", "SELL"),
    (2026, 9, 16, 18, 0, "FOMC Decision", "SELL"),
    (2026, 11, 4, 19, 0, "FOMC Decision", "SELL"),
    (2026, 12, 16, 19, 0, "FOMC Decision", "SELL"),

    # NFP – primeira sexta-feira do mês, 13:30 UTC
    (2026, 1, 2, 13, 30, "US Nonfarm Payrolls", "SELL"),
    (2026, 2, 6, 13, 30, "US Nonfarm Payrolls", "SELL"),
    (2026, 3, 6, 13, 30, "US Nonfarm Payrolls", "SELL"),
    (2026, 4, 3, 13, 30, "US Nonfarm Payrolls", "SELL"),
    (2026, 5, 1, 13, 30, "US Nonfarm Payrolls", "SELL"),
    (2026, 6, 5, 13, 30, "US Nonfarm Payrolls", "SELL"),
    (2026, 7, 2, 13, 30, "US Nonfarm Payrolls", "SELL"),
    (2026, 8, 7, 13, 30, "US Nonfarm Payrolls", "SELL"),
    (2026, 9, 4, 13, 30, "US Nonfarm Payrolls", "SELL"),
    (2026, 10, 2, 13, 30, "US Nonfarm Payrolls", "SELL"),
    (2026, 11, 6, 13, 30, "US Nonfarm Payrolls", "SELL"),
    (2026, 12, 4, 13, 30, "US Nonfarm Payrolls", "SELL"),

    # CPI – geralmente segunda semana do mês, 12:30 UTC
    (2026, 1, 14, 13, 30, "US CPI", "SELL"),
    (2026, 2, 11, 13, 30, "US CPI", "SELL"),
    (2026, 3, 11, 13, 30, "US CPI", "SELL"),
    (2026, 4, 15, 12, 30, "US CPI", "SELL"),
    (2026, 5, 13, 12, 30, "US CPI", "SELL"),
    (2026, 6, 10, 12, 30, "US CPI", "SELL"),
    (2026, 7, 15, 12, 30, "US CPI", "SELL"),
    (2026, 8, 12, 12, 30, "US CPI", "SELL"),
    (2026, 9, 16, 12, 30, "US CPI", "SELL"),
    (2026, 10, 14, 12, 30, "US CPI", "SELL"),
    (2026, 11, 12, 13, 30, "US CPI", "SELL"),
    (2026, 12, 11, 13, 30, "US CPI", "SELL"),
]

def analyze_news():
    """
    Retorna um dicionário com:
    - has_high_impact: True se há evento USD de alto impacto nas próximas 2 horas.
    - event: nome do evento ou "Sem notícias de alto impacto".
    - news_signal: "SELL", "BUY" ou "NEUTRAL" (direção esperada para o ouro).
    """
    if not mt5.initialize():
        return {"has_high_impact": False, "event": "MT5 offline", "news_signal": "NEUTRAL"}

    agora = datetime.now(timezone.utc)
    limite = agora + timedelta(hours=2)

    # Tenta o calendário real do MT5 (se disponível)
    if hasattr(mt5, 'calendar_get'):
        try:
            eventos = mt5.calendar_get(datetime_from=agora, datetime_to=limite)
            if eventos is not None and len(eventos) > 0:
                for ev in eventos:
                    currency = getattr(ev, 'currency', '')
                    impact = getattr(ev, 'impact', '')
                    if currency.upper() == "USD" and (impact == "High" or impact == 3):
                        name = getattr(ev, 'name', 'Notícia USD de alto impacto')
                        direction = "NEUTRAL"
                        if any(k in name.lower() for k in ["nonfarm","nfp","cpi","gdp","core pce","ism","fomc"]):
                            direction = "SELL"
                        elif "ecb" in name.lower():
                            direction = "BUY"
                        return {
                            "has_high_impact": True,
                            "event": f"{name} (ALTO IMPACTO)",
                            "news_signal": direction
                        }
                return {"has_high_impact": False, "event": "Nenhum evento próximo", "news_signal": "NEUTRAL"}
        except:
            pass

    # Fallback: usa a tabela de eventos de 2026
    for ev in HIGH_IMPACT_EVENTS_2026:
        y, m, d, h, min, name, direction = ev
        try:
            ev_dt = datetime(y, m, d, h, min, tzinfo=timezone.utc)
        except:
            continue
        if agora <= ev_dt <= limite:
            return {
                "has_high_impact": True,
                "event": f"{name} (ALTO IMPACTO)",
                "news_signal": direction
            }

    return {"has_high_impact": False, "event": "Sem notícias de alto impacto", "news_signal": "NEUTRAL"}


# ========== Funções macro utilizadas pelo features.py ==========
GLOBAL_EVENTS = [
    # Aproveitamos a mesma lista para as features macro (pode ser a mesma ou uma lista maior)
    (2026,1,28,19,0,-1),(2026,3,18,18,0,-1),(2026,5,6,18,0,-1),(2026,6,17,18,0,-1),
    (2026,7,29,18,0,-1),(2026,9,16,18,0,-1),(2026,11,4,19,0,-1),(2026,12,16,19,0,-1),
    (2026,1,21,13,45,1),(2026,3,11,13,45,1),(2026,4,22,13,45,1),(2026,6,10,13,45,1),
    (2026,7,22,13,45,1),(2026,9,9,13,45,1),(2026,10,28,13,45,1),(2026,12,16,13,45,1),
    (2026,1,9,13,30,-1),(2026,2,6,13,30,-1),(2026,3,6,13,30,-1),(2026,4,3,13,30,-1),
    (2026,5,1,13,30,-1),(2026,6,5,13,30,-1),(2026,7,2,13,30,-1),(2026,8,7,13,30,-1),
    (2026,9,4,13,30,-1),(2026,10,2,13,30,-1),(2026,11,6,13,30,-1),(2026,12,4,13,30,-1),
    (2026,1,14,13,30,-1),(2026,2,11,13,30,-1),(2026,3,11,13,30,-1),(2026,4,14,12,30,-1),
    (2026,5,13,12,30,-1),(2026,6,10,12,30,-1),(2026,7,14,12,30,-1),(2026,8,12,12,30,-1),
    (2026,9,15,12,30,-1),(2026,10,13,12,30,-1),(2026,11,12,13,30,-1),(2026,12,11,13,30,-1),
]

def obter_features_macro():
    agora = datetime.now(timezone.utc)
    janelas_h = [12, 24, 72, 168]
    contagens = {f'macro_events_{h}h': 0 for h in janelas_h}
    buy_signals = 0
    sell_signals = 0
    next_days = 999
    next_dir = 0

    for ev in GLOBAL_EVENTS:
        try:
            ev_dt = datetime(ev[0], ev[1], ev[2], ev[3], ev[4], tzinfo=timezone.utc)
        except:
            continue
        diff_h = (ev_dt - agora).total_seconds() / 3600
        if diff_h < 0:
            continue
        for h in janelas_h:
            if diff_h <= h:
                contagens[f'macro_events_{h}h'] += 1
        if diff_h / 24 < next_days:
            next_days = diff_h / 24
            next_dir = ev[5]
        if ev[5] == 1:
            buy_signals += 1
        elif ev[5] == -1:
            sell_signals += 1

    return {
        'macro_events_12h': contagens['macro_events_12h'],
        'macro_events_24h': contagens['macro_events_24h'],
        'macro_events_72h': contagens['macro_events_72h'],
        'macro_events_168h': contagens['macro_events_168h'],
        'macro_buy_signals': buy_signals,
        'macro_sell_signals': sell_signals,
        'macro_days_to_next_event': round(next_days, 2),
        'macro_next_direction': next_dir
    }