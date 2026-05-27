# =========================================
# ai/model.py - IA PARA XAUUSD
# =========================================

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
import numpy as np

from ai.data import obter_dados_reais
from ai.features import criar_features

# =========================================
# TREINAR MODELO
# =========================================
def treinar_modelo():
    """
    Treina 3 modelos ensemble e retorna:
    - Tupla com modelos treinados
    - Última linha de features para previsão
    """
    print("📥 OBTENDO DADOS...")
    data = obter_dados_reais()

    if len(data) < 150:
        raise Exception(f"❌ POUCOS DADOS MT5: {len(data)} candles")

    print(f"📊 DADOS OBTIDOS: {len(data)} candles")
    
    print("🔧 CRIANDO FEATURES...")
    X, y = criar_features(data)
    
    print(f"🎯 AMOSTRAS: {len(X)} | FEATURES: {X.shape[1] if hasattr(X, 'shape') else '?'}")

    # Inicializar modelos
    rf = RandomForestClassifier(n_estimators=300, max_depth=10, random_state=42)
    gb = GradientBoostingClassifier(n_estimators=200, learning_rate=0.05, random_state=42)
    lr = LogisticRegression(max_iter=2000, C=0.1, random_state=42)

    # Treinar modelos
    print("🧠 TREINANDO RANDOM FOREST...")
    rf.fit(X, y)
    
    print("🧠 TREINANDO GRADIENT BOOSTING...")
    gb.fit(X, y)
    
    print("🧠 TREINANDO LOGISTIC REGRESSION...")
    lr.fit(X, y)

    # Calcular acurácia com cross-validation
    try:
        scores_rf = cross_val_score(rf, X, y, cv=5, scoring='accuracy')
        scores_gb = cross_val_score(gb, X, y, cv=5, scoring='accuracy')
        scores_lr = cross_val_score(lr, X, y, cv=5, scoring='accuracy')
        
        print(f"\n📊 ACURÁCIA MÉDIA:")
        print(f"   Random Forest:      {scores_rf.mean():.2%}")
        print(f"   Gradient Boosting:  {scores_gb.mean():.2%}")
        print(f"   Logistic Regression: {scores_lr.mean():.2%}")
    except:
        print("⚠️ Não foi possível calcular cross-validation")

    # Pegar última linha para features (última observação do treino)
    if hasattr(X, 'iloc'):
        last_features = X.iloc[-1:].values.flatten()
    else:
        last_features = X[-1]

    print("✅ MODELOS TREINADOS COM SUCESSO!")
    
    return (rf, gb, lr), last_features


# =========================================
# FAZER PREVISÃO
# =========================================
def prever(models, features):
    """
    Faz previsão usando média dos 3 modelos
    Retorna um dicionário com 'signal', 'probability_up' e 'probability_down'
    """
    rf, gb, lr = models

    # Probabilidades da classe 1 = UP/COMPRA
    p1 = rf.predict_proba([features])[0][1]
    p2 = gb.predict_proba([features])[0][1]
    p3 = lr.predict_proba([features])[0][1]

    # Média das probabilidades
    prob = (p1 + p2 + p3) / 3

    # Interpretar o sinal
    if prob > 0.60:
        signal = "BUY"
    elif prob < 0.40:
        signal = "SELL"
    else:
        signal = "WAIT"

    # Retornar dicionário estruturado (nunca None)
    return {
        "signal": signal,
        "probability_up": round(prob, 4),
        "probability_down": round(1 - prob, 4)
    }