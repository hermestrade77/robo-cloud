import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time, requests, os, joblib
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import shap

from ai.features import criar_features, calcular_fibonacci, FEATURES_COMPLETAS
from ai.data import obter_dados_reais
from ai.patterns import detectar_duplo_topo_fundo, detectar_ombro_cabeca_ombro
from news.news_filter import analyze_news, obter_features_macro

# ========== CONFIGURAÇÕES ==========
SYMBOL = "XAUUSD.pro"
TIMEFRAME = mt5.TIMEFRAME_M15
LOTE_BASE = 0.01
RISCO_PERCENTUAL = 0.5
SPREAD_MAXIMO = 1.50
MAGIC = 20260526
TAMANHO_MIN_DATASET = 150
TAMANHO_LOTE_RETREINO = 20
PERDA_MAX_DIA_PCT = 10.0
TRAILING_STOP_LUCRO_PCT = 5.0
MAX_TRADES_DIA = 0
PAUSA_APOS_STOP = 3600
MIN_RR_BASE = 1.2
ATIVAR_ORDENS_LIMITE = True
BREAKEVEN_ATIVAR = True
BREAKEVEN_PCT = 0.4
TRAILING_STOP_DIST_BASE = 1.5
RAILWAY_API = "https://robo-cloud-production.up.railway.app/update"

# ========== CONEXÃO MT5 ==========
if not mt5.initialize():
    print("❌ ERRO AO CONECTAR MT5")
    quit()
print("✅ MT5 CONECTADO")

# ========== CARREGAR / CRIAR MODELO (com reset e scaler) ==========
modelo_path = "modelo_ia.pkl"
features_path = "features_hist.npy"
labels_path = "labels_hist.npy"

# Remove arquivos antigos para garantir recriação limpa
for path in [modelo_path, features_path, labels_path]:
    if os.path.exists(path):
        os.remove(path)
        print(f"🗑️  Removido {path}")

print("📥 Treinando modelo com as novas features...")
data_m15 = obter_dados_reais(bars=500)
data_h1 = obter_dados_reais(timeframe=mt5.TIMEFRAME_H1, bars=500) if len(data_m15) >= 50 else None
data_h4 = obter_dados_reais(timeframe=mt5.TIMEFRAME_H4, bars=500) if len(data_m15) >= 50 else None
data_d1 = obter_dados_reais(timeframe=mt5.TIMEFRAME_D1, bars=200) if len(data_m15) >= 50 else None
data_w1 = obter_dados_reais(timeframe=mt5.TIMEFRAME_W1, bars=100) if len(data_m15) >= 50 else None

if len(data_m15) < TAMANHO_MIN_DATASET:
    raise Exception("Dados insuficientes para treinar.")

X, y = criar_features(data_m15, data_h1, data_h4, data_d1, data_w1, SYMBOL)
print(f"🔢 Features geradas: {X.shape[1]} colunas, {len(y)} amostras")
X_hist = X
y_hist = np.array(y)

# Escala os dados para melhor convergência
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_hist)

rf = RandomForestClassifier(n_estimators=300, max_depth=10, random_state=42, n_jobs=-1)
gb = GradientBoostingClassifier(n_estimators=200, learning_rate=0.05, random_state=42)
lr = LogisticRegression(max_iter=5000, C=0.1, random_state=42, solver='saga')

rf.fit(X_scaled, y_hist)
gb.fit(X_scaled, y_hist)
lr.fit(X_scaled, y_hist)
modelos = (rf, gb, lr)

joblib.dump((modelos, scaler), modelo_path)
np.save(features_path, X_hist)
np.save(labels_path, y_hist)
print("✅ Modelo inicial treinado e salvo com sucesso.")
print("✅ IA PRONTA")

trades_abertos = []
novos_exemplos = 0
saldo_inicio_dia = None
data_inicio_dia = None
pico_lucro_dia = 0.0
trades_dia = 0
pausado_ate = None

# ========== FUNÇÕES AUXILIARES ==========
def obter_dados(symbol=SYMBOL, timeframe=TIMEFRAME, barras=500):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, barras)
    if rates is None: return pd.DataFrame()
    df = pd.DataFrame(rates)
    if len(df)==0: return pd.DataFrame()
    df["time"] = pd.to_datetime(df["time"], unit="s")
    return df

def obter_sessao():
    h = datetime.now().hour
    if h<7: return "ASIA"
    elif h<13: return "LONDRES"
    elif h<17: return "NOVA YORK"
    return "AFTER"

def obter_tendencia(df):
    ema20 = df["close"].ewm(span=20).mean()
    ema50 = df["close"].ewm(span=50).mean()
    if ema20.iloc[-1] > ema50.iloc[-1]: return "COMPRA"
    elif ema20.iloc[-1] < ema50.iloc[-1]: return "VENDA"
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
    pos = mt5.positions_get(symbol=SYMBOL)
    return pos is not None and len(pos)>0

def enviar_ordem_mercado(sinal, sl, tp, lote):
    tick = mt5.symbol_info_tick(SYMBOL)
    if tick is None: return None
    preco = tick.ask if sinal=="COMPRA" else tick.bid
    req = {
        "action": mt5.TRADE_ACTION_DEAL, "symbol": SYMBOL, "volume": lote,
        "type": mt5.ORDER_TYPE_BUY if sinal=="COMPRA" else mt5.ORDER_TYPE_SELL,
        "price": preco, "sl": sl, "tp": tp, "deviation": 20, "magic": MAGIC,
        "comment": "ROBO_IA", "type_time": mt5.ORDER_TIME_GTC, "type_filling": mt5.ORDER_FILLING_IOC
    }
    res = mt5.order_send(req)
    print(f"📈 MERCADO {sinal} | Lote {lote} | SL {sl:.2f} | TP {tp:.2f}")
    return res.order if res.retcode==mt5.TRADE_RETCODE_DONE else None

def enviar_ordem_limite(sinal, preco_limite, sl, tp, lote):
    req = {
        "action": mt5.TRADE_ACTION_PENDING, "symbol": SYMBOL, "volume": lote,
        "type": mt5.ORDER_TYPE_BUY_LIMIT if sinal=="COMPRA" else mt5.ORDER_TYPE_SELL_LIMIT,
        "price": preco_limite, "sl": sl, "tp": tp, "deviation": 20, "magic": MAGIC,
        "comment": "ROBO_IA_LIMIT", "type_time": mt5.ORDER_TIME_GTC, "type_filling": mt5.ORDER_FILLING_IOC
    }
    res = mt5.order_send(req)
    print(f"📉 LIMITE {sinal} @ {preco_limite:.2f} | Lote {lote} | SL {sl:.2f} | TP {tp:.2f}")
    return res.order if res.retcode==mt5.TRADE_RETCODE_DONE else None

def executar_ordem_normal(sinal, sl, tp, lote, fib_confirm, preco_fibo):
    if fib_confirm and ATIVAR_ORDENS_LIMITE and preco_fibo:
        tick = mt5.symbol_info_tick(SYMBOL)
        if tick is None: return None
        preco = tick.ask if sinal=="COMPRA" else tick.bid
        if (sinal=="COMPRA" and preco_fibo<=preco) or (sinal=="VENDA" and preco_fibo>=preco):
            return enviar_ordem_limite(sinal, preco_fibo, sl, tp, lote)
    return enviar_ordem_mercado(sinal, sl, tp, lote)

def enviar_dashboard(dados):
    try:
        requests.post(RAILWAY_API, json=dados, timeout=15)
    except Exception as e:
        print(f"❌ Erro ao enviar dashboard: {e}")

def obter_info_conta():
    c = mt5.account_info()
    if c is None: return 1000,1000,0.0,100.0
    return c.balance, c.equity, c.profit, c.margin_level or 100.0

def obter_winrate():
    ini = datetime.now() - timedelta(days=30)
    ordens = mt5.history_orders_get(ini, datetime.now())
    if not ordens: return 0.0,0.0,0.0
    profits = [getattr(o,'profit',0) for o in ordens if getattr(o,'magic',0)==MAGIC and getattr(o,'state',0)==mt5.ORDER_STATE_FILLED]
    if not profits: return 0.0,0.0,0.0
    wins = [p for p in profits if p>0]
    losses = [p for p in profits if p<0]
    wr = len(wins)/len(profits)
    aw = sum(wins)/len(wins) if wins else 0.0
    al = abs(sum(losses)/len(losses)) if losses else 0.0
    return wr, aw, al

def obter_risco_atual(risco_base):
    if saldo_inicio_dia is None: return risco_base
    lucro = obter_lucro_dia()
    dd = (lucro/saldo_inicio_dia)*100 if lucro<0 else 0
    if dd<-5: risco_base*=0.5
    if dd<-8: risco_base*=0.5
    if dd<=-PERDA_MAX_DIA_PCT*0.9: risco_base=0.0
    return risco_base

def obter_lucro_dia():
    if saldo_inicio_dia is None: return 0.0
    _, eq, _, _ = obter_info_conta()
    return eq - saldo_inicio_dia

def pode_operar():
    global pico_lucro_dia, pausado_ate
    agora = datetime.now()
    if pausado_ate and agora<pausado_ate:
        return False, f"⏳ Pausa até {pausado_ate.strftime('%H:%M')}"
    lucro = obter_lucro_dia()
    ref = saldo_inicio_dia or 1000
    if lucro>pico_lucro_dia: pico_lucro_dia=lucro
    if PERDA_MAX_DIA_PCT>0 and ref>0 and (lucro/ref)*100 <= -PERDA_MAX_DIA_PCT:
        pausado_ate = agora + timedelta(seconds=PAUSA_APOS_STOP)
        return False, f"🛑 Perda máxima diária atingida"
    if TRAILING_STOP_LUCRO_PCT>0 and pico_lucro_dia>0 and ref>0:
        recuo = (pico_lucro_dia - lucro)/ref*100
        if recuo >= TRAILING_STOP_LUCRO_PCT:
            pausado_ate = agora + timedelta(seconds=PAUSA_APOS_STOP)
            return False, f"🏁 Trailing stop diário"
    if MAX_TRADES_DIA>0 and trades_dia>=MAX_TRADES_DIA:
        return False, f"🔢 Limite de trades diários"
    return True, "✅ Liberado"

def verificar_novo_dia():
    global saldo_inicio_dia, data_inicio_dia, pico_lucro_dia, trades_dia, pausado_ate
    hoje = datetime.now().date()
    if data_inicio_dia is None or hoje!=data_inicio_dia:
        _, eq, _, _ = obter_info_conta()
        saldo_inicio_dia = eq
        data_inicio_dia = hoje
        pico_lucro_dia = 0.0
        trades_dia = 0
        pausado_ate = None
        print(f"🌅 Novo dia. Equity inicial: ${saldo_inicio_dia:.2f}")

def gerenciar_posicoes(conf_ia, atr_atual):
    for pos in mt5.positions_get(symbol=SYMBOL) or []:
        if pos.magic != MAGIC: continue
        tick = mt5.symbol_info_tick(SYMBOL)
        if tick is None: continue
        if pos.type==mt5.POSITION_TYPE_BUY:
            preco_atual = tick.bid; sl_atual=pos.sl; tp=pos.tp; entrada=pos.price_open; direc=1
        else:
            preco_atual = tick.ask; sl_atual=pos.sl; tp=pos.tp; entrada=pos.price_open; direc=-1
        if preco_atual==0 or tp==0 or atr_atual==0: continue
        tp_dist = abs(tp-entrada)
        lucro_pontos = (preco_atual-entrada) if direc==1 else (entrada-preco_atual)
        pct_tp = lucro_pontos/tp_dist if tp_dist>0 else 0
        if BREAKEVEN_ATIVAR and pct_tp>=BREAKEVEN_PCT and sl_atual!=entrada:
            print(f"⚖️ Breakeven pos #{pos.ticket}")
            mt5.PositionModify(pos.ticket, sl=entrada, tp=pos.tp)
        if pct_tp>=BREAKEVEN_PCT:
            base = atr_atual*TRAILING_STOP_DIST_BASE
            if (direc==1 and conf_ia>0.6) or (direc==-1 and conf_ia<0.4): fator=0.7
            elif (direc==1 and conf_ia<0.4) or (direc==-1 and conf_ia>0.6): fator=1.3
            else: fator=1.0
            ts_dist = base*fator
            if direc==1:
                novo_sl = preco_atual - ts_dist
                if novo_sl>sl_atual and novo_sl>entrada:
                    print(f"📈 Trailing IA → SL {novo_sl:.2f}")
                    mt5.PositionModify(pos.ticket, sl=novo_sl, tp=pos.tp)
            else:
                novo_sl = preco_atual + ts_dist
                if novo_sl<sl_atual and novo_sl<entrada:
                    print(f"📉 Trailing IA → SL {novo_sl:.2f}")
                    mt5.PositionModify(pos.ticket, sl=novo_sl, tp=pos.tp)

def verificar_trades_fechados():
    global X_hist, y_hist, novos_exemplos, modelos, trades_abertos, scaler
    for trade in list(trades_abertos):
        if trade['ticket'] is None: continue
        ordem = mt5.orders_get(ticket=trade['ticket'])
        if ordem is None or len(ordem)==0:
            trades_abertos.remove(trade); continue
        ordem = ordem[0]
        if ordem.state == mt5.ORDER_STATE_FILLED:
            label = 1 if ordem.profit>0 else 0
            feat = trade['features'].reshape(1,-1)
            if X_hist.size==0:
                X_hist, y_hist = feat, np.array([label])
            else:
                X_hist = np.vstack([X_hist, feat]); y_hist = np.append(y_hist, label)
            novos_exemplos += 1
            trades_abertos.remove(trade)
            print(f"📚 Trade {trade['ticket']} label={label}")
            if novos_exemplos >= TAMANHO_LOTE_RETREINO:
                print("🔄 Retreando modelo...")
                X_scaled = scaler.fit_transform(X_hist)
                rf,gb,lr = modelos
                rf.fit(X_scaled, y_hist); gb.fit(X_scaled, y_hist); lr.fit(X_scaled, y_hist)
                joblib.dump((modelos, scaler), modelo_path)
                np.save(features_path, X_hist); np.save(labels_path, y_hist)
                print("✅ Modelo atualizado."); novos_exemplos=0

def prever_com_modelo(features):
    features_scaled = scaler.transform([features])
    rf,gb,lr = modelos
    p = (rf.predict_proba(features_scaled)[0][1] + gb.predict_proba(features_scaled)[0][1] + lr.predict_proba(features_scaled)[0][1])/3
    if p>0.60: sinal="COMPRA"
    elif p<0.40: sinal="VENDA"
    else: sinal="WAIT"
    return {"signal":sinal,"probability_up":p,"probability_down":1-p}

# ========== LOOP PRINCIPAL ==========
while True:
    try:
        print("\n🤖 ROBO IA XAU/USD (FULL)")
        verificar_trades_fechados()
        verificar_novo_dia()
        pode, msg = pode_operar()
        print("🔍", msg)

        sessao = obter_sessao()
        df = obter_dados()
        if len(df)<100:
            print("❌ DADOS INSUFICIENTES"); time.sleep(10); continue

        df_h1 = obter_dados(timeframe=mt5.TIMEFRAME_H1, barras=500)
        df_h4 = obter_dados(timeframe=mt5.TIMEFRAME_H4, barras=500)
        df_d1 = obter_dados(timeframe=mt5.TIMEFRAME_D1, barras=500)
        df_w1 = obter_dados(timeframe=mt5.TIMEFRAME_W1, barras=300)
        if len(df_h1)<50: df_h1=None
        if len(df_h4)<50: df_h4=None
        if len(df_d1)<50: df_d1=None
        if len(df_w1)<30: df_w1=None

        tendencia = obter_tendencia(df)
        atr = calcular_atr(df)
        tick = mt5.symbol_info_tick(SYMBOL)
        preco = tick.ask if tick else 0
        spread = tick.ask-tick.bid if tick else 0

        X_novo, _ = criar_features(df, df_h1, df_h4, df_d1, df_w1, SYMBOL)
        feat = X_novo[-1]
        res_ia = prever_com_modelo(feat)
        sinal_ia = res_ia['signal']
        prob = res_ia['probability_up']
        conf = round(prob*100,2)

        gerenciar_posicoes(prob, atr)

        # Fibonacci
        fib = calcular_fibonacci(df)
        fib_confirm = False; sl_fibo=tp_fibo=preco_fibo=None
        if fib and sinal_ia=="COMPRA":
            d618 = abs(fib['distancias']['fib_618_dist'])
            d382 = abs(fib['distancias']['fib_382_dist'])
            if d618<0.05 or d382<0.03:
                fib_confirm=True
                preco_fibo = fib['niveis']['618'] if d618<=d382 else fib['niveis']['382']
                sl_fibo = fib['niveis']['786']; tp_fibo = fib['niveis']['100']
        elif fib and sinal_ia=="VENDA":
            d618 = abs(fib['distancias']['fib_618_dist'])
            d382 = abs(fib['distancias']['fib_382_dist'])
            if d618<0.05 or d382<0.03:
                fib_confirm=True
                preco_fibo = fib['niveis']['618'] if d618<=d382 else fib['niveis']['382']
                sl_fibo = fib['niveis']['786']; tp_fibo = fib['niveis']['100']

        # Padrões gráficos
        padrao_info = None; padrao_tf = None
        for tf, df_tf in [('W1',df_w1),('D1',df_d1),('H4',df_h4)]:
            if df_tf is None: continue
            p = detectar_duplo_topo_fundo(df_tf) or detectar_ombro_cabeca_ombro(df_tf)
            if p: padrao_info=p; padrao_tf=tf; break

        # Notícias
        noticias = analyze_news()
        if noticias is None: noticias={"has_high_impact":False,"event":"NENHUMA","news_signal":"NEUTRAL"}
        evento = noticias.get("event","NENHUMA")
        alto_impacto = noticias.get("has_high_impact",False)
        sinal_news = noticias.get("news_signal","NEUTRAL")

        # Scores
        pts_c, pts_v = 0,0
        motivos = []
        if tendencia=="COMPRA": pts_c+=1; motivos.append("Tendência alta")
        elif tendencia=="VENDA": pts_v+=1; motivos.append("Tendência baixa")
        if sinal_ia=="COMPRA": pts_c+=1; motivos.append(f"IA compra ({conf}%)")
        elif sinal_ia=="VENDA": pts_v+=1; motivos.append(f"IA venda ({conf}%)")
        if conf>60: pts_c+=1
        elif conf<40: pts_v+=1
        if fib_confirm:
            if sinal_ia=="COMPRA": pts_c+=1
            else: pts_v+=1
            motivos.append("Confirmação Fibonacci")
        if padrao_info:
            if padrao_info['padrao'] in ['DUPLO_FUNDO','OCO_INVERTIDO']:
                pts_c+=2; motivos.append(f"Padrão {padrao_info['padrao']} {padrao_tf}")
            else:
                pts_v+=2; motivos.append(f"Padrão {padrao_info['padrao']} {padrao_tf}")
        if sinal_news=="COMPRA": pts_c+=1; motivos.append(f"Notícia USD favorece COMPRA")
        elif sinal_news=="VENDA": pts_v+=1; motivos.append(f"Notícia USD favorece VENDA")
        elif alto_impacto: motivos.append(f"⚠️ Notícia alto impacto: {evento}")

        # Cálculo SL/TP/lote
        saldo, eq, _, _ = obter_info_conta()
        risco = obter_risco_atual(RISCO_PERCENTUAL)
        valor_risco = saldo*(risco/100)
        usar_padrao = padrao_info is not None
        if usar_padrao:
            sl = padrao_info['sl']; tp = padrao_info['tp']
            p_ent = padrao_info.get('preco_entrada',preco)
            sl_dist = abs(p_ent-sl); tp_dist = abs(tp-p_ent)
            rr = tp_dist/(sl_dist+1e-9)
            if rr < MIN_RR_BASE*0.8:
                print(f"⚠️ RR padrão {rr:.2f}"); lote=0
            else:
                lote = valor_risco/sl_dist if sl_dist>0 else 0
                lote = max(LOTE_BASE, round(lote*0.5/0.01)*0.01)
        else:
            if fib_confirm and sl_fibo and tp_fibo:
                sl = sl_fibo; tp = tp_fibo
                sl_dist = abs((preco_fibo or preco)-sl)
                tp_dist = abs(tp-(preco_fibo or preco))
            else:
                mult_sl = 2.0; mult_tp = 4.0
                if conf>75: mult_sl,mult_tp=1.8,5.0
                elif conf<45: mult_sl,mult_tp=2.5,3.0
                sl_dist = atr*mult_sl; tp_dist = atr*mult_tp
                sl = preco-sl_dist if sinal_ia=="COMPRA" else preco+sl_dist
                tp = preco+tp_dist if sinal_ia=="COMPRA" else preco-tp_dist
            rr = tp_dist/(sl_dist+1e-9)
            min_rr = MIN_RR_BASE*(1.3 if conf<60 else 1.0)
            if rr < min_rr:
                print(f"⚠️ RR {rr:.2f}"); lote=0
            else:
                lote = valor_risco/sl_dist if sl_dist>0 else 0
        lote = max(LOTE_BASE, min(1.0, round(lote/0.01)*0.01)) if lote>0 else 0
        if alto_impacto and lote>0:
            lote = max(LOTE_BASE, round(lote*0.5/0.01)*0.01)
        spread_ok = spread <= SPREAD_MAXIMO
        if not spread_ok: lote=0; motivos.append("⚠️ Spread alto")

        motivo_str = "; ".join(motivos)
        lucro_dia = obter_lucro_dia()
        wr,_,_ = obter_winrate()
        resumo = f"PnL dia ${lucro_dia:.2f} | Trades {trades_dia} | WR {wr*100:.1f}%"

        # ----- SHAP EXPLANATION -----
        try:
            gb = modelos[1]  # GradientBoostingClassifier
            explainer = shap.TreeExplainer(gb)
            shap_vals = explainer.shap_values(feat.reshape(1, -1))
            if isinstance(shap_vals, list):
                vals = shap_vals[1][0]  # classe positiva (subida)
            else:
                vals = shap_vals[0]

            # Use os nomes da lista completa de features (FEATURES_COMPLETAS)
            feature_names = FEATURES_COMPLETAS[:len(vals)]
            contribs = sorted(zip(feature_names, vals), key=lambda x: abs(x[1]), reverse=True)
            explicacao = "🧠 Influências SHAP:\n"
            for nome, valor in contribs[:8]:
                direcao = "↑" if valor > 0 else "↓"
                explicacao += f"  {nome}: {direcao} ({valor:+.4f})\n"
        except Exception as e:
            explicacao = f"SHAP indisponível: {e}"

        analise = f"""
📊 MERCADO
Tendência: {tendencia}
Sinal IA: {sinal_ia} ({conf}%)
Notícia: {evento}
ATR {atr:.2f} | Spread {spread:.5f}
Sessão: {sessao}
Lote: {lote}
Motivo: {motivo_str}
{resumo}
{explicacao}
"""
        dados_dashboard = {
            "signal":sinal_ia,"confidence":conf,"market":tendencia,"price":preco,
            "atr":round(atr,2),"spread":round(spread,5),"news":evento,"session":sessao,
            "analysis":analise,"reason":motivo_str,"buy_score":pts_c,"sell_score":pts_v,
            "winrate":round(wr*100,1),"trades":trades_dia,"pnl":f"${lucro_dia:.2f}"
        }
        enviar_dashboard(dados_dashboard)

        if not possui_posicao() and pode and lote>0 and spread_ok:
            sinal_entrada = None
            if pts_c>=3: sinal_entrada="COMPRA"
            elif pts_v>=3: sinal_entrada="VENDA"
            if sinal_entrada:
                if usar_padrao:
                    sl_f = padrao_info['sl']; tp_f = padrao_info['tp']; p_ent = padrao_info.get('preco_entrada',preco)
                    if (sinal_entrada=="COMPRA" and padrao_info['padrao'] in ['DUPLO_FUNDO','OCO_INVERTIDO']) or \
                       (sinal_entrada=="VENDA" and padrao_info['padrao'] in ['DUPLO_TOPO','OCO']):
                        if ATIVAR_ORDENS_LIMITE and ((sinal_entrada=="COMPRA" and p_ent<=preco) or (sinal_entrada=="VENDA" and p_ent>=preco)):
                            ticket = enviar_ordem_limite(sinal_entrada, p_ent, sl_f, tp_f, lote)
                        else:
                            ticket = enviar_ordem_mercado(sinal_entrada, sl_f, tp_f, lote)
                    else:
                        ticket = executar_ordem_normal(sinal_entrada, sl, tp, lote, fib_confirm, preco_fibo)
                else:
                    ticket = executar_ordem_normal(sinal_entrada, sl, tp, lote, fib_confirm, preco_fibo)
                if ticket:
                    trades_dia += 1
                    trades_abertos.append({'features':feat,'sinal':sinal_entrada,'ticket':ticket})
        else:
            if not pode: print("❌", msg)
            elif lote==0: print("❌ Lote zerado")
            else: print("⚠️ POSIÇÃO ABERTA")
        time.sleep(30)
    except Exception as e:
        print("❌ ERRO LOOP:", e)
        time.sleep(10)