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
    page_title="SI-QA: MTF Sniper",
    page_icon="🎯",
    layout="wide"
)

# --- ESTILO VISUAL ---
st.markdown("""
<style>
    .stApp { background-color: #000000; color: #00ff00; font-family: 'Courier New', monospace; }
    .stButton>button { background-color: #003300; color: #fff; border: 1px solid #00ff00; width: 100%; }
    div[data-testid="stExpander"] { border: 1px solid #00ff00; background-color: #050505; }
    .stSuccess { background-color: #064000; color: white; }
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
# PROMPT MESTRE ORIGINAL (MANTIDO)
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

async def get_dual_timeframe_data(symbol_code, macro_granularity):
    """
    BAIXA DADOS DUPLOS: M15 (Para Gatilho) + MACRO (Para Tendência)
    """
    uri = "wss://ws.binaryws.com/websockets/v3?app_id=1089"
    try:
        async with websockets.connect(uri) as websocket:
            # Requisita M15 (Fixo)
            req_micro = {
                "ticks_history": symbol_code, "adjust_start_time": 1,
                "count": 100, "end": "latest", "style": "candles", "granularity": 900
            }
            # Requisita Macro (Variável: H1 ou H4)
            req_macro = {
                "ticks_history": symbol_code, "adjust_start_time": 1,
                "count": 300, "end": "latest", "style": "candles", "granularity": macro_granularity
            }
            
            # Envia Micro
            await websocket.send(json.dumps(req_micro))
            res_micro = await websocket.recv()
            data_micro = json.loads(res_micro)
            
            # Envia Macro
            await websocket.send(json.dumps(req_macro))
            res_macro = await websocket.recv()
            data_macro = json.loads(res_macro)
            
            if 'error' in data_micro or 'error' in data_macro: return None, None, "Erro API"
            
            return data_micro['candles'], data_macro['candles'], None
    except Exception as e:
        return None, None, str(e)

# --- CÁLCULOS MATEMÁTICOS MTF ---

def calcular_indicadores(df):
    df['close'] = df['close'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['EMA_200'] = df['close'].ewm(span=200, adjust=False).mean() # Mestra
    df['SMA_20'] = df['close'].rolling(window=20).mean()
    df['STD_20'] = df['close'].rolling(window=20).std()
    df['Z_Score'] = (df['close'] - df['SMA_20']) / df['STD_20']
    return df.dropna()

def analisar_confluencia_python(df_micro, df_macro):
    """
    CRUZA A TENDÊNCIA MACRO COM O SINAL MICRO
    Retorna um relatório de inteligência para a IA.
    """
    # 1. Analisa Tendência Macro
    last_macro = df_macro.iloc[-1]
    tendencia_macro = "ALTA" if last_macro['close'] > last_macro['EMA_200'] else "BAIXA"
    
    # 2. Analisa Gatilho Micro (M15)
    last_micro = df_micro.iloc[-1]
    z_micro = last_micro['Z_Score']
    
    sinal_final = "NEUTRO/AGUARDAR"
    motivo = "Sem confluência."
    
    # Lógica de Sniper
    if tendencia_macro == "ALTA":
        if z_micro < -1.5: # M15 está barato (pullback) numa tendência de alta
            sinal_final = "COMPRA FORTE (SNIPER)"
            motivo = "Macro em ALTA e M15 sobrevendido (Pullback identificado)."
        elif z_micro > 2.0:
            sinal_final = "PERIGOSO (VENDA CONTRA TENDÊNCIA)"
            motivo = "M15 pede venda, mas Macro é alta. Ignorar scalping."
            
    elif tendencia_macro == "BAIXA":
        if z_micro > 1.5: # M15 está caro (pullback) numa tendência de baixa
            sinal_final = "VENDA FORTE (SNIPER)"
            motivo = "Macro em BAIXA e M15 sobrecomprado (Pullback identificado)."
        elif z_micro < -2.0:
            sinal_final = "PERIGOSO (COMPRA CONTRA TENDÊNCIA)"
            motivo = "M15 pede compra, mas Macro é baixa. Ignorar scalping."
            
    return f"""
    [MTF CONFLUENCE ENGINE REPORT]
    1. MACRO DIRECTION ({len(df_macro)} candles): {tendencia_macro} (Above/Below EMA 200)
    2. MICRO TRIGGER (M15 Z-Score): {z_micro:.2f}
    3. PYTHON VERDICT: {sinal_final}
    4. REASON: {motivo}
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
st.sidebar.header("⚙️ SI-QA SNIPER")
if "GEMINI_API_KEY" in st.secrets: api_key = st.secrets["GEMINI_API_KEY"]
else: api_key = st.sidebar.text_input("Gemini API Key", type="password")

st.sidebar.divider()
tg_token = st.sidebar.text_input("Bot Token", type="password")
tg_chat = st.sidebar.text_input("Chat ID")

st.sidebar.divider()
st.sidebar.subheader("🎯 Alvo Macro (Direção)")
estilo = st.sidebar.radio(
    "Definir Tendência Pelo:",
    ["Day Trade (H1 define direção)", "Swing Trade (H4 define direção)"],
    index=0
)

# Configura o Macro
if estilo == "Day Trade (H1 define direção)":
    macro_tf = 3600
    nome_macro = "H1"
else:
    macro_tf = 14400
    nome_macro = "H4"

modo_app = st.sidebar.radio("Ferramenta:", ["Análise MTF (Visual)", "Radar MTF (Auto)"])

with st.spinner("Conectando..."):
    LISTA_ATIVOS = buscar_lista_ativos_deriv()
if not LISTA_ATIVOS: st.stop()

# ==========================================================
# MODO 1: ANÁLISE MTF VISUAL
# ==========================================================
if modo_app == "Análise MTF (Visual)":
    st.title(f"🎯 SI-QA: Sniper ({nome_macro} + M15)")
    st.info(f"Estratégia: A direção é definida pelo **{nome_macro}**, mas a entrada busca precisão no **M15**.")
    
    col1, col2, col3 = st.columns(3)
    with col1: img_m15 = st.file_uploader("M15 (Entrada)", type=['png', 'jpg'])
    with col2: img_macro = st.file_uploader(f"{nome_macro} (Direção)", type=['png', 'jpg'])
    
    if st.button("ANALISAR CONFLUÊNCIA"):
        if not api_key: st.error("Falta API Key."); st.stop()
        if not img_m15: st.error("M15 é obrigatório para entrada."); st.stop()
            
        status = st.status("Iniciando Sniper Protocol...", expanded=True)
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("models/gemini-3-flash-preview", safety_settings=SAFETY_SETTINGS)
        
        # 1. Identificação
        status.write("👁️ Identificando Ativo...")
        img_p = img_m15 if img_m15 else img_macro
        nome, codigo = analisar_imagem(Image.open(img_p), model, LISTA_ATIVOS)
        
        if not nome: status.update(label="Erro Visão", state="error"); st.stop()
        status.write(f"✅ Ativo: {nome}")
        
        # 2. Dados Duplos (Micro + Macro)
        status.write(f"📡 Baixando dados combinados (M15 + {nome_macro})...")
        c_micro, c_macro, erro = asyncio.run(get_dual_timeframe_data(codigo, macro_tf))
        if erro: st.error(erro); st.stop()
        
        df_micro = calcular_indicadores(pd.DataFrame(c_micro))
        df_macro = calcular_indicadores(pd.DataFrame(c_macro))
        
        # 3. Análise de Confluência Python
        status.write("🧮 Cruzando Tendência vs Gatilho...")
        relatorio_mtf = analisar_confluencia_python(df_micro, df_macro)
        
        # 4. Prompt Injection (A Lógica Sniper)
        inputs_gemini = [SYSTEM_PROMPT]
        contexto = "IMAGES PROVIDED:\n"
        if img_m15: inputs_gemini.append(Image.open(img_m15)); contexto+="- M15 CHART (Entry Precision)\n"
        if img_macro: inputs_gemini.append(Image.open(img_macro)); contexto+=f"- {nome_macro} CHART (Macro Trend)\n"
        
        prompt_injecao = f"""
        TARGET: {nome}
        STRATEGY: MTF SNIPER (Macro Direction: {nome_macro} | Entry Trigger: M15)
        
        === DATA INTELLIGENCE ===
        {relatorio_mtf}
        
        === DETAILED DATA ===
        MACRO ({nome_macro}) PRICE: {df_macro.iloc[-1]['close']} (EMA 200: {df_macro.iloc[-1]['EMA_200']:.2f})
        MICRO (M15) PRICE: {df_micro.iloc[-1]['close']} (Z-Score: {df_micro.iloc[-1]['Z_Score']:.2f})
        
        TASK:
        1. Read the Python Verdict above.
        2. Look at the images to confirm structure (e.g., Support/Resistance).
        3. IGNORE M15 signals that go against the {nome_macro} Trend.
        4. ONLY recommend trade if Macro and Micro are aligned (Confluence).
        """
        
        inputs_gemini.append(prompt_injecao)
        
        try:
            status.write("🧠 Gerando Sinal de Precisão...")
            resp = model.generate_content(inputs_gemini)
            status.update(label="Pronto", state="complete")
            st.divider()
            st.markdown(resp.text)
            with st.expander("Ver Relatório de Confluência"): st.text(relatorio_mtf)
        except Exception as e:
            st.error(f"Erro: {e}")

# ==========================================================
# MODO 2: RADAR MTF
# ==========================================================
elif modo_app == "Radar MTF (Auto)":
    st.title(f"📡 Radar Sniper ({nome_macro} + M15)")
    st.markdown("Monitora a **Tendência Macro** e avisa quando o **M15** der entrada a favor dela.")
    alvos = st.multiselect("Ativos:", list(LISTA_ATIVOS.keys()), default=["CRASH 1000 INDEX"])
    
    if st.button("INICIAR RADAR SNIPER"):
        if not tg_token: st.error("Falta Telegram"); st.stop()
        st.success("Radar Sniper Ativo...")
        enviar_telegram(tg_token, tg_chat, f"📡 RADAR SNIPER INICIADO ({nome_macro} x M15)")
        
        ph = st.empty()
        while True:
            log = []
            for nome in alvos:
                codigo = LISTA_ATIVOS[nome]
                c_micro, c_macro, _ = asyncio.run(get_dual_timeframe_data(codigo, macro_tf))
                
                if c_micro and c_macro:
                    df_mi = calcular_indicadores(pd.DataFrame(c_micro))
                    df_ma = calcular_indicadores(pd.DataFrame(c_macro))
                    
                    # Lógica de Alerta
                    z = df_mi.iloc[-1]['Z_Score']
                    trend_up = df_ma.iloc[-1]['close'] > df_ma.iloc[-1]['EMA_200']
                    
                    msg = ""
                    # Compra a favor da tendência
                    if trend_up and z < -2.0:
                        msg = f"🎯 **{nome}**\nSNIPER BUY!\nMacro: Alta ({nome_macro})\nM15: Sobrevendido (Z: {z:.2f})"
                    
                    # Venda a favor da tendência
                    elif not trend_up and z > 2.0:
                        msg = f"🎯 **{nome}**\nSNIPER SELL!\nMacro: Baixa ({nome_macro})\nM15: Sobrecomprado (Z: {z:.2f})"
                        
                    if msg:
                        enviar_telegram(tg_token, tg_chat, msg)
                        log.append(f"{nome}: 🟢 SINAL ENVIADO")
                    else:
                        dir_str = "Alta" if trend_up else "Baixa"
                        log.append(f"{nome}: Macro {dir_str} | M15 Z: {z:.2f}")
                        
                time.sleep(1)
            ph.code("\n".join(log))
            time.sleep(60)