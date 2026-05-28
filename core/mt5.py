import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time
import requests
from datetime import datetime, timedelta
import os
import joblib
import shap

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression

from ai.features import criar_features, calcular_fibonacci
from ai.data import obter_dados_reais
from ai.patterns import (
    detectar_duplo_topo_fundo,
    detectar_ombro_cabeca_ombro,
)
from news.news_filter import analyze_news, obter_features_macro

# =========================================
# CONFIGURAÇÕES
# =========================================
SYMBOL = "XAUUSD.pro"
TIMEFRAME = mt5.TIMEFRAME_M15
LOTE_BASE = 0.01
RISCO_PERCENTUAL = 0.5          # % do saldo arriscado por trade
SPREAD_MAXIMO = 1.50
MAGIC = 20260526
TAMANHO_MIN_DATASET = 150
TAMANHO_LOTE_RETREINO = 20

# Limites diários
PERDA_MAX_DIA_PCT = 10.0
TRAILING_STOP_LUCRO_PCT = 5.0
MAX_TRADES_DIA = 0
PAUSA_APOS_STOP = 3600

# Parâmetros de entrada e proteção
MIN_RR_BASE = 1.5
ATIVAR_ORDENS_LIMITE = True
BREAKEVEN_ATIVAR = True
BREAKEVEN_PCT = 0.4
TRAILING_STOP_DIST_BASE = 1.5

RAILWAY_API = "https://robo-cloud-production.up.railway.app/update"

# =========================================
# INICIALIZAÇÃO MT5
# =========================================
if not mt5.initialize():
    print("❌ ERRO AO CONECTAR MT5")
    quit()
print("✅ MT5 CONECTADO")

# =========================================
# CARREGAR / CRIAR MODELO (com verificação de dimensão)
# =========================================
modelo_path = "modelo_ia.pkl"
features_path = "features_hist.npy"
labels_path = "labels_hist.npy"

dados_teste = obter_dados_reais(bars=200)
dados_h1_teste = obter_dados_reais(timeframe=mt5.TIMEFRAME_H1, bars=200) if len(dados_teste) >= 50 else None
dados_h4_teste = obter_dados_reais(timeframe=mt5.TIMEFRAME_H4, bars=200) if len(dados_teste) >= 50 else None
dados_d1_teste = obter_dados_reais(timeframe=mt5.TIMEFRAME_D1, bars=100) if len(dados_teste) >= 50 else None
dados_w1_teste = obter_dados_reais(timeframe=mt5.TIMEFRAME_W1, bars=50) if len(dados_teste) >= 50 else None
X_teste, _ = criar_features(dados_teste, dados_h1_teste, dados_h4_teste, dados_d1_teste, dados_w1_teste, SYMBOL)
num_features_atual = X_teste.shape[1]

recriar_modelo = True
if os.path.exists(modelo_path) and os.path.exists(features_path) and os.path.exists(labels_path):
    modelos_carregados = joblib.load(modelo_path)
    rf_carregado = modelos_carregados[0]
    if hasattr(rf_carregado, 'n_features_in_') and rf_carregado.n_features_in_ == num_features_atual:
        X_hist = np.load(features_path)
        y_hist = np.load(labels_path)
        modelos = modelos_carregados
        recriar_modelo = False
        print(f"📂 {len(X_hist)} exemplos anteriores carregados. Features compatíveis ({num_features_atual}).")
    else:
        print("⚠️ Modelo salvo com número diferente de features. Será retreinado.")
        for path in [modelo_path, features_path, labels_path]:
            if os.path.exists(path): os.remove(path)

if recriar_modelo:
    print("📥 Treinando modelo inicial...")
    data_m15 = obter_dados_reais(bars=500)
    data_h1 = obter_dados_reais(timeframe=mt5.TIMEFRAME_H1, bars=500) if len(data_m15) >= 50 else None
    data_h4 = obter_dados_reais(timeframe=mt5.TIMEFRAME_H4, bars=500) if len(data_m15) >= 50 else None
    data_d1 = obter_dados_reais(timeframe=mt5.TIMEFRAME_D1, bars=200) if len(data_m15) >= 50 else None
    data_w1 = obter_dados_reais(timeframe=mt5.TIMEFRAME_W1, bars=100) if len(data_m15) >= 50 else None
    if len(data_m15) < TAMANHO_MIN_DATASET:
        raise Exception("Dados insuficientes para treinar.")
    X, y = criar_features(data_m15, data_h1, data_h4, data_d1, data_w1, SYMBOL)
    X_hist = X
    y_hist = np.array(y)

    rf = RandomForestClassifier(n_estimators=300, max_depth=10, random_state=42)
    gb = GradientBoostingClassifier(n_estimators=200, learning_rate=0.05, random_state=42)
    lr = LogisticRegression(max_iter=2000, C=0.1, random_state=42)

    rf.fit(X_hist, y_hist)
    gb.fit(X_hist, y_hist)
    lr.fit(X_hist, y_hist)
    modelos = (rf, gb, lr)
    joblib.dump(modelos, modelo_path)
    np.save(features_path, X_hist)
    np.save(labels_path, y_hist)
    print("✅ Modelo inicial salvo.")

print("✅ IA PRONTA")

# Variáveis globais
trades_abertos = []
novos_exemplos = 0
saldo_inicio_dia = None
data_inicio_dia = None
pico_lucro_dia = 0.0
trades_dia = 0
pausado_ate = None

# =========================================
# FUNÇÕES DE MERCADO
# =========================================
def obter_dados(symbol=SYMBOL, timeframe=TIMEFRAME, barras=500):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, barras)
    if rates is None:
        return pd.DataFrame()
    df = pd.DataFrame(rates)
    if len(df) == 0:
        return pd.DataFrame()
    df["time"] = pd.to_datetime(df["time"], unit="s")
    return df

def obter_sessao():
    hora = datetime.now().hour
    if 0 <= hora < 7:
        return "ASIA"
    elif 7 <= hora < 13:
        return "LONDRES"
    elif 13 <= hora < 17:
        return "NOVA YORK"
    return "AFTER"

def obter_tendencia(df):
    ema20 = df["close"].ewm(span=20).mean()
    ema50 = df["close"].ewm(span=50).mean()
    if ema20.iloc[-1] > ema50.iloc[-1]:
        return "COMPRA"
    elif ema20.iloc[-1] < ema50.iloc[-1]:
        return "VENDA"
    return "WAIT"

def calcular_atr(df, periodo=14):
    high_low = df["high"] - df["low"]
    high_close = np.abs(df["high"] - df["close"].shift())
    low_close = np.abs(df["low"] - df["close"].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    atr = pd.Series(true_range).rolling(periodo).mean()
    return atr.iloc[-1]

def possui_posicao():
    posicoes = mt5.positions_get(symbol=SYMBOL)
    if posicoes is None:
        return False
    return len(posicoes) > 0

def enviar_ordem_mercado(sinal, sl, tp, lote):
    tick = mt5.symbol_info_tick(SYMBOL)
    if tick is None:
        print("❌ SEM TICK")
        return None
    preco = tick.ask if sinal == "COMPRA" else tick.bid
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": SYMBOL,
        "volume": lote,
        "type": mt5.ORDER_TYPE_BUY if sinal == "COMPRA" else mt5.ORDER_TYPE_SELL,
        "price": preco,
        "sl": sl,
        "tp": tp,
        "deviation": 20,
        "magic": MAGIC,
        "comment": "ROBO_IA_XAUUSD",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    resultado = mt5.order_send(request)
    print(f"📈 ORDEM MERCADO {sinal} | Lote: {lote} | SL: {sl:.2f} | TP: {tp:.2f}")
    if resultado.retcode == mt5.TRADE_RETCODE_DONE:
        return resultado.order
    else:
        print(f"❌ Erro: {resultado.comment}")
        return None

def enviar_ordem_limite(sinal, preco_limite, sl, tp, lote):
    request = {
        "action": mt5.TRADE_ACTION_PENDING,
        "symbol": SYMBOL,
        "volume": lote,
        "type": mt5.ORDER_TYPE_BUY_LIMIT if sinal == "COMPRA" else mt5.ORDER_TYPE_SELL_LIMIT,
        "price": preco_limite,
        "sl": sl,
        "tp": tp,
        "deviation": 20,
        "magic": MAGIC,
        "comment": "ROBO_IA_XAUUSD_PADRAO",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    resultado = mt5.order_send(request)
    print(f"📉 ORDEM LIMITE {sinal} @ {preco_limite:.2f} | Lote: {lote} | SL: {sl:.2f} | TP: {tp:.2f}")
    if resultado.retcode == mt5.TRADE_RETCODE_DONE:
        return resultado.order
    else:
        print(f"❌ Erro: {resultado.comment}")
        return None

def executar_ordem_normal(sinal, sl, tp, lote, fib_confirm, preco_fibo):
    if fib_confirm and ATIVAR_ORDENS_LIMITE and preco_fibo:
        tick = mt5.symbol_info_tick(SYMBOL)
        if tick is None:
            return None
        preco = tick.ask if sinal == "COMPRA" else tick.bid
        if (sinal == "COMPRA" and preco_fibo <= preco) or (sinal == "VENDA" and preco_fibo >= preco):
            return enviar_ordem_limite(sinal, preco_fibo, sl, tp, lote)
        else:
            return enviar_ordem_mercado(sinal, sl, tp, lote)
    else:
        return enviar_ordem_mercado(sinal, sl, tp, lote)

def enviar_dashboard(dados):
    try:
        requests.post(RAILWAY_API, json=dados, timeout=15)
    except:
        pass

# =========================================
# MÉTRICAS DA CONTA E RISCO
# =========================================
def obter_info_conta():
    conta = mt5.account_info()
    if conta is None:
        return 1000, 1000, 0.0, 100.0
    return conta.balance, conta.equity, conta.profit, conta.margin_level if conta.margin_level else 100.0

def obter_winrate():
    data_inicial = datetime.now() - timedelta(days=30)
    ordens = mt5.history_orders_get(data_inicial, datetime.now())
    if not ordens:
        return 0.0, 0.0, 0.0
    profits = []
    for o in ordens:
        if getattr(o, 'magic', 0) == MAGIC and getattr(o, 'state', 0) == mt5.ORDER_STATE_FILLED:
            profits.append(getattr(o, 'profit', 0))
    if not profits:
        return 0.0, 0.0, 0.0
    wins = [p for p in profits if p > 0]
    losses = [p for p in profits if p < 0]
    winrate = len(wins) / len(profits)
    avg_win = sum(wins) / len(wins) if wins else 0.0
    avg_loss = abs(sum(losses) / len(losses)) if losses else 0.0
    return winrate, avg_win, avg_loss

def obter_risco_atual(risco_base):
    if saldo_inicio_dia is None or saldo_inicio_dia == 0:
        return risco_base
    lucro_dia = obter_lucro_dia()
    drawdown_pct = (lucro_dia / saldo_inicio_dia) * 100 if lucro_dia < 0 else 0
    if drawdown_pct < -5:
        risco_base *= 0.5
    if drawdown_pct < -8:
        risco_base *= 0.5
    if drawdown_pct <= -PERDA_MAX_DIA_PCT * 0.9:
        risco_base = 0.0
    return risco_base

def obter_lucro_dia():
    if saldo_inicio_dia is None:
        return 0.0
    _, equity, _, _ = obter_info_conta()
    return equity - saldo_inicio_dia

def pode_operar():
    global pico_lucro_dia, pausado_ate
    agora = datetime.now()
    if pausado_ate and agora < pausado_ate:
        restante = (pausado_ate - agora).seconds // 60
        return False, f"⏳ Pausa por mais {restante} min"

    lucro_dia = obter_lucro_dia()
    saldo_ref = saldo_inicio_dia if saldo_inicio_dia else 1000

    if lucro_dia > pico_lucro_dia:
        pico_lucro_dia = lucro_dia

    if PERDA_MAX_DIA_PCT > 0 and saldo_ref > 0:
        perda_pct = (lucro_dia / saldo_ref) * 100
        if perda_pct <= -PERDA_MAX_DIA_PCT:
            pausado_ate = agora + timedelta(seconds=PAUSA_APOS_STOP)
            return False, f"🛑 Perda máxima diária ({PERDA_MAX_DIA_PCT}%): {perda_pct:.1f}%"

    if TRAILING_STOP_LUCRO_PCT > 0 and pico_lucro_dia > 0 and saldo_ref > 0:
        recuo = pico_lucro_dia - lucro_dia
        recuo_pct = (recuo / saldo_ref) * 100
        if recuo_pct >= TRAILING_STOP_LUCRO_PCT:
            pausado_ate = agora + timedelta(seconds=PAUSA_APOS_STOP)
            return False, f"🏁 Trailing stop diário: recuo {recuo_pct:.1f}%"

    if MAX_TRADES_DIA > 0 and trades_dia >= MAX_TRADES_DIA:
        return False, f"🔢 Limite de {MAX_TRADES_DIA} trades diários"

    return True, "✅ Liberado"

def verificar_novo_dia():
    global saldo_inicio_dia, data_inicio_dia, pico_lucro_dia, trades_dia, pausado_ate
    agora = datetime.now()
    hoje = agora.date()
    if data_inicio_dia is None or hoje != data_inicio_dia:
        _, equity, _, _ = obter_info_conta()
        saldo_inicio_dia = equity
        data_inicio_dia = hoje
        pico_lucro_dia = 0.0
        trades_dia = 0
        pausado_ate = None
        print(f"🌅 Novo dia! Equity inicial: ${saldo_inicio_dia:.2f}")

# =========================================
# GERENCIAMENTO DE POSIÇÕES (TRAILING STOP IA)
# =========================================
def gerenciar_posicoes(confianca_ia, atr_atual):
    posicoes = mt5.positions_get(symbol=SYMBOL)
    if posicoes is None:
        return

    for pos in posicoes:
        if pos.magic != MAGIC:
            continue

        tick = mt5.symbol_info_tick(SYMBOL)
        if tick is None:
            continue

        if pos.type == mt5.POSITION_TYPE_BUY:
            preco_atual = tick.bid
            sl_atual = pos.sl
            tp = pos.tp
            preco_entrada = pos.price_open
            direcao = 1
        else:
            preco_atual = tick.ask
            sl_atual = pos.sl
            tp = pos.tp
            preco_entrada = pos.price_open
            direcao = -1

        if preco_atual == 0 or tp == 0 or atr_atual == 0:
            continue

        tp_dist = abs(tp - preco_entrada)
        if direcao == 1:
            lucro_pontos = preco_atual - preco_entrada
        else:
            lucro_pontos = preco_entrada - preco_atual

        percentual_tp = (lucro_pontos / tp_dist) if tp_dist > 0 else 0

        # ----- BREAKEVEN -----
        if BREAKEVEN_ATIVAR and percentual_tp >= BREAKEVEN_PCT and sl_atual != preco_entrada:
            print(f"⚖️ Breakeven ativado para posição #{pos.ticket}. SL → {preco_entrada:.2f}")
            mt5.PositionModify(pos.ticket, sl=preco_entrada, tp=pos.tp)

        # ----- TRAILING STOP INTELIGENTE (IA) -----
        if percentual_tp >= BREAKEVEN_PCT:
            base_dist = atr_atual * TRAILING_STOP_DIST_BASE
            if (direcao == 1 and confianca_ia > 0.6) or (direcao == -1 and confianca_ia < 0.4):
                fator_confianca = 0.7
            elif (direcao == 1 and confianca_ia < 0.4) or (direcao == -1 and confianca_ia > 0.6):
                fator_confianca = 1.3
            else:
                fator_confianca = 1.0

            ts_dist = base_dist * fator_confianca

            if direcao == 1:
                novo_sl = preco_atual - ts_dist
                if novo_sl > sl_atual and novo_sl > preco_entrada:
                    print(f"📈 Trailing stop IA (conf={confianca_ia:.2f}) → SL: {novo_sl:.2f}")
                    mt5.PositionModify(pos.ticket, sl=novo_sl, tp=pos.tp)
            else:
                novo_sl = preco_atual + ts_dist
                if novo_sl < sl_atual and novo_sl < preco_entrada:
                    print(f"📉 Trailing stop IA (conf={confianca_ia:.2f}) → SL: {novo_sl:.2f}")
                    mt5.PositionModify(pos.ticket, sl=novo_sl, tp=pos.tp)

# =========================================
# APRENDIZADO
# =========================================
def verificar_trades_fechados():
    global X_hist, y_hist, novos_exemplos, modelos, trades_abertos
    for trade in list(trades_abertos):
        if trade['ticket'] is None:
            continue
        ordem = mt5.orders_get(ticket=trade['ticket'])
        if ordem is None or len(ordem) == 0:
            trades_abertos.remove(trade)
            continue
        ordem = ordem[0]
        if ordem.state == mt5.ORDER_STATE_FILLED:
            label = 1 if ordem.profit > 0 else 0
            feat = trade['features'].reshape(1, -1)
            if X_hist.size == 0:
                X_hist = feat
                y_hist = np.array([label])
            else:
                X_hist = np.vstack([X_hist, feat])
                y_hist = np.append(y_hist, label)
            novos_exemplos += 1
            trades_abertos.remove(trade)
            print(f"📚 Trade {trade['ticket']} registrado: label={label}")
            if novos_exemplos >= TAMANHO_LOTE_RETREINO:
                print("🔄 Retreando modelo...")
                rf, gb, lr = modelos
                rf.fit(X_hist, y_hist)
                gb.fit(X_hist, y_hist)
                lr.fit(X_hist, y_hist)
                joblib.dump(modelos, modelo_path)
                np.save(features_path, X_hist)
                np.save(labels_path, y_hist)
                print("✅ Modelo atualizado.")
                novos_exemplos = 0

def prever_com_modelo(features):
    rf, gb, lr = modelos
    p1 = rf.predict_proba([features])[0][1]
    p2 = gb.predict_proba([features])[0][1]
    p3 = lr.predict_proba([features])[0][1]
    prob = (p1 + p2 + p3) / 3
    if prob > 0.60:
        sinal = "COMPRA"
    elif prob < 0.40:
        sinal = "VENDA"
    else:
        sinal = "WAIT"
    return {"signal": sinal, "probability_up": prob, "probability_down": 1 - prob}

# =========================================
# LOOP PRINCIPAL
# =========================================
while True:
    try:
        print("\n================================\n🤖 ROBO IA XAU/USD (FULL)\n================================")
        verificar_trades_fechados()

        verificar_novo_dia()
        pode, motivo = pode_operar()
        print("🔍", motivo)

        sessao = obter_sessao()
        print("⏰ SESSÃO:", sessao)

        # Dados de mercado (todos os timeframes)
        df = obter_dados()
        if len(df) < 100:
            print("❌ DADOS INSUFICIENTES")
            time.sleep(10)
            continue

        df_h1 = obter_dados(timeframe=mt5.TIMEFRAME_H1, barras=500)
        df_h4 = obter_dados(timeframe=mt5.TIMEFRAME_H4, barras=500)
        df_d1 = obter_dados(timeframe=mt5.TIMEFRAME_D1, barras=500)
        df_w1 = obter_dados(timeframe=mt5.TIMEFRAME_W1, barras=300)

        if len(df_h1) < 50: df_h1 = None
        if len(df_h4) < 50: df_h4 = None
        if len(df_d1) < 50: df_d1 = None
        if len(df_w1) < 30: df_w1 = None

        tendencia = obter_tendencia(df)
        atr = calcular_atr(df)
        print("📊 ATR:", atr)

        tick = mt5.symbol_info_tick(SYMBOL)
        if tick:
            preco = tick.ask
            spread = tick.ask - tick.bid
        else:
            preco, spread = 0, 0

        # Features e previsão IA
        X_novo, _ = criar_features(df, df_h1, df_h4, df_d1, df_w1, SYMBOL)
        if hasattr(X_novo, 'iloc'):
            features_atuais = X_novo.iloc[-1:].values.flatten()
        else:
            features_atuais = X_novo[-1]

        resultado_ia = prever_com_modelo(features_atuais)
        sinal_ia = resultado_ia["signal"]
        confianca_prob = resultado_ia["probability_up"]
        confianca = round(confianca_prob * 100, 2)

        # Gerenciamento de posições abertas (trailing stop IA)
        gerenciar_posicoes(confianca_prob, atr)

        # Fibonacci (M15)
        fib_data = calcular_fibonacci(df)
        fib_confirm = False
        sl_fibo = tp_fibo = preco_fibo = None
        if fib_data and sinal_ia == "COMPRA":
            dist_618 = abs(fib_data['distancias']['fib_618_dist'])
            dist_382 = abs(fib_data['distancias']['fib_382_dist'])
            if dist_618 < 0.05 or dist_382 < 0.03:
                fib_confirm = True
                preco_fibo = fib_data['niveis']['618'] if dist_618 <= dist_382 else fib_data['niveis']['382']
                sl_fibo = fib_data['niveis']['786']
                tp_fibo = fib_data['niveis']['100']
        elif fib_data and sinal_ia == "VENDA":
            dist_618 = abs(fib_data['distancias']['fib_618_dist'])
            dist_382 = abs(fib_data['distancias']['fib_382_dist'])
            if dist_618 < 0.05 or dist_382 < 0.03:
                fib_confirm = True
                preco_fibo = fib_data['niveis']['618'] if dist_618 <= dist_382 else fib_data['niveis']['382']
                sl_fibo = fib_data['niveis']['786']
                tp_fibo = fib_data['niveis']['100']

        # Detecção de padrões gráficos em H4, D1, W1
        padrao_info = None
        padrao_tf = None
        for tf, df_tf in [('W1', df_w1), ('D1', df_d1), ('H4', df_h4)]:
            if df_tf is None or len(df_tf) < 50:
                continue
            padrao = detectar_duplo_topo_fundo(df_tf) or detectar_ombro_cabeca_ombro(df_tf)
            if padrao:
                padrao_info = padrao
                padrao_tf = tf
                break

        # Notícias de curto prazo
        noticias = analyze_news()
        if noticias is None:
            noticias = {"has_high_impact": False, "event": "NENHUMA", "news_signal": "NEUTRAL"}
        evento_noticia = noticias.get("event", "NENHUMA")
        tem_alto_impacto = noticias.get("has_high_impact", False)
        sinal_noticia = noticias.get("news_signal", "NEUTRAL")

        # Scores
        pontos_compra = 0
        pontos_venda = 0
        motivos = []
        if tendencia == "COMPRA":
            pontos_compra += 1
            motivos.append("Tendência de alta (M15)")
        elif tendencia == "VENDA":
            pontos_venda += 1
            motivos.append("Tendência de baixa (M15)")

        if sinal_ia == "COMPRA":
            pontos_compra += 1
            motivos.append(f"IA compra ({confianca}%)")
        elif sinal_ia == "VENDA":
            pontos_venda += 1
            motivos.append(f"IA venda ({confianca}%)")

        if confianca > 60:
            pontos_compra += 1
        elif confianca < 40:
            pontos_venda += 1

        if fib_confirm:
            pontos_compra += 1 if sinal_ia == "COMPRA" else 0
            pontos_venda += 1 if sinal_ia == "VENDA" else 0
            motivos.append("Confirmação Fibonacci (M15)")

        if padrao_info:
            if padrao_info['padrao'] in ['DUPLO_FUNDO', 'OCO_INVERTIDO']:
                pontos_compra += 2
                motivos.append(f"Padrão {padrao_info['padrao']} no {padrao_tf} (reversão altista)")
            else:
                pontos_venda += 2
                motivos.append(f"Padrão {padrao_info['padrao']} no {padrao_tf} (reversão baixista)")

        if sinal_noticia == "COMPRA":
            pontos_compra += 1
            motivos.append(f"Notícia USD ({evento_noticia}) favorece COMPRA")
        elif sinal_noticia == "VENDA":
            pontos_venda += 1
            motivos.append(f"Notícia USD ({evento_noticia}) favorece VENDA")
        elif tem_alto_impacto:
            motivos.append(f"⚠️ Notícia de alto impacto: {evento_noticia} (neutra)")

        # Cálculo de SL/TP e lote
        saldo, equity, _, _ = obter_info_conta()
        risco_percent = obter_risco_atual(RISCO_PERCENTUAL)
        valor_risco = saldo * (risco_percent / 100)

        usar_padrao = padrao_info is not None
        if not usar_padrao:
            if fib_confirm and sl_fibo and tp_fibo:
                sl_dist = abs(preco - sl_fibo) if not preco_fibo else abs(preco_fibo - sl_fibo)
                tp_dist = abs(tp_fibo - (preco_fibo if preco_fibo else preco))
            else:
                multi_sl = 2.0
                multi_tp = 4.0
                if confianca > 75:
                    multi_sl = 1.8
                    multi_tp = 5.0
                elif confianca < 45:
                    multi_sl = 2.5
                    multi_tp = 3.0
                sl_dist = atr * multi_sl
                tp_dist = atr * multi_tp
                sl_fibo = preco - sl_dist if sinal_ia == "COMPRA" else preco + sl_dist
                tp_fibo = preco + tp_dist if sinal_ia == "COMPRA" else preco - tp_dist

            if sl_dist > 0:
                rr_atual = tp_dist / sl_dist
                min_rr = MIN_RR_BASE
                if confianca < 60:
                    min_rr = MIN_RR_BASE * 1.3
                if rr_atual < min_rr:
                    print(f"⚠️ RR insuficiente ({rr_atual:.2f}:1 < {min_rr}:1). Entrada ignorada.")
                    lote_dinamico = 0
                else:
                    lote_dinamico = valor_risco / sl_dist
            else:
                lote_dinamico = 0
        else:
            # Usa níveis do padrão gráfico
            sl_final = padrao_info['sl']
            tp_final = padrao_info['tp']
            preco_padrao = padrao_info.get('preco_entrada', preco)
            sl_dist = abs(preco_padrao - sl_final)
            tp_dist = abs(tp_final - preco_padrao)

            if sl_dist > 0:
                rr_atual = tp_dist / sl_dist
                min_rr = MIN_RR_BASE * 0.8
                if rr_atual < min_rr:
                    print(f"⚠️ RR insuficiente no padrão ({rr_atual:.2f}:1). Entrada ignorada.")
                    lote_dinamico = 0
                else:
                    lote_dinamico = valor_risco / sl_dist
            else:
                lote_dinamico = 0

            lote_dinamico = max(LOTE_BASE, round(lote_dinamico * 0.5 / 0.01) * 0.01) if lote_dinamico > 0 else 0

        if lote_dinamico > 0:
            lote_dinamico = max(LOTE_BASE, min(1.0, round(lote_dinamico / 0.01) * 0.01))

        if tem_alto_impacto and lote_dinamico > 0:
            lote_dinamico *= 0.5
            lote_dinamico = max(LOTE_BASE, round(lote_dinamico / 0.01) * 0.01)

        spread_ok = spread <= SPREAD_MAXIMO
        if not spread_ok:
            motivos.append("⚠️ Spread alto")
            lote_dinamico = 0

        texto_motivo = "; ".join(motivos) if motivos else "Sem sinal"
        lucro_dia = obter_lucro_dia()
        winrate, _, _ = obter_winrate()
        resumo_diario = f"PnL dia: ${lucro_dia:.2f} ({((lucro_dia/saldo_inicio_dia)*100 if saldo_inicio_dia else 0):.1f}%) | Trades: {trades_dia}"

        # Explicação SHAP
        try:
            gb = modelos[1]
            explainer = shap.TreeExplainer(gb)
            shap_vals = explainer.shap_values(features_atuais.reshape(1, -1))
            if isinstance(shap_vals, list):
                vals = shap_vals[1][0]
            else:
                vals = shap_vals[0]
            # Nomes das features (simplificado, use os primeiros)
            feature_names = [
                "close","return","volatility","trend","trend_strength","momentum",
                "fib_0_dist","fib_236_dist","fib_382_dist","fib_500_dist",
                "fib_618_dist","fib_786_dist","fib_100_dist","fib_1618_dist",
                "tick_volume","tick_volume_ratio","rsi","macd","adx","plus_di",
                "minus_di","bb_position","bb_width","stoch_k","stoch_d",
                "dist_sma50","dist_sma200",
                "news_15m","news_30m","news_60m","news_240m",
                "news_next_time","news_high_impact","news_direction_signal",
                "macro_events_12h","macro_events_24h","macro_events_72h","macro_events_168h",
                "macro_buy_signals","macro_sell_signals","macro_days_to_next_event","macro_next_direction"
            ]
            contribs = sorted(zip(feature_names[:len(vals)], vals), key=lambda x: abs(x[1]), reverse=True)
            explicacao = "🧠 Influências SHAP:\n"
            for nome, valor in contribs[:8]:
                direcao = "↑" if valor > 0 else "↓"
                explicacao += f"  {nome}: {direcao} ({valor:+.4f})\n"
        except Exception as e:
            explicacao = f"SHAP indisponível: {e}"

        risco_label = "ALTO" if atr > 10 else "MODERADO" if atr > 5 else "BAIXO"
        analise = f"""
📊 MERCADO
Tendência: {tendencia}
Sinal IA: {sinal_ia} ({confianca}%)
Notícia: {evento_noticia}
ATR: {atr:.2f} | Spread: {spread:.5f}
Sessão: {sessao} | Risco: {risco_label}
Lote: {lote_dinamico}
Motivo: {texto_motivo}
{resumo_diario}
Winrate (30d): {winrate*100:.1f}%
{explicacao}
"""
        dados_dashboard = {
            "signal": sinal_ia,
            "confidence": confianca,
            "market": tendencia,
            "price": preco,
            "atr": round(atr, 2),
            "spread": round(spread, 5),
            "news": evento_noticia,
            "session": sessao,
            "analysis": analise,
            "reason": texto_motivo,
            "buy_score": pontos_compra,
            "sell_score": pontos_venda,
            "winrate": round(winrate * 100, 1),
            "trades": trades_dia,
            "pnl": f"${lucro_dia:.2f}"
        }
        enviar_dashboard(dados_dashboard)

        if not possui_posicao() and pode and lote_dinamico > 0 and spread_ok:
            sinal_entrada = None
            if pontos_compra >= 3:
                sinal_entrada = "COMPRA"
            elif pontos_venda >= 3:
                sinal_entrada = "VENDA"

            if sinal_entrada:
                if usar_padrao:
                    sl_final = padrao_info['sl']
                    tp_final = padrao_info['tp']
                    preco_padrao = padrao_info.get('preco_entrada', preco)
                    if (sinal_entrada == "COMPRA" and padrao_info['padrao'] in ['DUPLO_FUNDO', 'OCO_INVERTIDO']) or \
                       (sinal_entrada == "VENDA" and padrao_info['padrao'] in ['DUPLO_TOPO', 'OCO']):
                        if ATIVAR_ORDENS_LIMITE:
                            if (sinal_entrada == "COMPRA" and preco_padrao <= preco) or (sinal_entrada == "VENDA" and preco_padrao >= preco):
                                ticket = enviar_ordem_limite(sinal_entrada, preco_padrao, sl_final, tp_final, lote_dinamico)
                            else:
                                ticket = enviar_ordem_mercado(sinal_entrada, sl_final, tp_final, lote_dinamico)
                        else:
                            ticket = enviar_ordem_mercado(sinal_entrada, sl_final, tp_final, lote_dinamico)
                    else:
                        ticket = executar_ordem_normal(sinal_entrada, sl_fibo, tp_fibo, lote_dinamico, fib_confirm, preco_fibo)
                else:
                    ticket = executar_ordem_normal(sinal_entrada, sl_fibo, tp_fibo, lote_dinamico, fib_confirm, preco_fibo)

                if ticket:
                    trades_dia += 1
                    trades_abertos.append({
                        'features': features_atuais,
                        'sinal': sinal_entrada,
                        'ticket': ticket,
                        'tipo': 'padrao' if usar_padrao else 'normal'
                    })
                    print(f"📌 Trade {ticket} registrado. Trades hoje: {trades_dia}")
        else:
            if not pode:
                print("❌ " + motivo)
            elif lote_dinamico == 0:
                print("❌ Lote zerado (risco/bloqueio)")
            else:
                print("⚠️ POSIÇÃO ABERTA")

        time.sleep(30)

    except Exception as e:
        print("❌ ERRO NO LOOP:", e)
        time.sleep(10)