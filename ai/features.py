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
    return {'tendencia_impulso': tendencia, 'niveis': niveis, 'distancias': distancias}

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

    # MACD
    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    macd_line = ema12 - ema26
    signal = macd_line.ewm(span=9).mean()
    df['macd'] = macd_line - signal
    df['macd_line'] = macd_line
    df['macd_signal'] = signal

    # ADX
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

    # Bollinger Bands
    sma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    upper_band = sma20 + 2 * std20
    lower_band = sma20 - 2 * std20
    df['bb_position'] = (close - lower_band) / (upper_band - lower_band + 1e-9)
    df['bb_width'] = (upper_band - lower_band) / (sma20 + 1e-9)

    # Estocástico
    low_min = low.rolling(14).min()
    high_max = high.rolling(14).max()
    stoch_k = 100 * (close - low_min) / (high_max - low_min + 1e-9)
    df['stoch_k'] = stoch_k.rolling(3).mean()
    df['stoch_d'] = df['stoch_k'].rolling(3).mean()

    # Distâncias SMAs
    sma50 = close.rolling(50).mean()
    sma200 = close.rolling(200).mean()
    df['dist_sma50'] = (close - sma50) / (sma50 + 1e-9) * 100
    df['dist_sma200'] = (close - sma200) / (sma200 + 1e-9) * 100
    return df

# ============================================
# NOTÍCIAS (curto prazo) – retorna apenas números
# ============================================
def obter_features_noticias():
    agora = datetime.now(timezone.utc)
    janelas_min = [15, 30, 60, 240]
    contagens = {f'news_{m}m': 0 for m in janelas_min}
    next_event_time = 999
    news_direction_signal = 0

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
                        if diff_min < next_event_time:
                            next_event_time = diff_min
                            # direção simplificada: se menciona FOMC, NFP, etc., sinal -1 (venda ouro)
                            name = getattr(ev, 'name', '').lower()
                            if any(k in name for k in ["nonfarm", "nfp", "cpi", "gdp", "core pce", "ism"]):
                                news_direction_signal = -1
                            elif "ecb" in name:
                                news_direction_signal = 1
        except:
            pass

    # Fallback fixo (apenas para preencher features)
    if next_event_time == 999:
        # Tenta uma tabela fixa simples
        for h, m in [(12,30), (13,30), (14,0), (18,0)]:
            noticia_utc = agora.replace(hour=h, minute=m, second=0, microsecond=0)
            if noticia_utc < agora:
                noticia_utc += timedelta(days=1)
            diff_min = (noticia_utc - agora).total_seconds() / 60
            for janela in janelas_min:
                if diff_min <= janela:
                    contagens[f'news_{janela}m'] += 1
            if diff_min < next_event_time:
                next_event_time = diff_min
                news_direction_signal = -1  # simplificação

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
# MACRO (Fed, juros, eventos globais) – apenas números
# ============================================
GLOBAL_EVENTS = [
    (2026,1,28,19,0,-1), (2026,3,18,18,0,-1), (2026,5,6,18,0,-1), (2026,6,17,18,0,-1),
    (2026,7,29,18,0,-1), (2026,9,16,18,0,-1), (2026,11,4,19,0,-1), (2026,12,16,19,0,-1),
    (2026,1,21,13,45,1), (2026,3,11,13,45,1), (2026,4,22,13,45,1), (2026,6,10,13,45,1),
    (2026,7,22,13,45,1), (2026,9,9,13,45,1), (2026,10,28,13,45,1), (2026,12,16,13,45,1),
    (2026,1,9,13,30,-1), (2026,2,6,13,30,-1), (2026,3,6,13,30,-1), (2026,4,3,13,30,-1),
    (2026,5,1,13,30,-1), (2026,6,5,13,30,-1), (2026,7,2,13,30,-1), (2026,8,7,13,30,-1),
    (2026,9,4,13,30,-1), (2026,10,2,13,30,-1), (2026,11,6,13,30,-1), (2026,12,4,13,30,-1),
    (2026,1,14,13,30,-1), (2026,2,11,13,30,-1), (2026,3,11,13,30,-1), (2026,4,14,12,30,-1),
    (2026,5,13,12,30,-1), (2026,6,10,12,30,-1), (2026,7,14,12,30,-1), (2026,8,12,12,30,-1),
    (2026,9,15,12,30,-1), (2026,10,13,12,30,-1), (2026,11,12,13,30,-1), (2026,12,11,13,30,-1),
]

def obter_features_macro():
    agora = datetime.now(timezone.utc)
    janelas_h = [12, 24, 72, 168]
    contagens = {f'macro_events_{h}h': 0 for h in janelas_h}
    buy_signals = 0
    sell_signals = 0
    next_days = 999
    next_dir = 0

    for ev in GLOBAL_EVENTS:
        try:
            ev_dt = datetime(ev[0], ev[1], ev[2], ev[3], ev[4], tzinfo=timezone.utc)
        except:
            continue
        diff_h = (ev_dt - agora).total_seconds() / 3600
        if diff_h < 0:
            continue
        for h in janelas_h:
            if diff_h <= h:
                contagens[f'macro_events_{h}h'] += 1
        if diff_h / 24 < next_days:
            next_days = diff_h / 24
            next_dir = ev[5]
        if ev[5] == 1:
            buy_signals += 1
        elif ev[5] == -1:
            sell_signals += 1

    return {
        'macro_events_12h': contagens['macro_events_12h'],
        'macro_events_24h': contagens['macro_events_24h'],
        'macro_events_72h': contagens['macro_events_72h'],
        'macro_events_168h': contagens['macro_events_168h'],
        'macro_buy_signals': buy_signals,
        'macro_sell_signals': sell_signals,
        'macro_days_to_next_event': round(next_days, 2),
        'macro_next_direction': next_dir
    }

# ============================================
# FUNÇÃO PRINCIPAL criar_features
# ============================================
def criar_features(data_m15, data_h1=None, data_h4=None, data_d1=None, data_w1=None, symbol="XAUUSD.pro"):
    # --- M15 ---
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
        for nome in ['fib_0_dist','fib_236_dist','fib_382_dist','fib_500_dist',
                     'fib_618_dist','fib_786_dist','fib_100_dist','fib_1618_dist']:
            df[nome] = 0.0

    df = calcular_tick_volume(df, symbol)
    df = adicionar_indicadores_classicos(df)

    news_feats = obter_features_noticias()
    macro_feats = obter_features_macro()
    for k, v in {**news_feats, **macro_feats}.items():
        df[k] = v

    df = df.dropna()

    features_m15 = [
        "close","return","volatility","trend","trend_strength","momentum",
        "fib_0_dist","fib_236_dist","fib_382_dist","fib_500_dist",
        "fib_618_dist","fib_786_dist","fib_100_dist","fib_1618_dist",
        "tick_volume","tick_volume_ratio",
        "rsi","macd","adx","plus_di","minus_di",
        "bb_position","bb_width",
        "stoch_k","stoch_d",
        "dist_sma50","dist_sma200",
        "news_15m","news_30m","news_60m","news_240m",
        "news_next_time","news_high_impact","news_direction_signal",
        "macro_events_12h","macro_events_24h","macro_events_72h","macro_events_168h",
        "macro_buy_signals","macro_sell_signals",
        "macro_days_to_next_event","macro_next_direction"
    ]

    X = df[features_m15].values

    # --- Multitimeframe ---
    def processar_tf(df_tf, prefixo):
        if df_tf is None or len(df_tf) < 50:
            return pd.DataFrame()
        df_tf = pd.DataFrame(df_tf)
        df_tf = adicionar_indicadores_classicos(df_tf)
        fib_tf = calcular_fibonacci(df_tf)
        if fib_tf:
            for nome, val in fib_tf['distancias'].items():
                df_tf[nome] = val
        else:
            for nome in ['fib_0_dist','fib_236_dist','fib_382_dist','fib_500_dist',
                         'fib_618_dist','fib_786_dist','fib_100_dist','fib_1618_dist']:
                df_tf[nome] = 0.0
        df_tf["return"] = df_tf["close"].pct_change()
        df_tf["volatility"] = df_tf["return"].rolling(10).std()
        df_tf["ema_fast"] = df_tf["close"].ewm(span=9).mean()
        df_tf["ema_slow"] = df_tf["close"].ewm(span=21).mean()
        df_tf["trend"] = df_tf["ema_fast"] - df_tf["ema_slow"]
        df_tf["trend_strength"] = abs(df_tf["trend"])
        df_tf["momentum"] = df_tf["close"] - df_tf["close"].shift(5)
        cols = [
            "close","return","volatility","trend","trend_strength","momentum",
            "fib_0_dist","fib_236_dist","fib_382_dist","fib_500_dist",
            "fib_618_dist","fib_786_dist","fib_100_dist","fib_1618_dist",
            "rsi","macd","adx","plus_di","minus_di",
            "bb_position","bb_width",
            "stoch_k","stoch_d",
            "dist_sma50","dist_sma200"
        ]
        exist = [c for c in cols if c in df_tf.columns]
        df_tf = df_tf[exist].dropna()
        df_tf = df_tf.add_prefix(f'{prefixo}_')
        return df_tf

    df['time_dt'] = pd.to_datetime(df['time'])
    base = df.copy()
    for tf_df, prefix in [(data_h1, 'h1'), (data_h4, 'h4'), (data_d1, 'd1'), (data_w1, 'w1')]:
        if tf_df is None or len(tf_df) < 50:
            continue
        tf_proc = processar_tf(tf_df, prefix)
        if tf_proc.empty:
            continue
        tf_proc['time_dt'] = pd.to_datetime(tf_df['time'])
        base = pd.merge_asof(base.sort_values('time_dt'), tf_proc.sort_values('time_dt'),
                             on='time_dt', direction='backward', suffixes=('', f'_{prefix}'))
        # preenche NaN das novas colunas com 0
        novas = [c for c in base.columns if c.startswith(f'{prefix}_')]
        base[novas] = base[novas].fillna(0)

    # Monta X final com todas as colunas (M15 + extras)
    colunas_finais = features_m15.copy()
    for prefix in ['h1', 'h4', 'd1', 'w1']:
        colunas_finais += [c for c in base.columns if c.startswith(f'{prefix}_') and c not in colunas_finais]
    X = base[colunas_finais].values

    # Target
    df["target"] = (df["close"].shift(-1) > df["close"]).astype(int)
    y = df["target"].values
    valid = ~np.isnan(y)
    return X[valid], y[valid]