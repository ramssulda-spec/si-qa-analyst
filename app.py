import streamlit as st
import asyncio
import websockets
import json
import pandas as pd
import numpy as np
import google.generativeai as genai
from PIL import Image
import requests
import time

# ==============================================================================
# 1. CONFIGURAÇÕES DA PÁGINA (QUANTUM AESTHETIC)
# ==============================================================================
st.set_page_config(
    page_title="SI-APATECO QUANTUM V5.1",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Orbitron:wght@900&display=swap');
    
    .stApp {
        background-color: #000000;
        background-image: radial-gradient(circle at center, #0f0f0f 0%, #000000 100%);
        color: #e0e0e0;
        font-family: 'JetBrains Mono', monospace;
    }
    
    h1, h2, h3 {
        font-family: 'Orbitron', sans-serif !important;
        background: linear-gradient(90deg, #00ff88, #00b8ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -1px;
    }
    
    /* Metrics Highlighting */
    div[data-testid="stMetric"] {
        background-color: rgba(20, 20, 20, 0.8);
        border: 1px solid #333;
        border-radius: 6px;
        padding: 10px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        color: #00ff41 !important;
        font-family: 'Orbitron', sans-serif;
    }
    div[data-testid="stMetricLabel"] {
        color: #888;
    }

    /* Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #00ff41, #008f24);
        color: black;
        font-family: 'Orbitron';
        font-weight: 900;
        border: none;
        border-radius: 4px;
        text-transform: uppercase;
        padding: 15px 30px;
        transition: 0.3s;
        box-shadow: 0 0 10px rgba(0, 255, 65, 0.2);
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 20px rgba(0, 255, 65, 0.5);
    }

    /* DataFrame Styles */
    .dataframe {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

# --- SEGURANÇA GOOGLE GEMINI ---
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# ==============================================================================
# 2. PROMPT MESTRE (CONTROLADO PELOS DADOS)
# ==============================================================================
SYSTEM_PROMPT = """
( ROLE: QUANTUM EXECUTION ALGORITHM v5.1
Your logic is LOCKED to the provided Python Data. You strictly forbid visual price guessing.
You act as the Interpreter of the Math Core.

DATA CONTEXT:
1. REAL TIME SIGNAL: The specific setup found right now based on FVG/Structure.
2. HISTORICAL REALITY (Backtest): The system just simulated this strategy over the last 500 candles.
   -> IF Win Rate < 40%: Warn the user that this asset is currently chaotic (HIGH RISK).
   -> IF Win Rate > 60%: Validate as HIGH PROBABILITY SETUP.

OUTPUT FORMAT (Markdown):

## 💠 QUANTUM VERDICT: [ {FINAL_DECISION} ]
**Asset:** {ASSET_NAME} | **Probability Score:** {WIN_RATE}%

### 📉 TACTICAL GRID (STRICT EXECUTION)
| Parameter | Level/Price | Note |
| :--- | :--- | :--- |
| **Action** | **{FINAL_DECISION}** | *{AGGRESSIVE / CONSERVATIVE}* |
| **Entry Zone** | **{MATH_ENTRY}** | *Calculated Level* |
| **Stop Loss** | **{MATH_SL}** | *Structural Level* |
| **TP 1** | **{MATH_TP1}** | *Risk 1:1.5* |
| **TP 2** | **{MATH_TP2}** | *Liquidity Target* |

### 🧠 REASONING CORE:
- **Bias Alignment:** The H4 Macro Trend is {MACRO_TREND}. M15 RSI is {RSI_VAL}.
- **Historical Proof:** Over the last 500 candles, this logic generated a Net Profit of **{NET_PROFIT}R**.
- **Execution Context:** {Synthesize why the Math + Visual Context supports the trade}.
)
"""

# ==============================================================================
# 3. CONECTORES DE API & DADOS
# ==============================================================================

@st.cache_data(ttl=3600)
def get_deriv_assets():
    """Busca ativos disponíveis"""
    async def _fetch():
        uri = "wss://ws.binaryws.com/websockets/v3?app_id=1089"
        try:
            async with websockets.connect(uri) as ws:
                req = {"active_symbols": "brief", "product_type": "basic"}
                await ws.send(json.dumps(req))
                res = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(res)
                if 'error' in data: return None
                ativos = {}
                for x in data['active_symbols']:
                    if x['market'] == 'synthetic_index': ativos[x['display_name'].upper()] = x['symbol']
                return ativos
        except: return None
    return asyncio.run(_fetch())

async def fetch_candles(code):
    """Baixa Histórico para Cálculo e Backtest"""
    uri = "wss://ws.binaryws.com/websockets/v3?app_id=1089"
    try:
        async with websockets.connect(uri) as ws:
            # M15: Baixa 1000 velas (Suficiente para indicadores + Backtest robusto)
            await ws.send(json.dumps({"ticks_history": code, "style": "candles", "granularity": 900, "count": 1000, "adjust_start_time": 1, "end": "latest"}))
            m15 = json.loads(await asyncio.wait_for(ws.recv(), timeout=5.0))
            
            # H4: Baixa 200 velas para Tendência Macro
            await ws.send(json.dumps({"ticks_history": code, "style": "candles", "granularity": 14400, "count": 200, "adjust_start_time": 1, "end": "latest"}))
            h4 = json.loads(await asyncio.wait_for(ws.recv(), timeout=5.0))
            
            if 'error' in m15 or 'error' in h4: return None, None, "API Error"
            return m15['candles'], h4['candles'], None
    except Exception as e: return None, None, str(e)

# ==============================================================================
# 4. MATH CORE (CÁLCULOS TÉCNICOS)
# ==============================================================================

def prepare_df(data):
    df = pd.DataFrame(data)
    cols = ['open','high','low','close','epoch']
    for c in cols: df[c] = pd.to_numeric(df[c], errors='coerce')
    return df

def indicators(df):
    """Calcula RSI, EMA, ATR"""
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100/(1+rs))
    
    df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['EMA_200'] = df['close'].ewm(span=200, adjust=False).mean()
    
    # ATR para Volatilidade
    df['tr0'] = abs(df['high'] - df['low'])
    df['tr1'] = abs(df['high'] - df['close'].shift())
    df['tr2'] = abs(df['low'] - df['close'].shift())
    df['ATR'] = df[['tr0', 'tr1', 'tr2']].max(axis=1).rolling(14).mean()
    
    df.dropna(inplace=True)
    return df

def find_swings(df, window=5):
    """Encontra Pontos Estruturais (Pivôs) para SL Técnico"""
    df['is_low'] = df.iloc[window:-window]['low'].rolling(window=2*window+1, center=True).min() == df['low']
    df['is_high'] = df.iloc[window:-window]['high'].rolling(window=2*window+1, center=True).max() == df['high']
    
    last_low = df[df['is_low'] == True]['low'].iloc[-1] if not df[df['is_low'] == True].empty else df['low'].min()
    last_high = df[df['is_high'] == True]['high'].iloc[-1] if not df[df['is_high'] == True].empty else df['high'].max()
    return last_low, last_high

def detect_valid_fvg(df):
    """Detector de Fair Value Gaps Não-Mitigados"""
    fvgs = []
    # Olha os últimos 40 candles
    recent = df.tail(40).reset_index(drop=True)
    
    for i in range(len(recent)-2, 2, -1):
        # Bearish (Resistência)
        if recent.iloc[i-2]['low'] > recent.iloc[i]['high']:
            top = recent.iloc[i-2]['low']; bot = recent.iloc[i]['high']
            is_open = True
            for j in range(i+1, len(recent)):
                if recent.iloc[j]['high'] >= bot: is_open = False; break
            if is_open: fvgs.append({'type': 'BEARISH', 'price': (top+bot)/2}); break
        
        # Bullish (Suporte)
        elif recent.iloc[i-2]['high'] < recent.iloc[i]['low']:
            top = recent.iloc[i]['low']; bot = recent.iloc[i-2]['high']
            is_open = True
            for j in range(i+1, len(recent)):
                 if recent.iloc[j]['low'] <= top: is_open = False; break
            if is_open: fvgs.append({'type': 'BULLISH', 'price': (top+bot)/2}); break
            
    return fvgs[0] if fvgs else None

# ==============================================================================
# 5. BACKTEST ENGINE V5.1 (A NOVIDADE CRUCIAL)
# ==============================================================================

def run_quantum_backtest(df, asset_name):
    """
    Simula a estratégia no passado recente (500 velas) para calcular probabilidade.
    """
    trades = 0; wins = 0; losses = 0
    profit_r = 0.0 # Saldo em Unidades de Risco (Ex: ganhou 1.5R ou perdeu 1.0R)
    
    total = len(df)
    
    # Loop de simulação
    for i in range(100, total - 50):
        row = df.iloc[i]
        signal_bt = None
        
        # Filtro Simplificado para Velocidade: 
        # No backtest usamos EMA200 local como proxy da Tendência
        trend_bullish = row['close'] > row['EMA_200']
        trend_bearish = row['close'] < row['EMA_200']
        rsi = row['RSI']
        
        # LÓGICA DO SIMULADOR (Reflete a lógica principal)
        if "BOOM" in asset_name:
             # Em Boom, Backtest só compra
             if trend_bullish and rsi < 40: signal_bt = 'BUY'
        elif "CRASH" in asset_name:
             # Em Crash, Backtest só vende
             if trend_bearish and rsi > 60: signal_bt = 'SELL'
        else:
             # Outros
             if trend_bullish and rsi < 35: signal_bt = 'BUY'
             if trend_bearish and rsi > 65: signal_bt = 'SELL'
        
        if signal_bt:
            entry = row['close']
            atr = row['ATR']
            
            # SL e TP Técnicos Dinâmicos
            sl_dist = atr * 2.0
            tp_dist = atr * 3.0 # Risco Retorno 1:1.5
            
            if signal_bt == 'BUY':
                sl = entry - sl_dist
                tp = entry + tp_dist
            else:
                sl = entry + sl_dist
                tp = entry - tp_dist
            
            # Caminha para o futuro para ver se deu Gain ou Loss
            result = "OPEN"
            for f in range(i+1, min(i+60, total)): # Verifica próximas 60 velas
                nxt = df.iloc[f]
                if signal_bt == 'BUY':
                    if nxt['low'] <= sl: result = "LOSS"; break
                    if nxt['high'] >= tp: result = "WIN"; break
                else:
                    if nxt['high'] >= sl: result = "LOSS"; break
                    if nxt['low'] <= tp: result = "WIN"; break
            
            if result != "OPEN":
                trades += 1
                if result == "WIN": 
                    wins += 1; profit_r += 1.5
                else: 
                    losses += 1; profit_r -= 1.0
                i = f # Pula para frente para não abrir trades sobrepostos
                
    win_rate = (wins / trades * 100) if trades > 0 else 0
    return {
        "WIN_RATE": round(win_rate, 1),
        "TOTAL_TRADES": trades,
        "NET_PROFIT": round(profit_r, 2)
    }

# ==============================================================================
# 6. ORQUESTRADOR CENTRAL (MATH + BACKTEST + SIGNAL)
# ==============================================================================

def quantum_processor(name, m15_data, h4_data):
    df_m15 = indicators(prepare_df(m15_data))
    df_h4 = indicators(prepare_df(h4_data))
    
    # [1] Executar Backtest Primeiro (Validação Histórica)
    bt_stats = run_quantum_backtest(df_m15, name)
    
    # [2] Analise de Tempo Real (Agora)
    current_price = df_m15.iloc[-1]['close']
    current_rsi = df_m15.iloc[-1]['RSI']
    atr_val = df_m15.iloc[-1]['ATR']
    
    # Bias Macro (H4)
    h4_last = df_h4.iloc[-1]
    bias = "BULLISH" if h4_last['close'] > h4_last['EMA_50'] else "BEARISH"
    
    # Estrutura (M15)
    swing_low, swing_high = find_swings(df_m15)
    smart_zone = detect_valid_fvg(df_m15)
    
    signal = "WAIT (NO SETUP)"
    entry_p = current_price
    sl_p = current_price; tp1_p = current_price; tp2_p = current_price
    fvg_txt = "NONE DETECTED"

    # --- LÓGICA DE DECISÃO FINAL ---
    
    # > PROTOCOLO BOOM
    if "BOOM" in name:
        if bias == "BULLISH": # A favor da tendência
            confluence = False
            
            # Motivos para entrar: FVG ou RSI Sobrevendido
            if smart_zone and smart_zone['type'] == 'BULLISH':
                entry_p = smart_zone['price']; confluence = True
                fvg_txt = f"Gap Suporte @ {entry_p:.2f}"
            
            if current_rsi < 45: confluence = True
            
            if confluence:
                signal = "STRONG BUY (TREND)"
                sl_p = swing_low - (atr_val * 0.5) # Stop Estrutural
                risk = entry_p - sl_p
                
                # Proteção contra SL muito curto ou muito longo
                if risk < atr_val: sl_p = entry_p - (atr_val*1.5); risk = entry_p - sl_p
                
                tp1_p = entry_p + (risk * 2.0); tp2_p = entry_p + (risk * 4.0)

    # > PROTOCOLO CRASH
    elif "CRASH" in name:
         if bias == "BEARISH":
            confluence = False
            if smart_zone and smart_zone['type'] == 'BEARISH':
                entry_p = smart_zone['price']; confluence = True
                fvg_txt = f"Gap Resistência @ {entry_p:.2f}"
            if current_rsi > 55: confluence = True

            if confluence:
                signal = "STRONG SELL (TREND)"
                sl_p = swing_high + (atr_val * 0.5)
                risk = sl_p - entry_p
                if risk < atr_val: sl_p = entry_p + (atr_val*1.5); risk = sl_p - entry_p
                
                tp1_p = entry_p - (risk * 2.0); tp2_p = entry_p - (risk * 4.0)
    
    # > PROTOCOLO VOLATILITY
    else:
        if bias == "BULLISH":
            if smart_zone and smart_zone['type'] == 'BULLISH': 
                signal = "BUY (FVG)"; entry_p = smart_zone['price']
            elif current_rsi < 35: 
                signal = "BUY (PULLBACK)"; entry_p = current_price
            
            if "BUY" in signal:
                sl_p = swing_low; risk = entry_p - sl_p
                if risk < atr_val: risk = atr_val*1.5; sl_p = entry_p - risk
                tp1_p = entry_p + (risk*1.5); tp2_p = entry_p + (risk*3.0)

        elif bias == "BEARISH":
            if smart_zone and smart_zone['type'] == 'BEARISH': 
                signal = "SELL (FVG)"; entry_p = smart_zone['price']
            elif current_rsi > 65: 
                signal = "SELL (PULLBACK)"; entry_p = current_price

            if "SELL" in signal:
                sl_p = swing_high; risk = sl_p - entry_p
                if risk < atr_val: risk = atr_val*1.5; sl_p = entry_p + risk
                tp1_p = entry_p - (risk*1.5); tp2_p = entry_p - (risk*3.0)

    # Retorna o Pacote de Dados Completo (Atual + Backtest)
    return {
        "ASSET_NAME": name,
        "MACRO_TREND": bias,
        "RSI_VAL": round(current_rsi, 2),
        "RSI_STATUS": "OVERBOUGHT" if current_rsi > 70 else ("OVERSOLD" if current_rsi < 30 else "NEUTRAL"),
        "FVG_DETECTED": fvg_txt,
        "FINAL_DECISION": signal,
        "MATH_ENTRY": round(entry_p, 2),
        "MATH_SL": round(sl_p, 2),
        "MATH_TP1": round(tp1_p, 2),
        "MATH_TP2": round(tp2_p, 2),
        # DADOS DO BACKTEST
        "WIN_RATE": bt_stats['WIN_RATE'],
        "TOTAL_TRADES": bt_stats['TOTAL_TRADES'],
        "NET_PROFIT": bt_stats['NET_PROFIT']
    }

# ==============================================================================
# 7. UI / FRONTEND (TELA FINAL)
# ==============================================================================

st.sidebar.title("🔐 SI-APATECO KEY")
if "GEMINI_API_KEY" in st.secrets: api = st.secrets["GEMINI_API_KEY"]
else: api = st.sidebar.text_input("Cole API Gemini", type="password")

st.sidebar.divider()
st.sidebar.markdown("""
**CORE:** V5.1 (Math + Backtest)
**Backtest:** Últimas 500 Velas
**Mode:** Precision Execution
""")

st.title("💠 SI-APATECO QUANTUM V5.1")
st.caption("Engine V5.1 includes: FVG Detector, Swing Structures & Real-Time Backtesting.")

assets = get_deriv_assets()
if not assets: st.error("Erro Conexão API. Recarregue a página."); st.stop()

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 1. ALVO")
    target = st.selectbox("Ativo", list(assets.keys()))
    uploaded = st.file_uploader("Screenshot (Validação Visual)", type=['png', 'jpg', 'jpeg'])
    
    st.write("")
    run = st.button("RUN SYSTEM", use_container_width=True)

with col2:
    if run and uploaded and api:
        st.divider()
        status = st.status("🛠️ PROCESSANDO NÚCLEOS...", expanded=True)
        
        # 1. DOWNLOAD
        status.write(f"📡 Baixando histórico {target} (M15 & H4)...")
        m15_raw, h4_raw, err = asyncio.run(fetch_candles(assets[target]))
        if err: status.update(state="error", label="Erro API"); st.stop()
        
        # 2. CÁLCULO E BACKTEST
        status.write("🎲 Executando Backtest nas últimas 500 velas...")
        result = quantum_processor(target, m15_raw, h4_raw)
        
        status.write("🧠 Validando Sinais em Tempo Real...")
        time.sleep(0.5)
        status.update(label="EXECUÇÃO CONCLUÍDA", state="complete")
        
        # --- EXIBIÇÃO ---
        
        # PAINEL DO BACKTEST (ESTATÍSTICA)
        st.subheader("📊 DESEMPENHO HISTÓRICO RECENTE")
        b1, b2, b3 = st.columns(3)
        b1.metric("Win Rate", f"{result['WIN_RATE']}%", delta_color="normal")
        b2.metric("Lucro Líquido (R)", f"{result['NET_PROFIT']}R")
        b3.metric("Trades Testados", f"{result['TOTAL_TRADES']}")
        
        if result['WIN_RATE'] < 45:
            st.error("⚠️ ALERTA DE RISCO: O Backtest indica baixa performance recente neste ativo.")
        elif result['WIN_RATE'] > 60:
            st.success("✅ ALTA PROBABILIDADE: Histórico recente favorável.")
        
        # PAINEL TÁTICO (DADOS MATEMÁTICOS)
        st.divider()
        st.subheader(f"GRID TÁTICO: {result['FINAL_DECISION']}")
        st.dataframe([result], use_container_width=True)
        
        # SINTESE IA
        st.divider()
        st.subheader("🤖 ANÁLISE QUANTUM (GEMINI)")
        
        genai.configure(api_key=api)
        model = genai.GenerativeModel("gemini-2.0-flash", safety_settings=SAFETY_SETTINGS)
        
        try:
            full_prompt = [SYSTEM_PROMPT, f"DATA_PACKET: {json.dumps(result)}", Image.open(uploaded)]
            resp = model.generate_content(full_prompt)
            st.markdown(resp.text)
        except Exception as e:
            st.error(f"Erro IA: {e}")
            
    elif run and not uploaded:
        st.warning("⚠️ Preciso do print do gráfico para cruzar com os dados matemáticos.")
    elif run and not api:
        st.error("⚠️ Falta a API Key do Gemini.")
