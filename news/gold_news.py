import feedparser

def get_gold_news(minutes=120):
    """
    Retorna lista de dicionários com 'headline' e 'time' das últimas notícias
    relacionadas a ouro/XAUUSD.
    Usa o Google News RSS (sem API key).
    """
    headlines = []
    try:
        # URL do Google News para "XAUUSD gold" ordenado por data
        url = "https://news.google.com/rss/search?q=XAUUSD+gold&hl=en&gl=US&ceid=US:en"
        feed = feedparser.parse(url)
        if feed.entries:
            for entry in feed.entries[:10]:
                # Extrai data (published) se disponível
                pub = entry.get('published', '')
                headlines.append({
                    'headline': entry.title,
                    'time': pub[:16] if pub else ''
                })
            return headlines
    except Exception as e:
        print(f"❌ Erro ao buscar notícias no Google News: {e}")

    # Se o Google News falhar, tenta o feed da Investing.com
    try:
        url2 = "https://www.investing.com/rss/news_gold.rss"
        feed2 = feedparser.parse(url2)
        if feed2.entries:
            for entry in feed2.entries[:10]:
                pub = entry.get('published', '')
                headlines.append({
                    'headline': entry.title,
                    'time': pub[:16] if pub else ''
                })
            return headlines
    except Exception as e:
        print(f"❌ Erro no feed da Investing.com: {e}")

    # Fallback final: lista vazia
    return headlines