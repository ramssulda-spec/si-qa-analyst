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
    page_title="SI-QA: TITAN Edition",
    page_icon="🧬",
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
    .stSuccess { background-color: #064000; color: white; border: 1px solid #00ff00; }
    .stWarning { background-color: #332b00; color: #ffcc00; border: 1px solid #ffcc00; }
    .stError { background-color: #330000; color: #ff0000; border: 1px solid #ff0000; }
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
# PROMPT MESTRE: SI-QA TITAN (PROTOCOLS A, B, C)
# ==============================================================================
SYSTEM_PROMPT = """
( ROLE & SYSTEM KERNEL
You are the "SI-QA TITAN", an Institutional Algorithm designed for the Deriv Synthetic Markets.
You operate on a "Hierarchy of Truth":
1. MATH (Python Data) is the absolute truth.
2. MACRO STRUCTURE (H4 Chart) is the map.
3. MICRO TRIGGER (M15 Chart) is the timing.

>> DYNAMIC ASSET PROTOCOLS (YOU MUST OBEY THE DETECTED CLASS):

<PROTOCOL_A: SPIKE_INDICES>
(Target: Crash 300/500/1000 & Boom 300/500/1000)
- PHYSICS: These assets have asymmetric volatility. Drops/Spikes happen in 1 tick.
- RULE 1: NEVER trust "Overbought/Oversold" oscillators blindly. A Crash index can stay "Oversold" for 50 candles while trending down.
- RULE 2: Trend Following (H4) is the only safe path.
- TRIGGER: Look for "N" Patterns (Spike -> Small Retracement -> Spike) or Key Support levels on H4.
- FORBIDDEN: Do not signal a reversal (catching a falling knife) unless price hits a massive H4 Support.

<PROTOCOL_B: DISCRETE_INDICES>
(Target: Step Index, Jump Indices)
- PHYSICS: Price moves in rigid blocks/steps. EMAs are less effective here.
- FOCUS: Horizontal Levels (Support/Resistance) and Breakouts.
- TRIGGER: Wait for a candle to BREAK and CLOSE outside a consolidation box.
- TRAP WARNING: Step Index loves "Fake Breakouts". Wait for the retest if possible.

<PROTOCOL_C: FLUID_INDICES>
(Target: Volatility 10/25/50/75/100, Range Break)
- PHYSICS: Standard Brownian Motion. Technical Analysis works perfectly here.
- FOCUS: Market Structure (HH/HL), EMA 200 Trend, and Fibonacci Retracements.
- TRIGGER: Z-Score deviation + RSI Divergence is the strongest signal.

 CRITICAL INPUT PROTOCOL
User provides:
A) 3 Charts (M15, H1, H4).
B) ASSET CLASS (Detected by Python).
C) MATH DATA (Z-Score, Spikes, or Trend Data).

 OUTPUT TERMINAL (Strict Format):

/// SI-QA TITAN ANALYSIS ///
[ASSET: {Asset} | PROTOCOL: {Protocol A/B/C}]

>> HIERARCHY CHECK:
   1. MACRO (H4): {Describe Structure - e.g., Bullish Order Block}
   2. MATH DATA: {Interpret the Python Data provided}
   3. MICRO (M15): {Describe the candle pattern}

>> VERDICT MATRIX:
   - TREND ALIGNMENT: {Strong/Weak/Against}
   - STATISTICAL EDGE: {High/Medium/Low}

>> EXECUTION ORDER:
    ACTION: {BUY / SELL / WAIT}
    TYPE: {SCALP (Catch Spike) / SWING (Trend) / DAY (Breakout)}
    ENTRY ZONE: {Specific Price Area}
    INVALIDATION POINT (SL): {Price where thesis fails}
    TARGET (TP): {Next Liquidity Pool}

>> INSTITUTIONAL NOTE:
    {One sentence explaining the "Why". Example: "H4 Support holds, and Python detects abnormal spike volume."}
)
"""

# --- FUNÇÕES API ---

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

async def get_raw_data(symbol_code):
    uri = "wss://ws.binaryws.com/websockets/v3?app_id=1089"
    try:
        async with websockets.connect(uri) as websocket:
            # Baixa M15 (Gatilho) e H4 (Macro)
            req_m15 = {"ticks_history": symbol_code, "adjust_start_time": 1, "count": 1000, "end": "latest", "style": "candles", "granularity": 900}
            req_h4 = {"ticks_history": symbol_code, "adjust_start_time": 1, "count": 200, "end": "latest", "style": "candles", "granularity": 14400}
            
            await websocket.send(json.dumps(req_m15)); res_m15 = await websocket.recv()
            await websocket.send(json.dumps(req_h4)); res_h4 = await websocket.recv()
            
            d_m15 = json.loads(res_m15)
            d_h4 = json.loads(res_h4)
            
            if 'error' in d_m15 or 'error' in d_h4: return None, None, "Erro API"
            return d_m15['candles'], d_h4['candles'], None
    except Exception as e: return None, None, str(e)

# --- NÚCLEOS MATEMÁTICOS ADAPTATIVOS ---

def math_common(df):
    df['close'] = df['close'].astype(float)
    df['EMA_200'] = df['close'].ewm(span=200, adjust=False).mean()
    return df

def math_volatility_step(df):
    """Para Step, V75, Range Break"""
    df['SMA_20'] = df['close'].rolling(window=20).mean()
    df['STD_20'] = df['close'].rolling(window=20).std()
    df['Z_Score'] = (df['close'] - df['SMA_20']) / df['STD_20']
    
    # RSI
    delta = df['close'].diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

def math_boom_crash(df, tipo):
    """Para Boom e Crash (Spikes)"""
    df['body_size'] = df['close'] - df['open']
    threshold = df['body_size'].std() * 2
    if "CRASH" in tipo:
        df['is_spike'] = df['body_size'] < -threshold
    else: # BOOM
        df['is_spike'] = df['body_size'] > threshold
    return df

def processar_dados_inteligentes(nome_ativo, df_m15):
    """O Cérebro Adaptativo"""
    df_m15 = math_common(df_m15)
    info_extra = ""
    classe = ""
    
    # 1. PROTOCOLO A: SPIKE
    if "CRASH" in nome_ativo or "BOOM" in nome_ativo:
        classe = "PROTOCOL A: SPIKE INDICES"
        df_final = math_boom_crash(df_m15, nome_ativo)
        total_spikes = df_final['is_spike'].sum()
        last_candle = df_final.iloc[-1]['body_size']
        trend = "BEARISH" if df_final.iloc[-1]['close'] < df_final.iloc[-1]['EMA_200'] else "BULLISH"
        
        info_extra = f"""
        [SPIKE DATA]
        - Trend (EMA 200): {trend}
        - Spike Frequency (Last 1000 candles): {total_spikes}
        - Current Candle Velocity: {last_candle:.4f}
        """

    # 2. PROTOCOLO B: DISCRETE (STEP/JUMP)
    elif "STEP" in nome_ativo or "JUMP" in nome_ativo:
        classe = "PROTOCOL B: DISCRETE INDICES"
        df_final = math_volatility_step(df_m15)
        # ATR para volatilidade
        df_final['tr'] = np.maximum((df_final['high'] - df_final['low']), 
                                    np.maximum(abs(df_final['high'] - df_final['close'].shift()), 
                                               abs(df_final['low'] - df_final['close'].shift())))
        atr = df_final['tr'].rolling(14).mean().iloc[-1]
        rsi = df_final.iloc[-1]['RSI']
        
        info_extra = f"""
        [DISCRETE DATA]
        - ATR (Volatility): {atr:.4f}
        - RSI: {rsi:.2f}
        - NOTE: Focus on Horizontal Breakouts (Boxes), ignore small wicks.
        """

    # 3. PROTOCOLO C: FLUID (V75, ETC)
    else: 
        classe = "PROTOCOL C: FLUID INDICES"
        df_final = math_volatility_step(df_m15)
        z = df_final.iloc[-1]['Z_Score']
        rsi = df_final.iloc[-1]['RSI']
        info_extra = f"""
        [MEAN REVERSION DATA]
        - Z-Score: {z:.2f} (Extreme if > 2.0 or < -2.0)
        - RSI: {rsi:.2f}
        """
        
    return info_extra, classe

def tentar_ler_ativo(img, model, lista_ativos):
    prompt = "Read the Asset Name exactly. Return ONLY the name."
    try:
        response = model.generate_content([prompt, img])
        nome_raw = response.text.upper().strip().replace("INDEX", "").strip()
        for k, v in lista_ativos.items():
            k_clean = k.replace("INDEX", "").strip()
            if nome_raw in k_clean or k_clean in nome_raw: return k, v
        return None, None
    except: return None, None

def enviar_telegram(token, chat_id, msg):
    try:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                     json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})
    except: pass

# --- INTERFACE PRINCIPAL ---
st.sidebar.header("⚙️ SI-QA TITAN")
if "GEMINI_API_KEY" in st.secrets: api_key = st.secrets["GEMINI_API_KEY"]
else: api_key = st.sidebar.text_input("Gemini API Key", type="password")

st.sidebar.divider()
tg_token = st.sidebar.text_input("Bot Token", type="password")
tg_chat = st.sidebar.text_input("Chat ID")

st.sidebar.divider()
modo_operacao = st.sidebar.radio("Modo:", ["Análise Visual (TITAN)", "Radar Auto (Telegram)"])

with st.spinner("Conectando Deriv..."):
    LISTA_ATIVOS = buscar_lista_ativos_deriv()
if not LISTA_ATIVOS: st.stop()

# ==========================================================
# MODO 1: ANÁLISE VISUAL TITAN
# ==========================================================
if modo_operacao == "Análise Visual (TITAN)":
    st.title("🧬 SI-QA: TITAN Adaptive")
    
    col1, col2, col3 = st.columns(3)
    with col1: img_m15 = st.file_uploader("1. M15", type=['png', 'jpg'])
    with col2: img_h1 = st.file_uploader("2. H1", type=['png', 'jpg'])
    with col3: img_h4 = st.file_uploader("3. H4", type=['png', 'jpg'])
    
    # Seletor Manual (Fail-Safe)
    ativo_manual = st.selectbox("Seletor Manual (Backup):", ["Automático (IA)"] + list(LISTA_ATIVOS.keys()))
    
    if st.button("ATIVAR NÚCLEO TITAN"):
        if not api_key: st.error("Falta API Key."); st.stop()
        img_p = img_m15 if img_m15 else (img_h1 if img_h1 else img_h4)
        if not img_p: st.error("Envie imagens."); st.stop()
        
        status = st.status("Processando...", expanded=True)
        genai.configure(api_key=api_key)
        
        # 1. Identificação
        nome_ativo = None; codigo_ativo = None
        if ativo_manual != "Automático (IA)":
            nome_ativo = ativo_manual; codigo_ativo = LISTA_ATIVOS[ativo_manual]
            status.write(f"⚠️ Seleção Manual: {nome_ativo}")
        else:
            try: model_vision = genai.GenerativeModel("models/gemini-1.5-flash")
            except: model_vision = genai.GenerativeModel("models/gemini-1.5-flash")
            nome_ativo, codigo_ativo = tentar_ler_ativo(Image.open(img_p), model_vision, LISTA_ATIVOS)
            if not nome_ativo: st.warning("IA não leu o nome. Use o Seletor Manual."); st.stop()
        
        status.write(f"✅ Ativo: {nome_ativo}")
        
        # 2. Dados
        c_m15, c_h4, erro = asyncio.run(get_raw_data(codigo_ativo))
        if erro: st.error(erro); st.stop()
        
        # 3. Processamento Adaptativo
        status.write("🧠 Detectando Classe do Ativo...")
        df_m15 = pd.DataFrame(c_m15)
        relatorio_math, classe_ativo = processar_dados_inteligentes(nome_ativo, df_m15)
        
        status.write(f"🧬 Protocolo Ativado: **{classe_ativo}**")
        
        # 4. Prompt Gemini 3.0
        try: model_logic = genai.GenerativeModel("models/gemini-3-flash-preview", safety_settings=SAFETY_SETTINGS)
        except: model_logic = genai.GenerativeModel("models/gemini-1.5-flash", safety_settings=SAFETY_SETTINGS)
        
        inputs = [SYSTEM_PROMPT]
        contexto = "CHARTS PROVIDED:\n"
        if img_m15: inputs.append(Image.open(img_m15)); contexto+="- M15\n"
        if img_h1: inputs.append(Image.open(img_h1)); contexto+="- H1\n"
        if img_h4: inputs.append(Image.open(img_h4)); contexto+="- H4\n"
        
        prompt_injecao = f"""
        TARGET: {nome_ativo}
        DETECTED CLASS: {classe_ativo}
        {contexto}
        
        === ADAPTIVE MATH DATA ===
        {relatorio_math}
        
        TASK: Execute analysis using ONLY the rules for {classe_ativo}.
        """
        inputs.append(prompt_injecao)
        
        try:
            status.write("🧠 Decodificando...")
            resp = model_logic.generate_content(inputs)
            status.update(label="Sucesso", state="complete")
            st.divider()
            st.markdown(resp.text)
            st.info(f"📊 **Dados Técnicos Usados:**\n{relatorio_math}")
        except Exception as e:
            if "429" in str(e): st.warning("Cota Gemini 3.0 excedida. Aguarde 30s.")
            else: st.error(f"Erro: {e}")

# ==========================================================
# MODO 2: RADAR AUTOMÁTICO
# ==========================================================
elif modo_operacao == "Radar Auto (Telegram)":
    st.title("📡 Radar Adaptativo (24/7)")
    alvos = st.multiselect("Ativos:", list(LISTA_ATIVOS.keys()), default=["CRASH 1000 INDEX"])
    
    if st.button("ATIVAR VIGILÂNCIA"):
        if not tg_token: st.error("Falta Telegram"); st.stop()
        st.success("Radar TITAN Ativo.")
        enviar_telegram(tg_token, tg_chat, "📡 RADAR TITAN INICIADO")
        
        ph = st.empty()
        while True:
            log = []
            for nome in alvos:
                try:
                    codigo = LISTA_ATIVOS[nome]
                    c_m15, c_h4, _ = asyncio.run(get_raw_data(codigo))
                    
                    if c_m15:
                        df_m15 = pd.DataFrame(c_m15)
                        # O Radar também é adaptativo agora!
                        math_report, classe = processar_dados_inteligentes(nome, df_m15)
                        
                        # Simples lógica de alerta baseada na string de retorno
                        msg = ""
                        
                        # Logica Crash/Boom
                        if "SPIKE" in classe:
                            if "Trend (EMA 200): BULLISH" in math_report and "BOOM" in nome:
                                msg = f"🚀 **{nome}**\nProtocolo A: Tendência de Alta em BOOM"
                            elif "Trend (EMA 200): BEARISH" in math_report and "CRASH" in nome:
                                msg = f"🔻 **{nome}**\nProtocolo A: Tendência de Baixa em CRASH"
                        
                        # Logica Step/V75
                        elif "Extreme" in math_report: # Z-Score > 2
                            msg = f"⚡ **{nome}**\nProtocolo C: Z-Score Extremo (Reversão Possível)"
                        
                        if msg:
                            enviar_telegram(tg_token, tg_chat, msg)
                            log.append(f"{nome}: ALERTA ✅")
                        else:
                            log.append(f"{nome}: Monitorando...")
                except: pass
                time.sleep(1)
            ph.code("\n".join(log))
            time.sleep(60)


