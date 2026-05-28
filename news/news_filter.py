import MetaTrader5 as mt5
from datetime import datetime, timedelta, timezone

GLOBAL_EVENTS = [
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

def analyze_news():
    if not mt5.initialize():
        return {"has_high_impact": False, "event": "NONE", "news_signal": "NEUTRAL"}
    agora = datetime.now(timezone.utc)
    limite = agora + timedelta(minutes=120)

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
                        return {"has_high_impact": True, "event": f"{name} (ALTO IMPACTO)", "news_signal": direction}
                return {"has_high_impact": False, "event": "Nenhum evento próximo", "news_signal": "NEUTRAL"}
        except:
            pass

    # fallback fixo
    for h, m, desc, direc in [(12,30,"US Core PCE", "SELL"), (13,30,"US NFP","SELL"),
                               (14,0,"US ISM PMI","SELL"), (18,0,"FOMC Minutes","WAIT")]:
        noticia_utc = agora.replace(hour=h, minute=m, second=0, microsecond=0)
        if noticia_utc < agora:
            noticia_utc += timedelta(days=1)
        if agora <= noticia_utc <= limite:
            return {"has_high_impact": True, "event": f"{desc} (ALTO IMPACTO)", "news_signal": direc}
    return {"has_high_impact": False, "event": "Sem notícias de alto impacto", "news_signal": "NEUTRAL"}

def obter_features_macro():
    agora = datetime.now(timezone.utc)
    janelas = [12,24,72,168]
    contagens = {f'macro_events_{h}h':0 for h in janelas}
    buy_sig, sell_sig = 0,0
    next_days, next_dir = 999,0
    for ev in GLOBAL_EVENTS:
        try:
            ev_dt = datetime(ev[0],ev[1],ev[2],ev[3],ev[4],tzinfo=timezone.utc)
        except:
            continue
        diff_h = (ev_dt - agora).total_seconds()/3600
        if diff_h < 0: continue
        for h in janelas:
            if diff_h <= h:
                contagens[f'macro_events_{h}h'] += 1
        if diff_h/24 < next_days:
            next_days = diff_h/24
            next_dir = ev[5]
        if ev[5]==1: buy_sig+=1
        elif ev[5]==-1: sell_sig+=1
    return {
        'macro_events_12h': contagens['macro_events_12h'],
        'macro_events_24h': contagens['macro_events_24h'],
        'macro_events_72h': contagens['macro_events_72h'],
        'macro_events_168h': contagens['macro_events_168h'],
        'macro_buy_signals': buy_sig,
        'macro_sell_signals': sell_sig,
        'macro_days_to_next_event': round(next_days,2),
        'macro_next_direction': next_dir
    }