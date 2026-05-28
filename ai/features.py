import pandas as pd
import numpy as np
import MetaTrader5 as mt5

# ============================================
# DETECÇÃO DE SWINGS E FIBONACCI (mantido)
# ============================================
def detectar_swings(df, janela=5):
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

# ============================================
# TICK VOLUME (já existente, mantido)
# ============================================
def calcular_tick_volume(df, symbol="XAUUSD.pro"):
    if not mt5.initialize():
        return df
    if not pd.api.types.is_datetime64_any_dtype(df['time']):
        df['time'] = pd.to_datetime(df['time'])
    volumes = []
    for idx, row in df.iterrows():
        if idx == 0:
            volumes.append(0)
            continue
        start = row['time'].to_pydatetime()
        end = start + pd.Timedelta(minutes=15)  # M15
        ticks = mt5.copy_ticks_range(symbol, start, end, mt5.COPY_TICKS_ALL)
        if ticks is not None:
            volumes.append(len(ticks))
        else:
            volumes.append(0)
    df['tick_volume'] = volumes
    df['tick_volume_ma'] = df['tick_volume'].rolling(20).mean()
    df['tick_volume_ratio'] = df['tick_volume'] / (df['tick_volume_ma'] + 1e-9)
    df.drop(columns=['tick_volume_ma'], inplace=True)
    return df

# ============================================
# NOVOS INDICADORES DE CONFIRMAÇÃO
# ============================================
def adicionar_indicadores_classicos(df):
    """
    Adiciona RSI, MACD, ADX, Bollinger, Estocástico e distâncias de SMAs.
    """
    close = df['close']
    high = df['high']
    low = df['low']

    # --- RSI (14) ---
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / (avg_loss + 1e-9)
    df['rsi'] = 100 - (100 / (1 + rs))

    # --- MACD (12,26,9) ---
    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    macd_line = ema12 - ema26
    signal = macd_line.ewm(span=9).mean()
    df['macd'] = macd_line - signal           # histograma (diferença)
    df['macd_line'] = macd_line
    df['macd_signal'] = signal

    # --- ADX (14) ---
    plus_dm = high.diff().clip(lower=0)
    minus_dm = -low.diff().clip(upper=0)
    tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
    atr14 = tr.rolling(14).mean()
    plus_di = 100 * (plus_dm.rolling(14).mean() / (atr14 + 1e-9))
    minus_di = 100 * (minus_dm.rolling(14).mean() / (atr14 + 1e-9))
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di + 1e-9)) * 100
    df['adx'] = dx.rolling(14).mean()
    df['plus_di'] = plus_di
    df['minus_di'] = minus_di

    # --- Bandas de Bollinger (20,2) ---
    sma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    upper_band = sma20 + 2 * std20
    lower_band = sma20 - 2 * std20
    df['bb_position'] = (close - lower_band) / (upper_band - lower_band + 1e-9)  # 0..1
    df['bb_width'] = (upper_band - lower_band) / (sma20 + 1e-9)

    # --- Estocástico (14,3,3) ---
    low_min = low.rolling(14).min()
    high_max = high.rolling(14).max()
    stoch_k = 100 * (close - low_min) / (high_max - low_min + 1e-9)
    df['stoch_k'] = stoch_k.rolling(3).mean()
    df['stoch_d'] = df['stoch_k'].rolling(3).mean()

    # --- Distâncias percentuais de SMAs (50, 200) ---
    sma50 = close.rolling(50).mean()
    sma200 = close.rolling(200).mean()
    df['dist_sma50'] = (close - sma50) / (sma50 + 1e-9) * 100
    df['dist_sma200'] = (close - sma200) / (sma200 + 1e-9) * 100

    return df

# ============================================
# FUNÇÃO PRINCIPAL PARA CRIAR FEATURES (COM MTF)
# ============================================
def criar_features(data_m15, data_h1=None, symbol="XAUUSD.pro"):
    """
    Cria o vetor de features para o modelo.
    Se data_h1 for fornecido, adiciona features do timeframe maior (MTF).
    """
    # Processa M15
    df = pd.DataFrame(data_m15)
    df["return"] = df["close"].pct_change()
    df["volatility"] = df["return"].rolling(10).std()
    df["ema_fast"] = df["close"].ewm(span=9).mean()
    df["ema_slow"] = df["close"].ewm(span=21).mean()
    df["trend"] = df["ema_fast"] - df["ema_slow"]
    df["trend_strength"] = abs(df["trend"])
    df["momentum"] = df["close"] - df["close"].shift(5)

    # Fibonacci
    fib = calcular_fibonacci(df)
    if fib is not None:
        for nome, valor in fib['distancias'].items():
            df[nome] = valor
    else:
        for nome in ['fib_0_dist', 'fib_236_dist', 'fib_382_dist', 'fib_500_dist',
                     'fib_618_dist', 'fib_786_dist', 'fib_100_dist', 'fib_1618_dist']:
            df[nome] = 0.0

    # Volume
    df = calcular_tick_volume(df, symbol)

    # Indicadores clássicos
    df = adicionar_indicadores_classicos(df)

    df = df.dropna()

    # Features básicas (M15)
    features_m15 = [
        "close", "return", "volatility", "trend", "trend_strength", "momentum",
        "fib_0_dist", "fib_236_dist", "fib_382_dist", "fib_500_dist",
        "fib_618_dist", "fib_786_dist", "fib_100_dist", "fib_1618_dist",
        "tick_volume", "tick_volume_ratio",
        "rsi", "macd", "adx", "plus_di", "minus_di",
        "bb_position", "bb_width",
        "stoch_k", "stoch_d",
        "dist_sma50", "dist_sma200"
    ]

    X = df[features_m15].values

    # Se tiver dados de H1, processa e concatena
    if data_h1 is not None and len(data_h1) >= 50:
        df_h1 = pd.DataFrame(data_h1)
        # Calcula apenas algumas features relevantes do H1 (simplificado)
        df_h1["return"] = df_h1["close"].pct_change()
        df_h1["volatility"] = df_h1["return"].rolling(10).std()
        df_h1["ema_fast"] = df_h1["close"].ewm(span=9).mean()
        df_h1["ema_slow"] = df_h1["close"].ewm(span=21).mean()
        df_h1["trend"] = df_h1["ema_fast"] - df_h1["ema_slow"]
        df_h1["trend_strength"] = abs(df_h1["trend"])
        df_h1["momentum"] = df_h1["close"] - df_h1["close"].shift(5)
        fib_h1 = calcular_fibonacci(df_h1)
        if fib_h1 is not None:
            for nome, valor in fib_h1['distancias'].items():
                df_h1[nome] = valor
        else:
            for nome in ['fib_0_dist', 'fib_236_dist', 'fib_382_dist', 'fib_500_dist',
                         'fib_618_dist', 'fib_786_dist', 'fib_100_dist', 'fib_1618_dist']:
                df_h1[nome] = 0.0
        df_h1 = adicionar_indicadores_classicos(df_h1)
        df_h1 = df_h1.dropna()

        # Alinha os índices: pega o último valor do H1 correspondente ao candle M15
        # Como os timeframes são diferentes, usamos merge_asof para combinar
        if not df_h1.empty:
            # Garantir timezone
            df['time_dt'] = pd.to_datetime(df['time'])
            df_h1['time_dt'] = pd.to_datetime(df_h1['time'])
            df_h1_sorted = df_h1.sort_values('time_dt')
            df_sorted = df.sort_values('time_dt')
            merged = pd.merge_asof(df_sorted, df_h1_sorted, on='time_dt', direction='backward', suffixes=('', '_h1'))
            # Pega as colunas do H1
            features_h1 = [col + '_h1' for col in features_m15 if col in merged.columns]
            # Preenche NaN com 0
            merged[features_h1] = merged[features_h1].fillna(0)
            X_h1 = merged[features_h1].values
            # Concatena as features M15 com H1
            X = np.hstack([X, X_h1])

    # Target
    df["target"] = (df["close"].shift(-1) > df["close"]).astype(int)
    y = df["target"].values
    # Remove linhas onde target é NaN (última linha)
    valid_idx = ~np.isnan(y)
    X = X[valid_idx]
    y = y[valid_idx]
    return X, y