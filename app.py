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
    page_title="SI-QA: Ultimate Kernel",
    page_icon="💠",
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

# --- MAPA DE TIMEFRAMES ---
TIMEFRAME_MAP = {
    "1M": 60, "M1": 60, "5M": 300, "M5": 300, 
    "15M": 900, "M15": 900, "30M": 1800, "M30": 1800,
    "1H": 3600, "H1": 3600, "4H": 14400, "H4": 14400,
    "1D": 86400, "D1": 86400
}

# --- CONFIGURAÇÃO DE SEGURANÇA (CORREÇÃO DO ERRO) ---
# Isso impede que o Gemini bloqueie a resposta por achar que o gráfico é "perigoso"
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

async def get_deep_history(symbol_code, granularity):
    """Baixa 2000 velas para Backtest Robusto (Reality Engine)"""
    uri = "wss://ws.binaryws.com/websockets/v3?app_id=1089"
    try:
        async with websockets.connect(uri) as websocket:
            req = {
                "ticks_history": symbol_code,
                "adjust_start_time": 1,
                "count": 2000, 
                "end": "latest",
                "style": "candles",
                "granularity": granularity
            }
            await websocket.send(json.dumps(req))
            res = await websocket.recv()
            data = json.loads(res)
            if 'error' in data: return None, data['error']['message']
            return data['candles'], None
    except Exception as e:
        return None, str(e)

# --- MOTOR DE BACKTEST REAL (PYTHON) ---

def calcular_indicadores(df):
    df['close'] = df['close'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    
    # Indicadores
    df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['SMA_20'] = df['close'].rolling(window=20).mean()
    df['STD_20'] = df['close'].rolling(window=20).std()
    df['Z_Score'] = (df['close'] - df['SMA_20']) / df['STD_20']
    
    return df.dropna()

def rodar_backtest_python(df):
    """
    Simula Mean Reversion nas últimas 2000 velas para validar Phase 3.
    """
    total_candles = len(df)
    if total_candles < 100: return "Dados insuficientes."
    
    wins = 0
    losses = 0
    sinais = 0
    
    # Loop de simulação
    for i in range(50, total_candles - 10):
        row = df.iloc[i]
        
        # Setup: Z-Score > 2.0 (Sobrecompra) -> Alvo: EMA 20
        if row['Z_Score'] > 2.0:
            sinais += 1
            outcome = "LOSS"
            for future_i in range(i+1, min(i+11, total_candles)):
                future_row = df.iloc[future_i]
                if future_row['low'] <= future_row['EMA_20']:
                    wins += 1
                    outcome = "WIN"
                    break
            if outcome == "LOSS": losses += 1

        # Setup: Z-Score < -2.0 (Sobrevenda) -> Alvo: EMA 20
        elif row['Z_Score'] < -2.0:
            sinais += 1
            outcome = "LOSS"
            for future_i in range(i+1, min(i+11, total_candles)):
                future_row = df.iloc[future_i]
                if future_row['high'] >= future_row['EMA_20']:
                    wins += 1
                    outcome = "WIN"
                    break
            if outcome == "LOSS": losses += 1

    win_rate = (wins / sinais * 100) if sinais > 0 else 0
    
    return f"""
    [REALITY ENGINE REPORT (PYTHON)]
    (Data Source: Last {total_candles} candles)
    - PATTERN FREQUENCY: {sinais} times detected in history.
    - SUCCESSFUL REVERSIONS: {wins}
    - FAILURES: {losses}
    - CALCULATED WIN RATE: {win_rate:.1f}%
    
    INSTRUCTION: Use this explicit Win Rate for Phase 3 'Virtual Backtest Check'.
    """

def analisar_imagem(img, model, lista_ativos):
    """Detecta Ativo e Timeframe"""
    prompt = "Identify Asset Name and Timeframe from header. Return: ASSET|TIMEFRAME"
    try:
        response = model.generate_content([prompt, img])
        texto = response.text.upper().strip()
        if "|" in texto: nome_raw, tf_raw = texto.split("|")
        else: nome_raw, tf_raw = texto, "M15"
            
        nome_ativo = None
        codigo_ativo = None
        nome_clean = nome_raw.replace("INDEX", "").strip()
        for k, v in lista_ativos.items():
            k_clean = k.replace("INDEX", "").strip()
            if nome_clean in k_clean or k_clean in nome_clean:
                nome_ativo = k
                codigo_ativo = v
                if nome_clean == k_clean: break
        
        segundos = 900 # Default M15
        tf_label = "M15"
        for k, v in TIMEFRAME_MAP.items():
            if k in tf_raw:
                segundos = v
                tf_label = k
                break
        return nome_ativo, codigo_ativo, segundos, tf_label
    except: return None, None, 900, "Erro IA"

# --- FUNÇÕES TELEGRAM ---
def enviar_telegram(token, chat_id, msg):
    try:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                     json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})
    except: pass

# --- INTERFACE ---
st.sidebar.header("⚙️ SI-QA SETTINGS")
if "GEMINI_API_KEY" in st.secrets: api_key = st.secrets["GEMINI_API_KEY"]
else: api_key = st.sidebar.text_input("Gemini API Key", type="password")

st.sidebar.divider()
tg_token = st.sidebar.text_input("Bot Token", type="password")
tg_chat = st.sidebar.text_input("Chat ID")

modo = st.sidebar.radio("Modo:", ["Análise Visual + Backtest", "Radar Automático"])

with st.spinner("Conectando Deriv..."):
    LISTA_ATIVOS = buscar_lista_ativos_deriv()
if not LISTA_ATIVOS: st.stop()

# ==========================================================
# MODO 1: ANÁLISE COMPLETA (3 IMAGENS + BACKTEST)
# ==========================================================
if modo == "Análise Visual + Backtest":
    st.title("💠 SI-QA: Ultimate Analysis")
    st.markdown("### Upload Multi-Timeframe (Tri-Dimensional)")
    
    col1, col2, col3 = st.columns(3)
    with col1: img_m15 = st.file_uploader("M15 (Gatilho/Entry)", type=['png', 'jpg'])
    with col2: img_h1 = st.file_uploader("H1 (Tendência)", type=['png', 'jpg'])
    with col3: img_h4 = st.file_uploader("H4 (Estrutura)", type=['png', 'jpg'])
    
    if st.button("INICIAR DECODIFICAÇÃO TOTAL"):
        if not api_key:
            st.error("Falta API Key.")
            st.stop()
        if not img_m15 and not img_h1 and not img_h4:
            st.error("Envie pelo menos uma imagem.")
            st.stop()
            
        status = st.status("Executando Protocolo SI-QA...", expanded=True)
        genai.configure(api_key=api_key)
        
        # AQUI ESTÁ A CORREÇÃO DE SEGURANÇA:
        model = genai.GenerativeModel("models/gemini-3-flash-preview", safety_settings=SAFETY_SETTINGS)
        
        # 1. Identificação (Prioridade: M15 -> H1 -> H4)
        status.write("👁️ Identificando Ativo...")
        img_principal = img_m15 if img_m15 else (img_h1 if img_h1 else img_h4)
        nome, codigo, segundos, tf_nome = analisar_imagem(Image.open(img_principal), model, LISTA_ATIVOS)
        
        if not nome:
            status.update(label="Erro", state="error")
            st.error("Falha na identificação do ativo.")
            st.stop()
            
        status.write(f"✅ Ativo: {nome} | Timeframe Base: {tf_nome}")
        
        # 2. Dados Profundos (2000 velas do timeframe detectado)
        status.write(f"📡 Baixando 2000 velas de {tf_nome} para Backtest...")
        candles, erro = asyncio.run(get_deep_history(codigo, segundos))
        if erro: st.error(erro); st.stop()
        
        df = pd.DataFrame(candles)
        df['epoch'] = pd.to_datetime(df['epoch'], unit='s')
        df = calcular_indicadores(df)
        
        # 3. Backtest Python
        status.write("🧮 Rodando Reality Engine (Estatística)...")
        relatorio_backtest = rodar_backtest_python(df)
        
        # 4. Preparar Prompt Multi-Imagem
        inputs_gemini = [SYSTEM_PROMPT]
        
        contexto_imgs = "IMAGES PROVIDED:\n"
        if img_m15: 
            inputs_gemini.append(Image.open(img_m15))
            contexto_imgs += "- IMAGE 1: M15 CHART (Entry Trigger)\n"
        if img_h1: 
            inputs_gemini.append(Image.open(img_h1))
            contexto_imgs += "- IMAGE 2: H1 CHART (Trend)\n"
        if img_h4: 
            inputs_gemini.append(Image.open(img_h4))
            contexto_imgs += "- IMAGE 3: H4 CHART (Structure)\n"
            
        prompt_injecao = f"""
        TARGET ASSET: {nome}
        BASE TIMEFRAME: {tf_nome}
        PRICE: {df.iloc[-1]['close']}
        Z-SCORE: {df.iloc[-1]['Z_Score']:.2f}
        
        {contexto_imgs}
        
        === REAL-TIME BACKTEST DATA (PHASE 3 CHECK) ===
        {relatorio_backtest}
        
        === LIVE MATH DATA (LAST 15 CANDLES) ===
        {df.tail(15).to_string()}
        
        COMMAND: EXECUTE SI-QA KERNEL LOGIC USING THE DATA ABOVE.
        """
        
        inputs_gemini.append(prompt_injecao)
        
        status.write("🧠 Gerando Sinal Final...")
        
        # TRATAMENTO DE ERRO DE SEGURANÇA NA GERAÇÃO
        try:
            resp = model.generate_content(inputs_gemini)
            status.update(label="Concluído", state="complete")
            st.divider()
            st.markdown(resp.text)
            
            with st.expander("Ver Prova Real (Backtest Python)"):
                st.text(relatorio_backtest)
        except ValueError:
            status.update(label="Bloqueio de Segurança", state="error")
            st.error("O Gemini bloqueou a resposta. Isso acontece raramente em gráficos voláteis. Tente novamente ou use outra imagem.")
        except Exception as e:
            st.error(f"Erro desconhecido: {str(e)}")

# ==========================================================
# MODO 2: RADAR
# ==========================================================
elif modo == "Radar Automático":
    st.title("📡 Radar de Probabilidade (Z-Score)")
    alvos = st.multiselect("Ativos:", list(LISTA_ATIVOS.keys()), default=["CRASH 1000 INDEX"])
    
    if st.button("INICIAR RADAR"):
        if not tg_token: st.error("Falta Telegram"); st.stop()
        st.success("Radar Rodando... (Não feche esta aba)")
        enviar_telegram(tg_token, tg_chat, "📡 RADAR SI-QA INICIADO")
        
        ph = st.empty()
        while True:
            log = []
            for nome in alvos:
                codigo = LISTA_ATIVOS[nome]
                candles, _ = asyncio.run(get_deep_history(codigo, 900)) # M15 padrão
                
                if candles:
                    df = pd.DataFrame(candles)
                    df = calcular_indicadores(df)
                    z = df.iloc[-1]['Z_Score']
                    
                    if abs(z) > 2.8:
                        msg = f"🚨 **{nome}**\nZ-Score Crítico: {z:.2f}\nProbabilidade de Reversão Alta!"
                        enviar_telegram(tg_token, tg_chat, msg)
                        log.append(f"{nome}: 🔴 ALERTA (Z: {z:.2f})")
                    else:
                        log.append(f"{nome}: ... (Z: {z:.2f})")
                time.sleep(1)
            ph.code("\n".join(log))
            time.sleep(60)