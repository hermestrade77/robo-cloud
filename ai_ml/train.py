import os
import joblib
import pandas as pd

from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

from ai_ml.dataset import load_trades
from ai_ml.features import build_features


# =========================
# LOAD DATA
# =========================

df = load_trades()

print("\n====================")
print("DATASET LOADED")
print("====================")

print("TOTAL TRADES:", len(df))


# =========================
# PROTEÇÃO ANTI-ERRO
# =========================

if df is None or len(df) < 20:

    print("\n❌ ERRO: Poucos dados para treino")

    print("Você precisa de pelo menos 20-50 trades salvos no banco")

    print("Rode o robô MT5 para gerar histórico primeiro")

    exit()


# =========================
# FEATURES
# =========================

X, y = build_features(df)

print("\n====================")
print("FEATURE ENGINEERING")
print("====================")

print("Features shape:", X.shape)

print("Target shape:", y.shape)


# =========================
# PROTEÇÃO EXTRA
# =========================

if len(X) == 0:

    print("\n❌ ERRO: Dataset vazio após processamento")

    exit()


# =========================
# SPLIT
# =========================

X_train, X_test, y_train, y_test = train_test_split(

    X,
    y,
    test_size=0.2,
    random_state=42,
    shuffle=True
)


# =========================
# MODEL
# =========================

model = XGBClassifier(

    n_estimators=300,
    max_depth=5,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    eval_metric="logloss"
)


# =========================
# TRAIN
# =========================

model.fit(X_train, y_train)


# =========================
# PREDICTION
# =========================

y_pred = model.predict(X_test)

acc = accuracy_score(y_test, y_pred)


print("\n====================")
print("MODEL RESULT")
print("====================")

print(f"Accuracy: {acc:.4f}")


# =========================
# IMPORTÂNCIA DAS FEATURES
# =========================

print("\nFEATURE IMPORTANCE:")

for i, col in enumerate(X.columns):

    print(col, "=>", model.feature_importances_[i])


# =========================
# SAVE MODEL
# =========================

os.makedirs("ai_ml", exist_ok=True)

joblib.dump(model, "ai_ml/model.pkl")


print("\n====================")
print("MODEL SAVED")
print("====================")

print("ai_ml/model.pkl pronto para uso")