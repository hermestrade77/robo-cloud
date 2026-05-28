import MetaTrader5 as mt5
from datetime import datetime, timedelta, timezone

# Eventos globais de altíssimo impacto (horário UTC, descrição, direção típica para ouro: 1=BUY, -1=SELL, 0=NEUTRAL)
GLOBAL_EVENTS = [
    # FOMC (decisão de juros) – USD forte tende a pressionar ouro (-1)
    (2026, 1, 28, 19, 0, "FOMC Decision", -1),
    (2026, 3, 18, 18, 0, "FOMC Decision", -1),
    (2026, 5, 6, 18, 0, "FOMC Decision", -1),
    (2026, 6, 17, 18, 0, "FOMC Decision", -1),
    (2026, 7, 29, 18, 0, "FOMC Decision", -1),
    (2026, 9, 16, 18, 0, "FOMC Decision", -1),
    (2026, 11, 4, 19, 0, "FOMC Decision", -1),
    (2026, 12, 16, 19, 0, "FOMC Decision", -1),

    # ECB (taxa de juros) – EUR forte pode enfraquecer USD, beneficiando ouro (+1)
    (2026, 1, 21, 13, 45, "ECB Decision", 1),
    (2026, 3, 11, 13, 45, "ECB Decision", 1),
    (2026, 4, 22, 13, 45, "ECB Decision", 1),
    (2026, 6, 10, 13, 45, "ECB Decision", 1),
    (2026, 7, 22, 13, 45, "ECB Decision", 1),
    (2026, 9, 9, 13, 45, "ECB Decision", 1),
    (2026, 10, 28, 13, 45, "ECB Decision", 1),
    (2026, 12, 16, 13, 45, "ECB Decision", 1),

    # NFP (Nonfarm Payrolls) – USD forte (-1)
    # Ocorre primeira sexta-feira de cada mês, mas usaremos datas exatas de 2026
    (2026, 1, 9, 13, 30, "US NFP", -1),
    (2026, 2, 6, 13, 30, "US NFP", -1),
    (2026, 3, 6, 13, 30, "US NFP", -1),
    (2026, 4, 3, 13, 30, "US NFP", -1),
    (2026, 5, 1, 13, 30, "US NFP", -1),
    (2026, 6, 5, 13, 30, "US NFP", -1),
    (2026, 7, 2, 13, 30, "US NFP", -1),
    (2026, 8, 7, 13, 30, "US NFP", -1),
    (2026, 9, 4, 13, 30, "US NFP", -1),
    (2026, 10, 2, 13, 30, "US NFP", -1),
    (2026, 11, 6, 13, 30, "US NFP", -1),
    (2026, 12, 4, 13, 30, "US NFP", -1),

    # CPI US – inflação alta fortalece USD (-1)
    (2026, 1, 14, 13, 30, "US CPI", -1),
    (2026, 2, 11, 13, 30, "US CPI", -1),
    (2026, 3, 11, 13, 30, "US CPI", -1),
    (2026, 4, 14, 12, 30, "US CPI", -1),
    (2026, 5, 13, 12, 30, "US CPI", -1),
    (2026, 6, 10, 12, 30, "US CPI", -1),
    (2026, 7, 14, 12, 30, "US CPI", -1),
    (2026, 8, 12, 12, 30, "US CPI", -1),
    (2026, 9, 15, 12, 30, "US CPI", -1),
    (2026, 10, 13, 12, 30, "US CPI", -1),
    (2026, 11, 12, 13, 30, "US CPI", -1),
    (2026, 12, 11, 13, 30, "US CPI", -1),
]

def analyze_news():
    """
    Análise de notícias de curto prazo (compatível com versão anterior).
    """
    if not mt5.initialize():
        return {"has_high_impact": False, "event": "NONE", "news_signal": "NEUTRAL"}

    agora = datetime.now(timezone.utc)
    limite = agora + timedelta(minutes=120)

    # Tenta calendário real do MT5
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
                        # Usa mesma lógica de direção do dicionário global
                        for key, dir_val in [("FOMC", "SELL"), ("NFP", "SELL"), ("CPI", "SELL"), ("GDP", "SELL"), ("ECB", "BUY")]:
                            if key.lower() in name.lower():
                                direction = "SELL" if dir_val == "SELL" else "BUY"
                                break
                        return {
                            "has_high_impact": True,
                            "event": f"{name} (ALTO IMPACTO)",
                            "news_signal": direction
                        }
                return {"has_high_impact": False, "event": "Nenhum evento próximo", "news_signal": "NEUTRAL"}
        except:
            pass

    # Fallback com tabela fixa de curto prazo
    NEWS_SCHEDULE = [
        (12, 30, "US Core PCE Price Index", "SELL"),
        (12, 30, "US GDP Annualized", "SELL"),
        (13, 30, "US Nonfarm Payrolls", "SELL"),
        (14, 0, "US ISM Manufacturing PMI", "SELL"),
        (18, 0, "FOMC Meeting Minutes", "WAIT"),
    ]
    for h, m, desc, dir in NEWS_SCHEDULE:
        noticia_utc = agora.replace(hour=h, minute=m, second=0, microsecond=0)
        if noticia_utc < agora:
            noticia_utc += timedelta(days=1)
        if agora <= noticia_utc <= limite:
            return {
                "has_high_impact": True,
                "event": f"{desc} (ALTO IMPACTO)",
                "news_signal": dir
            }
    return {"has_high_impact": False, "event": "Sem notícias de alto impacto", "news_signal": "NEUTRAL"}

def obter_features_macro():
    """
    Retorna features macro amplas baseadas no calendário global de eventos de alto impacto.
    """
    agora = datetime.now(timezone.utc)
    janelas_horas = [12, 24, 72, 168]  # 12h, 24h, 3d, 7d
    contagens = {f'macro_events_{h}h': 0 for h in janelas_horas}
    contagens['macro_buy_signals'] = 0   # total de eventos que favorecem compra no ouro
    contagens['macro_sell_signals'] = 0  # eventos que favorecem venda
    proximo_evento_dias = 999
    proximo_direcao = 0

    for event in GLOBAL_EVENTS + [  # adiciona também os eventos de curto prazo como macro
        (2026, m, d, h, min, "US NFP", -1) for (m, d, h, min) in []  # placeholder, já estão em GLOBAL_EVENTS
    ]:
        try:
            ev_dt = datetime(event[0], event[1], event[2], event[3], event[4], tzinfo=timezone.utc)
        except:
            continue
        diff_horas = (ev_dt - agora).total_seconds() / 3600
        if diff_horas < 0:
            continue
        for h in janelas_horas:
            if diff_horas <= h:
                contagens[f'macro_events_{h}h'] += 1
        if diff_horas / 24 < proximo_evento_dias:
            proximo_evento_dias = diff_horas / 24
            proximo_direcao = event[5]  # 1 ou -1

    if proximo_evento_dias == 999:
        proximo_evento_dias = 999
        proximo_direcao = 0

    return {
        'macro_events_12h': contagens['macro_events_12h'],
        'macro_events_24h': contagens['macro_events_24h'],
        'macro_events_72h': contagens['macro_events_72h'],
        'macro_events_168h': contagens['macro_events_168h'],
        'macro_buy_signals': contagens['macro_buy_signals'],
        'macro_sell_signals': contagens['macro_sell_signals'],
        'macro_days_to_next_event': round(proximo_evento_dias, 2),
        'macro_next_direction': proximo_direcao
    }