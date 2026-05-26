import pandas as pd
import ta
import joblib

from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# =========================
# CARREGAR DADOS
# =========================

df = pd.read_csv("data/xauusd.csv")

# =========================
# INDICADORES
# =========================

df["rsi"] = ta.momentum.RSIIndicator(
    close=df["close"],
    window=14
).rsi()

df["ema20"] = ta.trend.EMAIndicator(
    close=df["close"],
    window=20
).ema_indicator()

df["ema50"] = ta.trend.EMAIndicator(
    close=df["close"],
    window=50
).ema_indicator()

df["macd"] = ta.trend.MACD(
    close=df["close"]
).macd()

df["atr"] = ta.volatility.AverageTrueRange(
    high=df["high"],
    low=df["low"],
    close=df["close"],
    window=14
).average_true_range()

# =========================
# VOLATILIDADE
# =========================

df["volatility"] = (
    df["high"] - df["low"]
)

# =========================
# TARGET
# 0 = SELL
# 1 = HOLD
# 2 = BUY
# =========================

future = df["close"].shift(-5)

df["target"] = 1

threshold = 0.5

df.loc[
    future > df["close"] + threshold,
    "target"
] = 2

df.loc[
    future < df["close"] - threshold,
    "target"
] = 0

# =========================
# LIMPEZA
# =========================

df.dropna(inplace=True)

# =========================
# FEATURES
# =========================

features = [
    "rsi",
    "ema20",
    "ema50",
    "macd",
    "atr",
    "tick_volume",
    "volatility"
]

X = df[features]

y = df["target"]

# =========================
# TREINO
# =========================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

model = XGBClassifier(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.03,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="multi:softmax",
    num_class=3
)

model.fit(X_train, y_train)

# =========================
# TESTE
# =========================

pred = model.predict(X_test)

acc = accuracy_score(y_test, pred)

print(f"\nAccuracy: {acc:.2f}")

# =========================
# SALVAR MODELO
# =========================

joblib.dump(model, "ai/model.pkl")

print("IA treinada com sucesso.")