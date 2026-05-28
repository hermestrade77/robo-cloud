import MetaTrader5 as mt5
from datetime import datetime, timedelta, timezone

def get_gold_news(minutes=120):
    """
    Retorna lista de dicionários com 'headline' e 'time' das notícias
    recentes (últimos 'minutes' minutos) relacionadas a ouro/XAUUSD.
    Se o MT5 não estiver conectado, retorna lista vazia.
    """
    if not mt5.initialize():
        print("⚠️ MT5 não inicializado em get_gold_news()")
        return []

    agora = datetime.now(timezone.utc)
    inicio = agora - timedelta(minutes=minutes)
    
    try:
        # Obtém notícias a partir do timestamp inicial (em UTC)
        # O argumento 'datetime_from' aceita datetime.
        news = mt5.news_get(datetime_from=inicio, datetime_to=agora)
        if news is None or len(news) == 0:
            return []
        
        headlines = []
        for n in news:
            # Verifica atributos com segurança
            titulo = getattr(n, 'title', '')
            corpo = getattr(n, 'body', '')
            hora = getattr(n, 'time', None)
            # Filtra por palavras-chave (case insensitive)
            texto = (titulo + ' ' + corpo).lower()
            if any(k in texto for k in ['xau', 'gold', 'ouro', 'gold price', 'xauusd']):
                hora_str = datetime.fromtimestamp(hora, tz=timezone.utc).strftime('%H:%M') if hora else ''
                headlines.append({
                    'headline': titulo,
                    'time': hora_str
                })
        return headlines[:10]  # limita a 10 para o dashboard
    except Exception as e:
        print(f"❌ Erro ao buscar notícias MT5: {e}")
        return []