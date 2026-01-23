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
    page_title="SI-QA: Command Center",
    page_icon="🚀",
    layout="wide"
)

# --- ESTILO VISUAL ---
st.markdown("""
<style>
    .stApp { background-color: #050505; color: #00ff41; font-family: 'Consolas', monospace; }
    .stButton>button { background-color: #004d00; color: #fff; border: 1px solid #00ff41; font-weight: bold; }
    .stTextInput>div>div>input { background-color: #111; color: #00ff41; border: 1px solid #333; }
    h1, h2, h3 { color: #00ff41 !important; }
    .stSuccess { background-color: #003300; color: white; }
    .stError { background-color: #330000; color: white; }
</style>
""", unsafe_allow_html=True)

# --- MAPA DE TIMEFRAMES (INTELIGÊNCIA HÍBRIDA) ---
# Converte o que a IA lê na imagem para segundos da API Deriv
TIMEFRAME_MAP = {
    "1M": 60, "M1": 60, "1 MINUTE": 60,
    "5M": 300, "M5": 300, "5 MINUTES": 300,
    "15M": 900, "M15": 900, "15 MINUTES": 900,
    "30M": 1800, "M30": 1800, "30 MINUTES": 1800,
    "1H": 3600, "H1": 3600, "1 HOUR": 3600,
    "4H": 14400, "H4": 14400, "4 HOURS": 14400,
    "1D": 86400, "D1": 86400, "DAILY": 86400
}

# --- PROMPT MESTRE (MANTIDO INTACTO) ---
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

async def get_deriv_data_dynamic(symbol_code, granularity):
    """
    Baixa dados com granularidade dinâmica baseada na imagem.
    """
    uri = "wss://ws.binaryws.com/websockets/v3?app_id=1089"
    try:
        async with websockets.connect(uri) as websocket:
            req = {
                "ticks_history": symbol_code,
                "adjust_start_time": 1,
                "count": 300, 
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

# --- FUNÇÕES AUXILIARES (TELEGRAM & CÁLCULOS) ---

def enviar_telegram(token, chat_id, mensagem):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": mensagem, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except:
        pass

def calcular_indicadores(df):
    df['close'] = df['close'].astype(float)
    df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['SMA_20'] = df['close'].rolling(window=20).mean()
    df['STD_20'] = df['close'].rolling(window=20).std()
    df['Upper'] = df['SMA_20'] + (df['STD_20'] * 2)
    df['Lower'] = df['SMA_20'] - (df['STD_20'] * 2)
    df['Z_Score'] = (df['close'] - df['SMA_20']) / df['STD_20']
    return df.dropna()

def analisar_imagem_completa(img, model, lista_ativos):
    """
    Melhoria 1: Detecta NOME e TIMEFRAME da imagem.
    """
    prompt = """
    Look at the chart header. 
    1. Identify the Asset Name (e.g. Crash 1000 Index).
    2. Identify the Timeframe (e.g. M1, M15, H1, 1 Minute).
    Return Format: ASSET|TIMEFRAME
    """
    try:
        response = model.generate_content([prompt, img])
        texto = response.text.upper().strip()
        
        if "|" in texto:
            nome_raw, tf_raw = texto.split("|")
        else:
            nome_raw, tf_raw = texto, "M15" # Fallback
            
        # Match Nome do Ativo
        nome_ativo = None
        codigo_ativo = None
        nome_raw_clean = nome_raw.replace("INDEX", "").strip()
        
        for nome_oficial, codigo in lista_ativos.items():
            nome_oficial_clean = nome_oficial.replace("INDEX", "").strip()
            if nome_raw_clean in nome_oficial_clean or nome_oficial_clean in nome_raw_clean:
                nome_ativo = nome_oficial
                codigo_ativo = codigo
                if nome_raw_clean == nome_oficial_clean: break
        
        # Match Timeframe
        segundos = 3600 # Default H1
        tf_label = "H1 (Default)"
        
        for key, val in TIMEFRAME_MAP.items():
            if key in tf_raw.strip():
                segundos = val
                tf_label = f"{key} ({val}s)"
                break
                
        return nome_ativo, codigo_ativo, segundos, tf_label
        
    except Exception as e:
        return None, None, 3600, str(e)

# --- INTERFACE ---

st.sidebar.header("⚙️ SI-QA SETTINGS")

# Segredos / API Keys
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = st.sidebar.text_input("Gemini API Key", type="password")

st.sidebar.divider()
st.sidebar.subheader("📡 Telegram Radar")
tg_token = st.sidebar.text_input("Bot Token", type="password")
tg_chat = st.sidebar.text_input("Chat ID")

st.sidebar.divider()
modo = st.sidebar.radio("Modo de Operação:", ["Análise Visual (Upload)", "Radar Automático 24/7"])

with st.spinner("Conectando Deriv..."):
    LISTA_ATIVOS = buscar_lista_ativos_deriv()

if not LISTA_ATIVOS: st.stop()

# ==========================================================
# MODO 1: ANÁLISE VISUAL (MELHORIA 1 - DINÂMICO)
# ==========================================================
if modo == "Análise Visual (Upload)":
    st.title("👁️ SI-QA: Dynamic Analysis")
    st.markdown("### Detecta Ativo e Timeframe Automaticamente")
    
    col1, col2, col3 = st.columns(3)
    with col1: img_main = st.file_uploader("Gráfico Principal (Define a Matemática)", type=['png', 'jpg'])
    with col2: img_h1 = st.file_uploader("Gráfico H1 (Contexto)", type=['png', 'jpg'])
    with col3: img_h4 = st.file_uploader("Gráfico H4 (Estrutura)", type=['png', 'jpg'])
    
    if st.button("EXECUTAR ANÁLISE", type="primary"):
        if not api_key or not img_main:
            st.error("API Key e Imagem Principal são obrigatórias.")
            st.stop()
            
        status = st.status("Iniciando Visão Computacional...", expanded=True)
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("models/gemini-3-flash-preview")
        
        # 1. VISÃO DINÂMICA
        status.write("👁️ Lendo Ativo e Timeframe da imagem...")
        nome, codigo, segundos, tf_nome = analisar_imagem_completa(Image.open(img_main), model, LISTA_ATIVOS)
        
        if not nome:
            status.update(label="Erro", state="error")
            st.error("Falha na leitura.")
            st.stop()
            
        status.write(f"✅ Ativo: **{nome}** | Timeframe Visual: **{tf_nome}**")
        
        # 2. DADOS PRECISOS
        status.write(f"📡 Baixando dados matemáticos correspondentes ({segundos}s)...")
        candles, erro = asyncio.run(get_deriv_data_dynamic(codigo, segundos))
        
        if erro: st.error(erro); st.stop()
        
        df = pd.DataFrame(candles)
        df['epoch'] = pd.to_datetime(df['epoch'], unit='s')
        df_full = calcular_indicadores(df)
        
        # 3. GERAÇÃO
        prompt_injecao = f"""
        TARGET ASSET: {nome}
        DETECTED TIMEFRAME: {tf_nome}
        CURRENT PRICE: {df_full.iloc[-1]['close']}
        
        === MATCHING MATH DATA (LAST 15 CANDLES) ===
        {df_full.tail(15).to_string()}
        
        TASK: Analyze using the specific logic for {tf_nome}.
        """
        
        inputs = [SYSTEM_PROMPT, prompt_injecao, Image.open(img_main)]
        if img_h1: inputs.append(Image.open(img_h1))
        if img_h4: inputs.append(Image.open(img_h4))
        
        status.write("🧠 SI-QA Decodificando...")
        response = model.generate_content(inputs)
        status.update(label="Sucesso", state="complete", expanded=False)
        
        st.divider()
        st.markdown(response.text)

# ==========================================================
# MODO 2: RADAR AUTOMÁTICO (MELHORIA 2 - TELEGRAM)
# ==========================================================
elif modo == "Radar Automático 24/7":
    st.title("📡 SI-QA: Silent Radar")
    st.markdown("### Monitoramento Matemático em Segundo Plano")
    
    ativos_alvo = st.multiselect("Selecione Ativos para Monitorar:", list(LISTA_ATIVOS.keys()), default=["CRASH 1000 INDEX", "VOLATILITY 75 INDEX"])
    intervalo = st.slider("Intervalo de Varredura (Segundos)", 60, 300, 60)
    
    if st.button("ATIVAR RADAR", type="primary"):
        if not tg_token or not tg_chat:
            st.error("Configure o Token e Chat ID do Telegram na barra lateral.")
            st.stop()
            
        st.success("📡 Radar Ativo! Mantenha esta aba aberta. Verifique seu Telegram.")
        enviar_telegram(tg_token, tg_chat, "🚨 SI-QA RADAR INICIADO 🚨\nMonitorando o mercado...")
        
        placeholder = st.empty()
        
        while True:
            log_scan = []
            for nome_ativo in ativos_alvo:
                codigo = LISTA_ATIVOS[nome_ativo]
                
                # Baixa dados M15 para o Radar (Padrão de Alerta)
                candles, erro = asyncio.run(get_deriv_data_dynamic(codigo, 900))
                
                if candles:
                    df = pd.DataFrame(candles)
                    df = calcular_indicadores(df)
                    last = df.iloc[-1]
                    
                    # --- LÓGICA DE ALERTA MATEMÁTICO (MATH GATES) ---
                    # 1. Z-Score Extremo (Reversão)
                    if abs(last['Z_Score']) > 2.8:
                        msg = f"🚨 **ALERTA: {nome_ativo}**\nZ-Score Crítico: {last['Z_Score']:.2f}\nPossível Reversão Iminente!"
                        enviar_telegram(tg_token, tg_chat, msg)
                        log_scan.append(f"{nome_ativo}: 🔴 ALERTA ENVIADO (Z-Score)")
                    
                    # 2. Rompimento de Bandas (Volatilidade)
                    elif last['close'] > last['Upper'] or last['close'] < last['Lower']:
                        msg = f"⚠️ **ATIVIDADE: {nome_ativo}**\nPreço rompeu Bandas de Bollinger.\nAlta Volatilidade."
                        enviar_telegram(tg_token, tg_chat, msg)
                        log_scan.append(f"{nome_ativo}: 🟡 Aviso Enviado")
                        
                    else:
                        log_scan.append(f"{nome_ativo}: ...Monitorando (Z: {last['Z_Score']:.2f})")
                
                time.sleep(1) # Delay leve entre ativos
            
            placeholder.code("\n".join(log_scan))
            time.sleep(intervalo)