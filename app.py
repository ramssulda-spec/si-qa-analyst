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

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(
    page_title="SI-QA: Platinum (Backtest + Tri-Force)",
    page_icon="💎",
    layout="wide"
)

# --- ESTILO VISUAL ---
st.markdown("""
<style>
    .stApp { background-color: #000000; color: #00ff00; font-family: 'Courier New', monospace; }
    .stButton>button { background-color: #004d00; color: #ffffff; border: 1px solid #00ff00; font-weight: bold; width: 100%; }
    div[data-testid="stExpander"] { border: 1px solid #00ff00; background-color: #0a0a0a; }
    h1, h2, h3 { color: #00ff00 !important; }
    .stFileUploader>div>div>button { color: #000; background-color: #00ff00; }
</style>
""", unsafe_allow_html=True)

# --- SEGURANÇA ---
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# ==============================================================================
# PROMPT MESTRE ORIGINAL (100% INTACTO)
# ==============================================================================
SYSTEM_PROMPT = """
( ROLE & SYSTEM KERNEL
You are the "Synthetic Indices Quantum Architect" (SI-QA).
You exist solely to decode the PRNG (Pseudo-Random Number Generator) algorithms of the Deriv Synthetic Market.

>> YOUR DNA:
1. You DO NOT guess. You DO NOT predict. You CALCULATE probability densities.
2. Synthetic Indices are non-sentimental; they are mathematically bound by specific algorithms.
3. Your analysis must rely on Volatility Cycles, Mathematical Deviation (Z-Score), and Fractal Algorithm Defects.

 CRITICAL INPUT PROTOCOL (MANDATORY)
Since you function as a text/vision processing engine, you require INPUT to execute the code.
User MUST provide either:
A) A High-Definition Screenshot of the chart (Timeframes: M15, H1, H4).
B) A Data Array of the last 30-50 Candles (OHLC Values).
**IF NO DATA IS PROVIDED: State "AWAITING DATA INJECTION" and Pause.**

 PHASE 0: INDEX-SPECIFIC SUB-ROUTINE LOADING
First, Identify the Asset and Load its specific Logic:

[SUB-ROUTINE A: VOLATILITY INDICES (V75, V10, V100)]
Focus: Standard Deviation Expansions, Mean Reversion to Moving Averages (EMA 20/50), Accumulation/Distribution.
Triggers: Breakers + ATR expansion > 2.0.

[SUB-ROUTINE B: SPIKE INDICES (BOOM & CRASH)]
Focus: Tick Counting, Drop/Spike Rejection zones, "N" Pattern formation.
Rule: AGAINST the Spike trading is BANNED unless Structure Shift is confirmed on H1.
Rule: WITH the Spike trading requires 'Golden Pocket' Retracement (61.8% - 78.6%).

[SUB-ROUTINE C: DISCRETE INDICES (STEP & JUMP)]
Focus: Level Ladders, Support breaks.
Triggers: Only Break & Retest of flat levels.

 PHASE 1: PRNG ALGORITHMIC DECODER (THE QUANTUM SCAN)

1.1. ALGORITHMIC REGIME DETECTION
Calculate current state relative to recent history:
- [0] Dead Zone: Low volatility/ATR < Historical Mean. (ACTION: IDLE)
- [1] Pump/Dump: Volatility > 3 Sigma. (ACTION: FADE/REVERSION)
- [2] Flow State: Consistent HH/HL sequence w/ Displacement. (ACTION: TREND FOLLOWING)

1.2. FRACTAL NOISE CANCELLATION
Identify and DISCARD "Noise Candles":
- Candles with >50% Wicks relative to Body.
- Candles strictly inside previous candle range (Harami/Inside Bar).
*Target only "Power Candles" (Body > 70% of Range).*

 PHASE 2: THE "MATH-FIRST" VALIDATION GATES
The setup is valid ONLY if the Boolean Logic is TRUE for ALL:

1. [DISPLACEMENT VELOCITY]: Did price move away from the zone faster (fewer candles) than it took to get there? [T/F]
2. [LIQUIDITY EXTRACTION]: Did the move initiate AFTER clearing a fractal High/Low? (The Judas Swing) [T/F]
3. [PREMIUM/DISCOUNT ARRAY]: Is the entry in the correct Quadrant (Above 50% for Sell, Below 50% for Buy)? [T/F]
4. [IMBALANCE PRESENCE]: Is there an unmitigated FVG or Algorithm Gap clearly visible? [T/F]

If ANY is "False" => STATUS: ABORT_NO_EDGE.

 PHASE 3: REAL-TIME BACKTEST SIMULATION (VIRTUAL)
*Mental Simulation:*
"Scan the visible chart history. Look for the EXACT same pattern setup. How many times did it appear? How many times did it fail?"
- Pattern Frequency Score (1-10)
- Failure Rate estimation.
*If Failure Rate in simulation > 40% -> ABORT.*

 PHASE 4: EXECUTION MATRIX (SURGICAL PRECISION)

>> ENTRY ZONES (Choose One Best Match):
1. **The Origin (Extreme):** Order Block Body Open (Precision Entry).
2. **The Equilibrium (Fair Value):** 50% of the FVG.
3. **The Spike Limit (Boom/Crash):** Previous Spike Base + Spread.

>> RISK PARAMETERS (Dynamic):
- Stop Loss: MUST be protected by a structural Invalidity Point (ATR Buffer added).
- Risk Reward Ratio: STRICTLY > 1:3. No exceptions.

 PHASE 5: PROBABILITY & OUTPUT GENERATION

Compute final score "Win Probability" (WP) based on Confluences/Regime.
Output formatted specifically for trader execution.

---
 OUTPUT TERMINAL:
(Render this specifically when you analyze the data)

/// SYNTHETIC QUANTUM DECODER ///
[TIMESTAMP: Current | ASSET: {Symbol}]

SYSTEM STATE: {CALCULATING...}
>> REGIME DETECTED: [ {Type} | STRENGTH: {0-100}% ]
   *Mathematical Context: (e.g. 2 SD Expansion, Range Bound)*

>> PRNG DECODING:
   [1] Structure Break: {YES/NO/PENDING}
   [2] Algorithm Trap (Fakeout): {DETECTED/CLEAN}
   [3] Momentum Velocity: {ACCELERATING / DECELERATING}

>> VIRTUAL BACKTEST CHECK:
   "Similar structures in current view have yielded positive reactions X out of Y times."

>> STRATEGY EXECUTION:
    ACTION: {BUY LIMIT / SELL LIMIT / BUY NOW / SELL NOW / STAY OUT}
    ENTRY PRICE (Specific): {1234.56}
    STOP LOSS (Hard Deck): {1230.00}
    TAKE PROFIT 1 (Liq pool): {1250.00}
    TAKE PROFIT 2 (Extension): {1280.00}

>> FINAL CONFIDENCE RATING:
    PROBABILITY: {XX.X%}
    CRITICAL WARNING: {Example: "Against Trend," "Approaching Key Level"}
    ADVICE: {One precise tactical instruction}

---------------------------------------------------
COMMAND: WAITING FOR CHART IMAGE OR OHLC DATA ARRAY TO INITIATE DECODING.
)
"""

# --- FUNÇÕES DE API ---

@st.cache_data(ttl=3600)
def buscar_lista_ativos_deriv():
    async def _fetch():
        uri = "wss://ws.binaryws.com/websockets/v3?app_id=1089"
        try:
            async with websockets.connect(uri) as ws:
                req = {"active_symbols": "brief", "product_type": "basic"}
                await ws.send(json.dumps(req))
                res = await ws.recv()
                data = json.loads(res)
                if 'error' in data: return None
                ativos_dict = {}
                for item in data['active_symbols']:
                    if item['market'] == 'synthetic_index':
                        ativos_dict[item['display_name'].upper()] = item['symbol']
                return ativos_dict
        except: return None
    return asyncio.run(_fetch())

async def get_platinum_data(symbol_code):
    """
    BAIXA TUDO:
    1. M15 PROFUNDO (2000 velas) -> Para Backtest Estatístico
    2. H1 e H4 (200 velas) -> Para Contexto Tri-Force
    """
    uri = "wss://ws.binaryws.com/websockets/v3?app_id=1089"
    try:
        async with websockets.connect(uri) as websocket:
            # 1. M15 DEEP (Para Backtest)
            req_m15_deep = {"ticks_history": symbol_code, "adjust_start_time": 1, "count": 2000, "end": "latest", "style": "candles", "granularity": 900}
            
            # 2. H1 e H4 (Contexto)
            req_h1 = {"ticks_history": symbol_code, "adjust_start_time": 1, "count": 200, "end": "latest", "style": "candles", "granularity": 3600}
            req_h4 = {"ticks_history": symbol_code, "adjust_start_time": 1, "count": 200, "end": "latest", "style": "candles", "granularity": 14400}
            
            # Execução
            await websocket.send(json.dumps(req_m15_deep)); res_m15 = await websocket.recv()
            await websocket.send(json.dumps(req_h1)); res_h1 = await websocket.recv()
            await websocket.send(json.dumps(req_h4)); res_h4 = await websocket.recv()
            
            d_m15 = json.loads(res_m15)
            d_h1 = json.loads(res_h1)
            d_h4 = json.loads(res_h4)
            
            if 'error' in d_m15 or 'error' in d_h1 or 'error' in d_h4: return None, None, None, "Erro API"
            
            return d_m15['candles'], d_h1['candles'], d_h4['candles'], None
    except Exception as e:
        return None, None, None, str(e)

# --- MOTOR DE BACKTEST (RESTAURADO!) ---

def calcular_indicadores(df):
    df['close'] = df['close'].astype(float)
    df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['EMA_200'] = df['close'].ewm(span=200, adjust=False).mean() # Tendência Mestra
    df['SMA_20'] = df['close'].rolling(window=20).mean()
    df['STD_20'] = df['close'].rolling(window=20).std()
    df['Z_Score'] = (df['close'] - df['SMA_20']) / df['STD_20']
    return df.dropna()

def rodar_backtest_estatistico(df):
    """
    Testa a eficácia da estratégia nas últimas 2000 velas de M15.
    Lógica: Reversão à Média (Z-Score > 2.0 volta para EMA 20).
    """
    total = len(df)
    if total < 500: return "Dados insuficientes para estatística."
    
    wins = 0
    losses = 0
    sinais = 0
    
    for i in range(50, total - 20):
        row = df.iloc[i]
        
        # Setup de Venda (Sobrecompra)
        if row['Z_Score'] > 2.0:
            sinais += 1
            outcome = "LOSS"
            # Verifica próximas 15 velas
            for future_i in range(i+1, min(i+16, total)):
                if df.iloc[future_i]['low'] <= df.iloc[future_i]['EMA_20']:
                    wins += 1; outcome = "WIN"; break
            if outcome == "LOSS": losses += 1

        # Setup de Compra (Sobrevenda)
        elif row['Z_Score'] < -2.0:
            sinais += 1
            outcome = "LOSS"
            for future_i in range(i+1, min(i+16, total)):
                if df.iloc[future_i]['high'] >= df.iloc[future_i]['EMA_20']:
                    wins += 1; outcome = "WIN"; break
            if outcome == "LOSS": losses += 1
            
    win_rate = (wins / sinais * 100) if sinais > 0 else 0
    
    return f"""
    [REALITY ENGINE REPORT]
    - TIMEFRAME ANALYZED: M15 (Last {total} candles)
    - PATTERN FREQUENCY: {sinais} signals found in history.
    - HISTORICAL SUCCESS: {wins}
    - HISTORICAL FAILURES: {losses}
    - CALCULATED PROBABILITY (WIN RATE): {win_rate:.1f}%
    """

def analisar_imagem(img, model, lista_ativos):
    prompt = "Identify Asset Name ONLY. Return: ASSET_NAME"
    try:
        response = model.generate_content([prompt, img])
        nome_raw = response.text.upper().strip().replace("INDEX", "").strip()
        nome_ativo = None
        codigo_ativo = None
        for k, v in lista_ativos.items():
            k_clean = k.replace("INDEX", "").strip()
            if nome_raw in k_clean or k_clean in nome_raw:
                nome_ativo = k; codigo_ativo = v; break
        return nome_ativo, codigo_ativo
    except: return None, None

# --- FUNÇÕES TELEGRAM ---
def enviar_telegram(token, chat_id, msg):
    try:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                     json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})
    except: pass

# --- INTERFACE ---
st.sidebar.header("⚙️ SI-QA PLATINUM")
if "GEMINI_API_KEY" in st.secrets: api_key = st.secrets["GEMINI_API_KEY"]
else: api_key = st.sidebar.text_input("Gemini API Key", type="password")

st.sidebar.divider()
tg_token = st.sidebar.text_input("Bot Token", type="password")
tg_chat = st.sidebar.text_input("Chat ID")

st.sidebar.divider()
modo_operacao = st.sidebar.radio(
    "Modo:",
    ["Análise Tri-Force + Backtest", "Radar Automático (Telegram)"]
)

with st.spinner("Conectando..."):
    LISTA_ATIVOS = buscar_lista_ativos_deriv()
if not LISTA_ATIVOS: st.stop()

# ==========================================================
# MODO 1: ANÁLISE TRI-FORCE + BACKTEST
# ==========================================================
if modo_operacao == "Análise Tri-Force + Backtest":
    st.title("💎 SI-QA: Platinum Analysis")
    st.markdown("### 3 Visões (M15/H1/H4) + 1 Verdade Estatística")
    
    col1, col2, col3 = st.columns(3)
    with col1: img_m15 = st.file_uploader("1. M15 (Micro)", type=['png', 'jpg'])
    with col2: img_h1 = st.file_uploader("2. H1 (Médio)", type=['png', 'jpg'])
    with col3: img_h4 = st.file_uploader("3. H4 (Macro)", type=['png', 'jpg'])
    
    if st.button("RODAR PROTOCOLO COMPLETO"):
        if not api_key: st.error("Falta API Key."); st.stop()
        img_p = img_m15 if img_m15 else (img_h1 if img_h1 else img_h4)
        if not img_p: st.error("Envie imagens."); st.stop()
        
        status = st.status("Iniciando Análise Platina...", expanded=True)
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("models/gemini-3-flash-preview", safety_settings=SAFETY_SETTINGS)
        
        # 1. Identificação
        status.write("👁️ Identificando Ativo...")
        nome, codigo = analisar_imagem(Image.open(img_p), model, LISTA_ATIVOS)
        if not nome: status.update(label="Erro", state="error"); st.stop()
        
        # 2. Dados Completos (M15 Deep, H1, H4)
        status.write(f"📡 Baixando 2000 velas de Backtest + Contexto H1/H4...")
        c_m15, c_h1, c_h4, erro = asyncio.run(get_platinum_data(codigo))
        if erro: st.error(erro); st.stop()
        
        df_m15 = calcular_indicadores(pd.DataFrame(c_m15))
        df_h1 = calcular_indicadores(pd.DataFrame(c_h1))
        df_h4 = calcular_indicadores(pd.DataFrame(c_h4))
        
        # 3. Rodar Backtest (Reality Engine)
        status.write("🧮 Calculando Probabilidade Real (Backtest Python)...")
        relatorio_backtest = rodar_backtest_estatistico(df_m15)
        
        # 4. Prompt
        inputs = [SYSTEM_PROMPT]
        contexto = "IMAGES:\n"
        if img_m15: inputs.append(Image.open(img_m15)); contexto+="- M15 (Entry)\n"
        if img_h1: inputs.append(Image.open(img_h1)); contexto+="- H1 (Trend)\n"
        if img_h4: inputs.append(Image.open(img_h4)); contexto+="- H4 (Structure)\n"
        
        prompt_injecao = f"""
        TARGET: {nome}
        {contexto}
        
        === REAL-TIME BACKTEST (PHASE 3 CHECK) ===
        {relatorio_backtest}
        
        === TRI-FORCE DATA CONTEXT ===
        [H4 MACRO]: Price {df_h4.iloc[-1]['close']} | Trend: {"BULLISH" if df_h4.iloc[-1]['close'] > df_h4.iloc[-1]['EMA_200'] else "BEARISH"}
        [M15 MICRO]: Z-Score {df_m15.iloc[-1]['Z_Score']:.2f}
        
        TASK:
        1. Use the H4 Trend to decide Day Trade vs Swing.
        2. Use the Backtest Win Rate to calculate Probability.
        3. Combine all into one final signal.
        """
        inputs.append(prompt_injecao)
        
        try:
            status.write("🧠 Gerando Veredito Final...")
            resp = model.generate_content(inputs)
            status.update(label="Pronto", state="complete")
            st.divider()
            st.markdown(resp.text)
            
            with st.expander("Ver Relatório Estatístico (Python)"):
                st.text(relatorio_backtest)
                
        except Exception as e: st.error(f"Erro: {e}")

# ==========================================================
# MODO 2: RADAR AUTOMÁTICO
# ==========================================================
elif modo_operacao == "Radar Automático (Telegram)":
    st.title("📡 SI-QA: Radar Platina")
    alvos = st.multiselect("Ativos:", list(LISTA_ATIVOS.keys()), default=["CRASH 1000 INDEX"])
    
    if st.button("ATIVAR MONITORAMENTO"):
        if not tg_token: st.error("Falta Telegram"); st.stop()
        st.success("Radar Ativo.")
        enviar_telegram(tg_token, tg_chat, "📡 RADAR SI-QA INICIADO")
        
        ph = st.empty()
        while True:
            log = []
            for nome in alvos:
                try:
                    codigo = LISTA_ATIVOS[nome]
                    # Baixa dados (M15 e H4 para Sniper Logic)
                    c_m15, _, c_h4, _ = asyncio.run(get_platinum_data(codigo))
                    
                    if c_m15 and c_h4:
                        df_mi = calcular_indicadores(pd.DataFrame(c_m15))
                        df_ma = calcular_indicadores(pd.DataFrame(c_h4))
                        
                        z = df_mi.iloc[-1]['Z_Score']
                        trend_up = df_ma.iloc[-1]['close'] > df_ma.iloc[-1]['EMA_200']
                        
                        msg = ""
                        if trend_up and z < -2.5:
                            msg = f"🚀 **{nome}**\nSETUP: Tendência H4 Alta + M15 Sobrevendido\nZ-Score: {z:.2f}"
                        elif not trend_up and z > 2.5:
                            msg = f"🔻 **{nome}**\nSETUP: Tendência H4 Baixa + M15 Sobrecomprado\nZ-Score: {z:.2f}"
                            
                        if msg:
                            enviar_telegram(tg_token, tg_chat, msg)
                            log.append(f"{nome}: SINAL ✅")
                        else:
                            log.append(f"{nome}: ...")
                except: pass
                time.sleep(1)
            ph.code("\n".join(log))
            time.sleep(60)

