import feedparser

from news.sentiment import (
    analyze_sentiment
)

# =========================
# RSS INSTITUCIONAL
# =========================

RSS_URLS = [

    "https://www.reutersagency.com/feed/?best-topics=gold&post_type=best",

    "https://www.investing.com/rss/news_25.rss",

]

# =========================
# ANALISAR NOTÍCIAS
# =========================

def analyze_news():

    buy_score = 0
    sell_score = 0

    latest_news = []

    # =====================
    # RSS
    # =====================

    for url in RSS_URLS:

        feed = feedparser.parse(url)

        for entry in feed.entries[:5]:

            title = entry.title

            latest_news.append(title)

            # =================
            # NLP IA
            # =================

            label, confidence = (
                analyze_sentiment(title)
            )

            # =================
            # SCORE
            # =================

            if label == "POSITIVE":

                buy_score += (
                    confidence * 20
                )

            else:

                sell_score += (
                    confidence * 20
                )

    # =====================
    # DECISÃO
    # =====================

    if buy_score > sell_score:

        sentiment = "BUY"

    elif sell_score > buy_score:

        sentiment = "SELL"

    else:

        sentiment = "HOLD"

    # =====================
    # LOG
    # =====================

    print("\n====================")
    print("NEWS SENTIMENT")
    print("====================")

    print(f"BUY SCORE: {buy_score:.2f}")
    print(f"SELL SCORE: {sell_score:.2f}")

    print(f"\nSENTIMENTO FINAL: {sentiment}")

    print("\nÚLTIMAS NOTÍCIAS:\n")

    for n in latest_news:

        print("-", n)

    print("====================")

    return sentiment