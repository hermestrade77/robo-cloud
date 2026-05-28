import pandas as pd
import numpy as np
import MetaTrader5 as mt5
from datetime import datetime, timedelta, timezone

# ============================================
# DETECÇÃO DE SWINGS E FIBONACCI
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
# TICK VOLUME (apenas M15)
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
        end = start + pd.Timedelta(minutes=15)
        ticks = mt5.copy_ticks_range(symbol, start, end, mt5.COPY_TICKS_ALL)
        volumes.append(len(ticks) if ticks is not None else 0)
    df['tick_volume'] = volumes
    df['tick_volume_ma'] = df['tick_volume'].rolling(20).mean()
    df['tick_volume_ratio'] = df['tick_volume'] / (df['tick_volume_ma'] + 1e-9)
    df.drop(columns=['tick_volume_ma'], inplace=True)
    return df

# ============================================
# INDICADORES CLÁSSICOS
# ============================================
def adicionar_indicadores_classicos(df):
    close = df['close']
    high = df['high']
    low = df['low']

    # RSI (14)
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / (avg_loss + 1e-9)
    df['rsi'] = 100 - (100 / (1 + rs))

    # MACD (12,26,9)
    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    macd_line = ema12 - ema26
    signal = macd_line.ewm(span=9).mean()
    df['macd'] = macd_line - signal
    df['macd_line'] = macd_line
    df['macd_signal'] = signal

    # ADX (14)
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

    # Bandas de Bollinger (20,2)
    sma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    upper_band = sma20 + 2 * std20
    lower_band = sma20 - 2 * std20
    df['bb_position'] = (close - lower_band) / (upper_band - lower_band + 1e-9)
    df['bb_width'] = (upper_band - lower_band) / (sma20 + 1e-9)

    # Estocástico (14,3,3)
    low_min = low.rolling(14).min()
    high_max = high.rolling(14).max()
    stoch_k = 100 * (close - low_min) / (high_max - low_min + 1e-9)
    df['stoch_k'] = stoch_k.rolling(3).mean()
    df['stoch_d'] = df['stoch_k'].rolling(3).mean()

    # Distâncias de SMAs (50,200)
    sma50 = close.rolling(50).mean()
    sma200 = close.rolling(200).mean()
    df['dist_sma50'] = (close - sma50) / (sma50 + 1e-9) * 100
    df['dist_sma200'] = (close - sma200) / (sma200 + 1e-9) * 100

    return df

# ============================================
# FEATURES DE NOTÍCIAS CURTO PRAZO
# ============================================
def obter_features_noticias():
    agora = datetime.now(timezone.utc)
    janelas_min = [15, 30, 60, 240]
    contagens = {f'news_{m}m': 0 for m in janelas_min}
    next_event_time = None
    news_direction_signal = 0

    EVENT_DIRECTION = {
        "Nonfarm Payrolls": -1,
        "Core PCE": -1,
        "GDP": -1,
        "ISM Manufacturing": -1,
        "FOMC": 0,
    }

    if hasattr(mt5, 'calendar_get'):
        try:
            eventos = mt5.calendar_get(datetime_from=agora, datetime_to=agora + timedelta(minutes=240))
            if eventos is not None and len(eventos) > 0:
                for ev in eventos:
                    currency = getattr(ev, 'currency', '')
                    impact = getattr(ev, 'impact', '')
                    if currency.upper() == "USD" and (impact == "High" or impact == 3):
                        event_time = getattr(ev, 'time', None) or getattr(ev, 'datetime', None)
                        if event_time is None:
                            continue
                        diff_min = (event_time.replace(tzinfo=timezone.utc) - agora).total_seconds() / 60
                        for m in janelas_min:
                            if diff_min <= m:
                                contagens[f'news_{m}m'] += 1
                        if next_event_time is None or diff_min < next_event_time:
                            next_event_time = diff_min
                            name = getattr(ev, 'name', '')
                            for key, dir_val in EVENT_DIRECTION.items():
                                if key.lower() in name.lower():
                                    news_direction_signal = dir_val
                                    break
                if next_event_time is not None:
                    return {
                        'news_15m': contagens['news_15m'],
                        'news_30m': contagens['news_30m'],
                        'news_60m': contagens['news_60m'],
                        'news_240m': contagens['news_240m'],
                        'news_next_time': next_event_time,
                        'news_high_impact': 1,
                        'news_direction_signal': news_direction_signal
                    }
        except:
            pass

    # Fallback
    NEWS_SCHEDULE = [
        (12, 30, "US Core PCE Price Index", -1),
        (12, 30, "US GDP Annualized", -1),
        (13, 30, "US Nonfarm Payrolls", -1),
        (14, 0, "US ISM Manufacturing PMI", -1),
        (18, 0, "FOMC Meeting Minutes", 0),
    ]
    for h, m, desc, dir_val in NEWS_SCHEDULE:
        noticia_utc = agora.replace(hour=h, minute=m, second=0, microsecond=0)
        if noticia_utc < agora:
            noticia_utc += timedelta(days=1)
        diff_min = (noticia_utc - agora).total_seconds() / 60
        for janela in janelas_min:
            if diff_min <= janela:
                contagens[f'news_{janela}m'] += 1
        if next_event_time is None or diff_min < next_event_time:
            next_event_time = diff_min
            news_direction_signal = dir_val

    if next_event_time is None:
        next_event_time = 999
        news_direction_signal = 0

    return {
        'news_15m': contagens['news_15m'],
        'news_30m': contagens['news_30m'],
        'news_60m': contagens['news_60m'],
        'news_240m': contagens['news_240m'],
        'news_next_time': next_event_time,
        'news_high_impact': 1 if contagens['news_60m'] > 0 else 0,
        'news_direction_signal': news_direction_signal
    }

# ============================================
# FEATURES MACRO (FED, JUROS)
# ============================================
def obter_features_macro():
    agora = datetime.now(timezone.utc)
    fomc_dates = [
        datetime(2026, 1, 28, 19, 0, tzinfo=timezone.utc),
        datetime(2026, 3, 18, 18, 0, tzinfo=timezone.utc),
        datetime(2026, 5, 6, 18, 0, tzinfo=timezone.utc),
        datetime(2026, 6, 17, 18, 0, tzinfo=timezone.utc),
        datetime(2026, 7, 29, 18, 0, tzinfo=timezone.utc),
        datetime(2026, 9, 16, 18, 0, tzinfo=timezone.utc),
        datetime(2026, 11, 4, 19, 0, tzinfo=timezone.utc),
        datetime(2026, 12, 16, 19, 0, tzinfo=timezone.utc),
    ]
    proxima = None
    for d in fomc_dates:
        if d > agora:
            proxima = d
            break
    dias_ate_fomc = 999
    fomc_hawkish = 0
    if proxima:
        dias_ate_fomc = (proxima - agora).days
        fomc_hawkish = -1   # simplificação: juros altos pressionam ouro

    return {
        'fomc_days_away': dias_ate_fomc,
        'fomc_hawkish': fomc_hawkish
    }

# ============================================
# FUNÇÃO PARA PROCESSAR UM TIMEFRAME MAIOR
# ============================================
def processar_timeframe(df, prefixo):
    if df is None or len(df) < 50:
        return pd.DataFrame()
    df = df.copy()
    df = adicionar_indicadores_classicos(df)
    fib = calcular_fibonacci(df)
    if fib is not None:
        for nome, valor in fib['distancias'].items():
            df[nome] = valor
    else:
        for nome in ['fib_0_dist', 'fib_236_dist', 'fib_382_dist', 'fib_500_dist',
                     'fib_618_dist', 'fib_786_dist', 'fib_100_dist', 'fib_1618_dist']:
            df[nome] = 0.0
    df['return'] = df['close'].pct_change()
    df['volatility'] = df['return'].rolling(10).std()
    df['ema_fast'] = df['close'].ewm(span=9).mean()
    df['ema_slow'] = df['close'].ewm(span=21).mean()
    df['trend'] = df['ema_fast'] - df['ema_slow']
    df['trend_strength'] = abs(df['trend'])
    df['momentum'] = df['close'] - df['close'].shift(5)

    colunas = [
        "close", "return", "volatility", "trend", "trend_strength", "momentum",
        "fib_0_dist", "fib_236_dist", "fib_382_dist", "fib_500_dist",
        "fib_618_dist", "fib_786_dist", "fib_100_dist", "fib_1618_dist",
        "rsi", "macd", "adx", "plus_di", "minus_di",
        "bb_position", "bb_width",
        "stoch_k", "stoch_d",
        "dist_sma50", "dist_sma200"
    ]
    existentes = [c for c in colunas if c in df.columns]
    df = df[existentes].dropna()
    df = df.add_prefix(f'{prefixo}_')
    return df

# ============================================
# FUNÇÃO PRINCIPAL CRIAR FEATURES
# ============================================
def criar_features(data_m15, data_h1=None, data_h4=None, data_d1=None, data_w1=None, symbol="XAUUSD.pro"):
    # --- Processa M15 ---
    df = pd.DataFrame(data_m15)
    df["return"] = df["close"].pct_change()
    df["volatility"] = df["return"].rolling(10).std()
    df["ema_fast"] = df["close"].ewm(span=9).mean()
    df["ema_slow"] = df["close"].ewm(span=21).mean()
    df["trend"] = df["ema_fast"] - df["ema_slow"]
    df["trend_strength"] = abs(df["trend"])
    df["momentum"] = df["close"] - df["close"].shift(5)

    fib = calcular_fibonacci(df)
    if fib is not None:
        for nome, valor in fib['distancias'].items():
            df[nome] = valor
    else:
        for nome in ['fib_0_dist', 'fib_236_dist', 'fib_382_dist', 'fib_500_dist',
                     'fib_618_dist', 'fib_786_dist', 'fib_100_dist', 'fib_1618_dist']:
            df[nome] = 0.0

    df = calcular_tick_volume(df, symbol)
    df = adicionar_indicadores_classicos(df)

    # Features de notícias e macro
    news_feats = obter_features_noticias()
    macro_feats = obter_features_macro()
    for k, v in {**news_feats, **macro_feats}.items():
        df[k] = v

    df = df.dropna()

    features_m15 = [
        "close", "return", "volatility", "trend", "trend_strength", "momentum",
        "fib_0_dist", "fib_236_dist", "fib_382_dist", "fib_500_dist",
        "fib_618_dist", "fib_786_dist", "fib_100_dist", "fib_1618_dist",
        "tick_volume", "tick_volume_ratio",
        "rsi", "macd", "adx", "plus_di", "minus_di",
        "bb_position", "bb_width",
        "stoch_k", "stoch_d",
        "dist_sma50", "dist_sma200",
        "news_15m", "news_30m", "news_60m", "news_240m",
        "news_next_time", "news_high_impact", "news_direction_signal",
        "fomc_days_away", "fomc_hawkish"
    ]

    X = df[features_m15].values

    # --- Função auxiliar para mesclar timeframes superiores ---
    def mesclar_timeframe(df_base, df_tf, prefixo):
        if df_tf is None or len(df_tf) == 0:
            return df_base
        df_tf_proc = processar_timeframe(df_tf, prefixo)
        if df_tf_proc.empty:
            return df_base
        df_base['time_dt'] = pd.to_datetime(df_base['time'])
        df_tf_proc['time_dt'] = pd.to_datetime(df_tf['time'])
        df_tf_sorted = df_tf_proc.sort_values('time_dt')
        merged = pd.merge_asof(df_base.sort_values('time_dt'), df_tf_sorted, on='time_dt', direction='backward', suffixes=('', f'_{prefixo}'))
        cols_tf = [c for c in merged.columns if c.startswith(prefixo)]
        merged[cols_tf] = merged[cols_tf].fillna(0)
        return merged

    merged = df.copy()
    if data_h1 is not None and len(data_h1) >= 50:
        merged = mesclar_timeframe(merged, data_h1, 'h1')
    if data_h4 is not None and len(data_h4) >= 50:
        merged = mesclar_timeframe(merged, data_h4, 'h4')
    if data_d1 is not None and len(data_d1) >= 50:
        merged = mesclar_timeframe(merged, data_d1, 'd1')
    if data_w1 is not None and len(data_w1) >= 30:
        merged = mesclar_timeframe(merged, data_w1, 'w1')

    # Monta matriz final
    colunas_base = features_m15
    for prefixo in ['h1', 'h4', 'd1', 'w1']:
        cols = [c for c in merged.columns if c.startswith(f'{prefixo}_')]
        if cols:
            X_extra = merged[cols].values
            X = np.hstack([X, X_extra])

    # Target
    df["target"] = (df["close"].shift(-1) > df["close"]).astype(int)
    y = df["target"].values
    valid_idx = ~np.isnan(y)
    X = X[valid_idx]
    y = y[valid_idx]
    return X, y