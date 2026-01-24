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
    page_title="SI-QA: Golden Ratio (Fixed)",
    page_icon="✨",
    layout="wide"
)

# --- ESTILO VISUAL ---
st.markdown("""
<style>
    .stApp { background-color: #000000; color: #00ff00; font-family: 'Courier New', monospace; }
    .stButton>button { background-color: #004d00; color: #ffffff; border: 1px solid #00ff00; font-weight: bold; width: 100%; }
    div[data-testid="stExpander"] { border: 1px solid #00ff00; background-color: #0a0a0a; }
    h1, h2, h3 { color: #00ff00 !important; }
    .stSuccess { background-color: #064000; color: white; border: 1px solid #00ff00; }
    .stWarning { background-color: #332b00; color: #ffcc00; border: 1px solid #ffcc00; }
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
# PROMPT MESTRE
# ==============================================================================
SYSTEM_PROMPT = """
( ROLE & SYSTEM KERNEL
You are the "Synthetic Indices Quantum Architect" (SI-QA).
You interpret the "Golden Protocol" (Z-Score + RSI + Fibonacci).

>> YOUR DNA:
1. You DO NOT guess. You validate signals based on Mathematical Confluence.
2. A "Sniper Entry" requires price to be at a Key Level (Support/Resistance) OR a Fibonacci Zone (61.8%).
3. You must act as a Risk Manager: If the Backtest Win Rate < 65%, advise CAUTION.

 CRITICAL INPUT PROTOCOL
User provides:
A) 3 Charts (M15, H1, H4).
B) Backtest Report (Probability).
C) Fibonacci & Indicator Data.

 PHASE 1: THE HIERARCHY CHECK
- Look at H4 first. Is it at a major Level?
- Look at H1. Is it trending?
- Look at M15. Is it giving a trigger?

 PHASE 2: THE GOLDEN CHECK (PYTHON DATA)
- Check the "FIBONACCI STATUS". Is price near the 61.8% Golden Pocket?
- Check Z-Score (Overextended) and RSI.
- IF Price is at Fib 61.8% AND Z-Score is extreme -> EXECUTE.

 PHASE 3: DECISION MATRIX
- IF H4 Structure is Dominant -> Signal is SWING TRADE.
- IF H4 is Ranging but H1 is Trending -> Signal is DAY TRADE.

 OUTPUT TERMINAL:
(Render this specifically)

/// SI-QA GOLDEN KERNEL ///
[TARGET: {Asset} | MODE: {Swing/Day}]

>> MATHEMATICAL CONFLUENCE:
   1. FIBONACCI ZONE: {Hit/Near/Far} (Distance to 61.8% level)
   2. Z-SCORE STATUS: {Value}
   3. RSI STATUS: {Value}
   4. BACKTEST ACCURACY: {Win Rate}%

>> STRATEGY EXECUTION:
    ACTION: {BUY / SELL / WAIT}
    CONFIDENCE: {HIGH/MEDIUM/LOW}
    ENTRY ZONE: {Price}
    STOP LOSS: {Price - Structural}
    TAKE PROFIT 1: {Fibonacci 0% or -27%}

>> QUANTUM REASONING:
    {Explain the confluence. Mention if the "Golden Pocket" (61.8%) is active.}
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
    uri = "wss://ws.binaryws.com/websockets/v3?app_id=1089"
    try:
        async with websockets.connect(uri) as websocket:
            req_m15 = {"ticks_history": symbol_code, "adjust_start_time": 1, "count": 2000, "end": "latest", "style": "candles", "granularity": 900}
            req_h1 = {"ticks_history": symbol_code, "adjust_start_time": 1, "count": 200, "end": "latest", "style": "candles", "granularity": 3600}
            req_h4 = {"ticks_history": symbol_code, "adjust_start_time": 1, "count": 300, "end": "latest", "style": "candles", "granularity": 14400}
            
            await websocket.send(json.dumps(req_m15)); res_m15 = await websocket.recv()
            await websocket.send(json.dumps(req_h1)); res_h1 = await websocket.recv()
            await websocket.send(json.dumps(req_h4)); res_h4 = await websocket.recv()
            
            d_m15 = json.loads(res_m15)
            d_h1 = json.loads(res_h1)
            d_h4 = json.loads(res_h4)
            
            if 'error' in d_m15 or 'error' in d_h1 or 'error' in d_h4: return None, None, None, "Erro API"
            return d_m15['candles'], d_h1['candles'], d_h4['candles'], None
    except Exception as e:
        return None, None, None, str(e)

# --- MATEMÁTICA AVANÇADA ---

def calcular_rsi(series, period=14):
    delta = series.diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calcular_indicadores(df):
    df['close'] = df['close'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    
    df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['EMA_200'] = df['close'].ewm(span=200, adjust=False).mean()
    df['SMA_20'] = df['close'].rolling(window=20).mean()
    df['STD_20'] = df['close'].rolling(window=20).std()
    df['Z_Score'] = (df['close'] - df['SMA_20']) / df['STD_20']
    df['RSI'] = calcular_rsi(df['close'], 14)
    return df.dropna()

def detectar_fibonacci_macro(df_macro):
    last_price = df_macro.iloc[-1]['close']
    trend_up = last_price > df_macro.iloc[-1]['EMA_200']
    
    max_h = df_macro['high'].tail(100).max()
    min_l = df_macro['low'].tail(100).min()
    diff = max_h - min_l
    
    fib_status = "NO ZONE"
    golden_level = 0
    
    if trend_up:
        golden_level = max_h - (diff * 0.618)
        if abs(last_price - golden_level) < (last_price * 0.005):
            fib_status = "⚠️ GOLDEN POCKET (BUY ZONE)"
    else:
        golden_level = min_l + (diff * 0.618)
        if abs(last_price - golden_level) < (last_price * 0.005):
            fib_status = "⚠️ GOLDEN POCKET (SELL ZONE)"
            
    return fib_status, golden_level

# CORREÇÃO: Função renomeada para 'rodar_backtest_estatistico'
def rodar_backtest_estatistico(df):
    total = len(df)
    if total < 500: return "Dados insuficientes."
    wins = 0; losses = 0; sinais = 0
    for i in range(50, total - 20):
        row = df.iloc[i]
        # Confluência: Z-Score + RSI
        if row['Z_Score'] > 2.0 and row['RSI'] > 70:
            sinais += 1; outcome = "LOSS"
            for future_i in range(i+1, min(i+16, total)):
                if df.iloc[future_i]['low'] <= df.iloc[future_i]['EMA_20']:
                    wins += 1; outcome = "WIN"; break
            if outcome == "LOSS": losses += 1
        elif row['Z_Score'] < -2.0 and row['RSI'] < 30:
            sinais += 1; outcome = "LOSS"
            for future_i in range(i+1, min(i+16, total)):
                if df.iloc[future_i]['high'] >= df.iloc[future_i]['EMA_20']:
                    wins += 1; outcome = "WIN"; break
            if outcome == "LOSS": losses += 1
    win_rate = (wins / sinais * 100) if sinais > 0 else 0
    return f"WIN RATE: {win_rate:.1f}% ({sinais} Sinais)"

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

# --- FUNÇÕES TELEGRAM ---
def enviar_telegram(token, chat_id, msg):
    try:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                     json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})
    except: pass

# --- INTERFACE ---
st.sidebar.header("⚙️ SI-QA GOLDEN")
if "GEMINI_API_KEY" in st.secrets: api_key = st.secrets["GEMINI_API_KEY"]
else: api_key = st.sidebar.text_input("Gemini API Key", type="password")

st.sidebar.divider()
tg_token = st.sidebar.text_input("Bot Token", type="password")
tg_chat = st.sidebar.text_input("Chat ID")

st.sidebar.divider()
modo_operacao = st.sidebar.radio("Modo:", ["Análise Visual (Fibonacci)", "Radar Auto (Fibonacci)"])

with st.spinner("Conectando..."):
    LISTA_ATIVOS = buscar_lista_ativos_deriv()
if not LISTA_ATIVOS: st.stop()

# ==========================================================
# MODO 1: ANÁLISE VISUAL COM FIBONACCI
# ==========================================================
if modo_operacao == "Análise Visual (Fibonacci)":
    st.title("✨ SI-QA: Golden Ratio Analysis")
    
    col1, col2, col3 = st.columns(3)
    with col1: img_m15 = st.file_uploader("1. M15", type=['png', 'jpg'])
    with col2: img_h1 = st.file_uploader("2. H1", type=['png', 'jpg'])
    with col3: img_h4 = st.file_uploader("3. H4", type=['png', 'jpg'])
    
    ativo_manual = st.selectbox("Seletor Manual (Backup):", ["Automático (IA)"] + list(LISTA_ATIVOS.keys()))
    
    if st.button("CALCULAR FIBONACCI & SINAL"):
        if not api_key: st.error("Falta API Key."); st.stop()
        img_p = img_m15 if img_m15 else (img_h1 if img_h1 else img_h4)
        if not img_p: st.error("Envie imagens."); st.stop()
        
        status = st.status("Calculando Níveis Matemáticos...", expanded=True)
        genai.configure(api_key=api_key)
        
        # Identificação
        nome_ativo = None; codigo_ativo = None
        if ativo_manual != "Automático (IA)":
            nome_ativo = ativo_manual; codigo_ativo = LISTA_ATIVOS[ativo_manual]
        else:
            try: model_vision = genai.GenerativeModel("models/gemini-1.5-flash")
            except: model_vision = genai.GenerativeModel("models/gemini-1.5-flash")
            nome_ativo, codigo_ativo = tentar_ler_ativo(Image.open(img_p), model_vision, LISTA_ATIVOS)
            if not nome_ativo: st.warning("Selecione o ativo manualmente."); st.stop()
        
        status.write(f"✅ Ativo: {nome_ativo}")
        
        # Dados
        c_m15, c_h1, c_h4, erro = asyncio.run(get_platinum_data(codigo_ativo))
        if erro: st.error(erro); st.stop()
        
        df_m15 = calcular_indicadores(pd.DataFrame(c_m15))
        df_h4 = calcular_indicadores(pd.DataFrame(c_h4)) # Macro para Fib
        
        # CÁLCULO FIBONACCI
        status.write("📐 Traçando Fibonacci no H4...")
        fib_msg, fib_price = detectar_fibonacci_macro(df_h4)
        
        # Backtest (CHAMADA CORRIGIDA)
        status.write("🧮 Rodando Backtest...")
        backtest_msg = rodar_backtest_estatistico(df_m15)
        
        # Prompt
        try: model_logic = genai.GenerativeModel("models/gemini-3-flash-preview", safety_settings=SAFETY_SETTINGS)
        except: model_logic = genai.GenerativeModel("models/gemini-1.5-flash", safety_settings=SAFETY_SETTINGS)
        
        inputs = [SYSTEM_PROMPT]
        contexto = "IMAGES:\n"
        if img_m15: inputs.append(Image.open(img_m15))
        if img_h1: inputs.append(Image.open(img_h1))
        if img_h4: inputs.append(Image.open(img_h4))
        
        prompt_injecao = f"""
        TARGET: {nome_ativo}
        {contexto}
        
        === GOLDEN DATA ===
        [FIBONACCI H4]: {fib_msg} (Golden Level Price: {fib_price:.2f})
        [M15 INDICATORS]: Z-Score {df_m15.iloc[-1]['Z_Score']:.2f} | RSI {df_m15.iloc[-1]['RSI']:.2f}
        [BACKTEST]: {backtest_msg}
        
        TASK:
        If Price is near Fibonacci 61.8% AND Indicators are extreme -> STRONG SIGNAL.
        """
        inputs.append(prompt_injecao)
        
        try:
            status.write("🧠 Gerando Sinal...")
            resp = model_logic.generate_content(inputs)
            status.update(label="Concluído", state="complete")
            st.divider()
            st.markdown(resp.text)
            st.info(f"📊 **Dados Matemáticos:**\n\nFibonacci Status: **{fib_msg}**\nNível 61.8%: {fib_price:.2f}")
        except Exception as e:
            if "429" in str(e): st.warning("Limite Gemini atingido. Aguarde.")
            else: st.error(f"Erro: {e}")

# ==========================================================
# MODO 2: RADAR FIBONACCI
# ==========================================================
elif modo_operacao == "Radar Auto (Fibonacci)":
    st.title("📡 Radar Fibonacci (Golden Pocket)")
    st.markdown("Avisa quando o preço toca na retração de **61.8% do H4**.")
    alvos = st.multiselect("Ativos:", list(LISTA_ATIVOS.keys()), default=["CRASH 1000 INDEX"])
    
    if st.button("ATIVAR"):
        if not tg_token: st.error("Falta Telegram"); st.stop()
        st.success("Radar Fibonacci Ativo.")
        enviar_telegram(tg_token, tg_chat, "📡 RADAR FIBONACCI INICIADO")
        
        ph = st.empty()
        while True:
            log = []
            for nome in alvos:
                try:
                    codigo = LISTA_ATIVOS[nome]
                    c_m15, _, c_h4, _ = asyncio.run(get_platinum_data(codigo))
                    if c_m15 and c_h4:
                        df_ma = calcular_indicadores(pd.DataFrame(c_h4))
                        fib_status, fib_price = detectar_fibonacci_macro(df_ma)
                        
                        if "GOLDEN POCKET" in fib_status:
                            current = df_ma.iloc[-1]['close']
                            msg = f"✨ **{nome}**\nPREÇO NO GOLDEN POCKET (61.8%)!\nPreço: {current}\nNível Fib: {fib_price:.2f}"
                            enviar_telegram(tg_token, tg_chat, msg)
                            log.append(f"{nome}: SINAL FIBONACCI ✅")
                        else:
                            log.append(f"{nome}: Longe do Fib...")
                except: pass
                time.sleep(1)
            ph.code("\n".join(log))
            time.sleep(60)


