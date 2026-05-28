import pandas as pd
import numpy as np

def detectar_swings(df, janela=5):
    """Retorna listas de índices de swings high e low."""
    highs = df['high'].values
    lows = df['low'].values
    n = len(df)
    swing_highs, swing_lows = [], []
    for i in range(janela, n - janela):
        if highs[i] == max(highs[i - janela : i + janela + 1]):
            swing_highs.append(i)
        if lows[i] == min(lows[i - janela : i + janela + 1]):
            swing_lows.append(i)
    return swing_highs, swing_lows

def calcular_fibonacci(df, swing_janela=5):
    """Calcula níveis e distâncias de Fibonacci do último movimento."""
    swing_highs, swing_lows = detectar_swings(df, swing_janela)
    if not swing_highs or not swing_lows:
        return None

    last_high = max(swing_highs)
    last_low = max(swing_lows)

    if last_high > last_low:
        inicio = df['low'].iloc[last_low]
        fim = df['high'].iloc[last_high]
        tendencia = "ALTA"
    else:
        inicio = df['high'].iloc[last_high]
        fim = df['low'].iloc[last_low]
        tendencia = "BAIXA"

    diff = abs(fim - inicio)
    if diff == 0:
        return None

    ratios = {
        '0': 0.0, '236': 0.236, '382': 0.382,
        '500': 0.5, '618': 0.618, '786': 0.786,
        '100': 1.0, '127': 1.272, '1618': 1.618
    }

    niveis = {}
    for nome, r in ratios.items():
        if tendencia == "ALTA":
            niveis[nome] = inicio + r * diff
        else:
            niveis[nome] = inicio - r * diff

    last_close = df['close'].iloc[-1]
    distancias = {}
    for nome, preco in niveis.items():
        distancias[f'fib_{nome}_dist'] = (last_close - preco) / diff

    return {
        'tendencia_impulso': tendencia,
        'niveis': niveis,
        'distancias': distancias
    }

def criar_features(data):
    """Cria features para o modelo, incluindo Fibonacci."""
    df = pd.DataFrame(data)

    # Features clássicas
    df["return"] = df["close"].pct_change()
    df["volatility"] = df["return"].rolling(10).std()
    df["ema_fast"] = df["close"].ewm(span=9).mean()
    df["ema_slow"] = df["close"].ewm(span=21).mean()
    df["trend"] = df["ema_fast"] - df["ema_slow"]
    df["trend_strength"] = abs(df["trend"])
    df["momentum"] = df["close"] - df["close"].shift(5)
    df["target"] = (df["close"].shift(-1) > df["close"]).astype(int)

    # Fibonacci
    fib = calcular_fibonacci(df)
    if fib is not None:
        for nome, valor in fib['distancias'].items():
            df[nome] = valor
    else:
        # Se não conseguir calcular, preenche com zero
        for nome in ['fib_0_dist', 'fib_236_dist', 'fib_382_dist', 'fib_500_dist',
                     'fib_618_dist', 'fib_786_dist', 'fib_100_dist', 'fib_1618_dist']:
            df[nome] = 0.0

    df = df.dropna()

    feature_cols = [
        "close", "return", "volatility", "trend", "trend_strength", "momentum",
        "fib_0_dist", "fib_236_dist", "fib_382_dist", "fib_500_dist",
        "fib_618_dist", "fib_786_dist", "fib_100_dist", "fib_1618_dist"
    ]

    X = df[feature_cols].values
    y = df["target"].values
    return X, y