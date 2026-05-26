from transformers import pipeline

# =========================
# MODELO NLP
# =========================

classifier = pipeline(
    "sentiment-analysis"
)

# =========================
# ANALISAR TEXTO
# =========================

def analyze_sentiment(text):

    result = classifier(text)[0]

    label = result["label"]

    score = result["score"]

    print("\n====================")
    print("SENTIMENTO IA")
    print("====================")

    print(f"TEXTO: {text}")
    print(f"LABEL: {label}")
    print(f"CONFIDENCE: {score:.2f}")

    print("====================")

    return label, score