import feedparser
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import time

# Carrega o modelo apenas uma vez (cache global)
_tokenizer = None
_model = None

def _load_finbert():
    global _tokenizer, _model
    if _model is None:
        print("🔄 Carregando FinBERT (pode levar alguns segundos)...")
        _tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
        _model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
        _model.eval()
        print("✅ FinBERT carregado.")
    return _tokenizer, _model

def analisar_sentimento_finbert(textos):
    """
    Recebe uma lista de strings (manchetes) e retorna uma lista de dicts
    com 'label' (positive/negative/neutral) e 'score' (probabilidade).
    """
    tokenizer, model = _load_finbert()
    # Tokeniza todos os textos de uma vez (batch)
    inputs = tokenizer(textos, return_tensors="pt", padding=True, truncation=True, max_length=128)
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
    resultados = []
    id2label = {0: "positive", 1: "negative", 2: "neutral"}
    for i, prob in enumerate(probs):
        idx = prob.argmax().item()
        resultados.append({
            'label': id2label[idx],
            'score': prob[idx].item()
        })
    return resultados

def get_gold_news(minutes=120):
    """
    Retorna lista de dicionários com 'headline', 'time' e 'sentiment' (label e score).
    Utiliza cache de 5 minutos para evitar requisições HTTP repetidas.
    """
    # Cache da última busca (já existente)
    if not hasattr(get_gold_news, "_cache"):
        get_gold_news._cache = {'timestamp': 0, 'data': []}

    agora = time.time()
    if agora - get_gold_news._cache['timestamp'] < 300:  # 5 min
        return get_gold_news._cache['data']

    headlines_raw = []
    # 1) Google News
    try:
        url = "https://news.google.com/rss/search?q=XAUUSD+gold+preço&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        feed = feedparser.parse(url)
        for entry in feed.entries[:10]:
            pub = entry.get('published', '')
            headlines_raw.append({
                'headline': entry.title,
                'time': pub[:16] if pub else '',
            })
    except:
        pass

    # 2) Fallback Investing.com
    if not headlines_raw:
        try:
            url2 = "https://www.investing.com/rss/news_gold.rss"
            feed2 = feedparser.parse(url2)
            for entry in feed2.entries[:10]:
                pub = entry.get('published', '')
                headlines_raw.append({
                    'headline': entry.title,
                    'time': pub[:16] if pub else '',
                })
        except:
            pass

    # Se conseguiu manchetes, analisa sentimento com FinBERT
    if headlines_raw:
        textos = [h['headline'] for h in headlines_raw]
        sentiments = analisar_sentimento_finbert(textos)
        for i, h in enumerate(headlines_raw):
            h['sentiment'] = sentiments[i]
    else:
        headlines_raw = []

    get_gold_news._cache['timestamp'] = agora
    get_gold_news._cache['data'] = headlines_raw
    return headlines_raw