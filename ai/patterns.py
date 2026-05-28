import pandas as pd
import numpy as np

def detectar_swings(df, janela=5):
    """Retorna listas de índices de swing highs e swing lows."""
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

def detectar_duplo_topo_fundo(df, swing_janela=5, tolerancia=0.01):
    """
    Detecta Duplo Topo (reversão baixista) e Duplo Fundo (reversão altista).
    Retorna dict com 'padrao': 'DUPLO_TOPO'/'DUPLO_FUNDO'/None,
    'preco_entrada': nível de rompimento do neckline,
    'sl': topo/fundo do padrão,
    'tp': projeção da altura.
    """
    if len(df) < swing_janela * 3:
        return None

    highs = df['high'].values
    lows = df['low'].values
    closes = df['close'].values

    # Detecta swings nos últimos candles
    swing_h, swing_l = detectar_swings(df, swing_janela)
    if len(swing_h) < 2 or len(swing_l) < 2:
        return None

    # Duplo Topo: dois topos próximos em preço (com um fundo entre eles)
    last_h = swing_h[-1]
    prev_h = swing_h[-2] if len(swing_h) >= 2 else None
    if prev_h is not None:
        # Encontra o fundo entre os dois topos
        between_lows = [l for l in swing_l if prev_h < l < last_h]
        if between_lows:
            neck_low = lows[between_lows[-1]]
            # Verifica se os topos estão próximos (dentro da tolerância)
            if abs(highs[last_h] - highs[prev_h]) / highs[prev_h] < tolerancia:
                # Rompimento do neckline (fundo entre topos) é sinal de venda
                preco_entrada = neck_low
                sl = max(highs[last_h], highs[prev_h])
                altura = sl - neck_low
                tp = neck_low - altura
                return {
                    'padrao': 'DUPLO_TOPO',
                    'preco_entrada': preco_entrada,
                    'sl': sl,
                    'tp': tp,
                    'altura': altura
                }

    # Duplo Fundo: dois fundos próximos em preço (com um topo entre eles)
    last_l = swing_l[-1]
    prev_l = swing_l[-2] if len(swing_l) >= 2 else None
    if prev_l is not None:
        between_highs = [h for h in swing_h if prev_l < h < last_l]
        if between_highs:
            neck_high = highs[between_highs[-1]]
            if abs(lows[last_l] - lows[prev_l]) / lows[prev_l] < tolerancia:
                preco_entrada = neck_high
                sl = min(lows[last_l], lows[prev_l])
                altura = neck_high - sl
                tp = neck_high + altura
                return {
                    'padrao': 'DUPLO_FUNDO',
                    'preco_entrada': preco_entrada,
                    'sl': sl,
                    'tp': tp,
                    'altura': altura
                }
    return None

def detectar_ombro_cabeca_ombro(df, swing_janela=5, tolerancia=0.015):
    """
    Detecta Ombro-Cabeça-Ombro (baixista) e OCO Invertido (altista).
    """
    if len(df) < swing_janela * 5:
        return None

    highs = df['high'].values
    lows = df['low'].values
    closes = df['close'].values
    swing_h, swing_l = detectar_swings(df, swing_janela)
    if len(swing_h) < 3 or len(swing_l) < 3:
        return None

    # Ombro-Cabeça-Ombro: três topos, o do meio mais alto, dois ombros simétricos
    top3 = swing_h[-3:]  # últimos três topos
    if len(top3) == 3:
        left_shoulder = highs[top3[0]]
        head = highs[top3[1]]
        right_shoulder = highs[top3[2]]
        # Pescoço (linha de suporte) formada pelos dois fundos entre os ombros
        lows_between = [l for l in swing_l if top3[0] < l < top3[2]]
        if len(lows_between) >= 2:
            neck_start = lows[lows_between[0]]
            neck_end = lows[lows_between[-1]]
            neckline = min(neck_start, neck_end)  # simplificação

            if head > left_shoulder and head > right_shoulder and abs(left_shoulder - right_shoulder) / head < tolerancia:
                # Confirmar rompimento do neckline (fechamento abaixo)
                if closes[-1] < neckline:
                    altura = head - neckline
                    return {
                        'padrao': 'OCO',
                        'preco_entrada': neckline,
                        'sl': head,
                        'tp': neckline - altura,
                        'altura': altura
                    }

    # OCO Invertido (altista): três fundos, o do meio mais baixo
    bottom3 = swing_l[-3:]
    if len(bottom3) == 3:
        left_shoulder = lows[bottom3[0]]
        head = lows[bottom3[1]]
        right_shoulder = lows[bottom3[2]]
        highs_between = [h for h in swing_h if bottom3[0] < h < bottom3[2]]
        if len(highs_between) >= 2:
            neck_start = highs[highs_between[0]]
            neck_end = highs[highs_between[-1]]
            neckline = max(neck_start, neck_end)
            if head < left_shoulder and head < right_shoulder and abs(left_shoulder - right_shoulder) / abs(head) < tolerancia:
                if closes[-1] > neckline:
                    altura = neckline - head
                    return {
                        'padrao': 'OCO_INVERTIDO',
                        'preco_entrada': neckline,
                        'sl': head,
                        'tp': neckline + altura,
                        'altura': altura
                    }
    return None

def obter_suporte_resistencia(df, janela=50):
    """
    Retorna o suporte (mínimo) e resistência (máximo) recentes.
    """
    recent = df.iloc[-janela:]
    suporte = recent['low'].min()
    resistencia = recent['high'].max()
    close = df['close'].iloc[-1]
    return {
        'suporte': suporte,
        'resistencia': resistencia,
        'dist_suporte_pct': (close - suporte) / close * 100 if close != 0 else 0,
        'dist_resistencia_pct': (resistencia - close) / close * 100 if close != 0 else 0
    }