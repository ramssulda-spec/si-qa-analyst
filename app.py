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
    page_title="SI-APATECO PRO v3.1",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILO VISUAL (SI-APATECO NEXT-GEN UI) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Roboto:wght@300;400;700&display=swap');
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .stApp {
        background-color: #050505;
        background-image: radial-gradient(circle at 50% 0%, #1a2e1a 0%, #050505 60%);
        font-family: 'Roboto', sans-serif;
    }

    h1 {
        font-family: 'Orbitron', sans-serif !important;
        background: linear-gradient(90deg, #00ff88, #00b8ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 20px rgba(0, 255, 136, 0.3);
        font-weight: 700 !important;
        letter-spacing: 2px;
    }
    
    h2, h3 {
        color: #e0e0e0 !important;
        font-family: 'Orbitron', sans-serif !important;
    }

    div[data-testid="stExpander"], div.stFileUploader {
        background: rgba(20, 20, 25, 0.6);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        transition: transform 0.2s ease, border-color 0.2s ease;
        animation: fadeIn 0.6s ease-out;
    }
    
    div[data-testid="stExpander"]:hover {
        border-color: rgba(0, 255, 136, 0.4);
    }

    .stButton>button {
        background: linear-gradient(135deg, #00b09b 0%, #96c93d 100%);
        color: #000;
        font-family: 'Orbitron', sans-serif;
        font-weight: bold;
        border: none;
        border-radius: 8px;
        padding: 18px 32px;
        font-size: 18px;
        text-transform: uppercase;
        letter-spacing: 2px;
        width: 100%;
        box-shadow: 0 4px 15px rgba(0, 255, 136, 0.2);
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    }

    .stButton>button:hover {
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 8px 30px rgba(0, 255, 136, 0.6);
        background: linear-gradient(135deg, #00d4bb 0%, #aee04d 100%);
    }

    /* Inputs e Status */
    .stSelectbox>div>div>div, .stTextInput>div>div>input {
        background-color: rgba(255, 255, 255, 0.05);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .stSuccess, .stInfo, .stWarning, .stError {
        border-radius: 8px;
        backdrop-filter: blur(5px);
        animation: fadeIn 0.4s ease-out;
    }
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
# PROMPT MESTRE (V3.0 - CONFLUÊNCIA TOTAL)
# ==============================================================================
SYSTEM_PROMPT = """
( ROLE: SI-APATECO ELITE QUANT ANALYST v3.0
You are an advanced Synthetic Indices Trading Engine.
Your Signal precision relies on the CONFLUENCE of 3 layers:

1. THE MATH LAYER (Provided Python Data):
   - You MUST respect the "H4 Bias" (Trend). 
     -> If H4 is Bearish, DO NOT suggest Longs unless clearly a scalp pullback.
   - You MUST respect RSI. 
     -> If RSI > 70 (Overbought), Sell probability increases.
     -> If RSI < 30 (Oversold), Buy probability increases.
   - ADX < 20 means Accumulation (Expect liquidity sweeps). ADX > 25 means Trend (Expect Pullbacks).

2. THE VISUAL LAYER (SMC/ICT Concepts):
   - Identify "Order Blocks" (Last opposite candle before a move).
   - Identify "Fair Value Gaps" (FVG) / Imbalances.
   - Identify "Liquidity Pools" (Equal Highs/Lows) that price might magnet to.

3. THE ASSET PROTOCOLS:
   - BOOM INDICES: Prioritize SPIKES (Buys). Only Sell if Structure is broken on H1/H4.
   - CRASH INDICES: Prioritize DROPS (Sells). Only Buy if Structure is broken on H1/H4.
   - VOLATILITY/STEP: Pure Price Action + RSI Divergence.

OUTPUT STRICT TEMPLATE:

/// 💠 SI-APATECO VERDICT 3.0 ///

[ASSET: {name} | BIAS: {Bullish/Bearish/Neutral}]

>> 1. QUANTITATIVE ALIGNMENT
   - H4 TREND BIAS: {From Python Data}
   - M15 MOMENTUM: RSI {Value} | ADX {Value}
   - MATH CONFLUENCE SCORE: {0 to 10}/10

>> 2. VISUAL SMC CONFIRMATION
   - STRUCTURE: {Is price making HH/HL or LH/LL?}
   - KEY ZONE: {Describe the closest Order Block or FVG identified in image}
   - LIQUIDITY TARGET: {Where is the Stop Loss liquidity located?}

>> 3. EXECUTION ORDER
   ⚡ SIGNAL: {STRONG BUY / WEAK BUY / WAIT / WEAK SELL / STRONG SELL}
   
   📍 ENTRY ZONE: {Specific price level based on Image visual support/resistance}
   🛑 STOP LOSS (STRUCTURAL): {Level below prev Swing Low for Buy / above Swing High for Sell}
   🎯 TAKE PROFIT (LIQUIDITY): {Level of next Liquidity Pool}

>> REASONING:
   {Explain: "Math aligns with Vision. H4 Bearish + M15 Bearish Flag + RSI Cooling down. High probability short at retest of FVG."}
)
"""

# --- FUNÇÕES API DERIV ---

@st.cache_data(ttl=3600)
def buscar_lista_ativos_deriv():
    async def _fetch():
        uri = "wss://ws.binaryws.com/websockets/v3?app_id=1089"
        try:
            async with websockets.connect(uri) as ws:
                req = {"active_symbols": "brief", "product_type": "basic"}
                await ws.send(json.dumps(req))
                res = await asyncio.wait_for(ws.recv(), timeout=5.0)
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
            # Baixa 2000 velas de M15 (Gatilho) e 200 de H4 (Tendência)
            req_m15 = {"ticks_history": symbol_code, "adjust_start_time": 1, "count": 2000, "end": "latest", "style": "candles", "granularity": 900}
            req_h4 = {"ticks_history": symbol_code, "adjust_start_time": 1, "count": 200, "end": "latest", "style": "candles", "granularity": 14400}
            
            await websocket.send(json.dumps(req_m15))
            res_m15 = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            
            await websocket.send(json.dumps(req_h4))
            res_h4 = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            
            d_m15 = json.loads(res_m15)
            d_h4 = json.loads(res_h4)
            
            if 'error' in d_m15 or 'error' in d_h4: return None, None, "Erro API Deriv (Dados inválidos)"
            return d_m15['candles'], d_h4['candles'], None
            
    except asyncio.TimeoutError:
        return None, None, "Erro: Deriv demorou muito para responder (Timeout)."
    except Exception as e: 
        return None, None, str(e)

# ==============================================================================
# --- NÚCLEOS MATEMÁTICOS ADAPTATIVOS 3.0 ---
# ==============================================================================

def math_common(df):
    """Limpeza e tipagem dos dados"""
    cols = ['open', 'high', 'low', 'close', 'epoch']
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

def math_get_rsi(series, period=14):
    """Cálculo robusto do RSI para detectar exaustão"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-9)
    return 100 - (100 / (1 + rs))

def math_advanced_indicators(df_m15, df_h4):
    """
    Motor Central de Cálculo:
    Calcula M15 e importa a tendência do H4 para contexto MTF (Multi-Timeframe).
    """
    # 1. PROCESSAMENTO H4 (CONTEXTO MACRO)
    df_h4['EMA_50'] = df_h4['close'].ewm(span=50, adjust=False).mean()
    df_h4.dropna(inplace=True)
    
    if len(df_h4) > 0:
        last_h4 = df_h4.iloc[-1]
        macro_trend = "BULLISH" if last_h4['close'] > last_h4['EMA_50'] else "BEARISH"
    else:
        macro_trend = "NEUTRAL"

    # 2. PROCESSAMENTO M15 (GATILHO)
    df_m15['EMA_20'] = df_m15['close'].ewm(span=20, adjust=False).mean()
    df_m15['EMA_200'] = df_m15['close'].ewm(span=200, adjust=False).mean()
    
    # RSI (Novo)
    df_m15['RSI'] = math_get_rsi(df_m15['close'])
    
    # Bollinger Bands
    df_m15['BB_Mid'] = df_m15['close'].rolling(window=20).mean()
    df_m15['BB_Std'] = df_m15['close'].rolling(window=20).std()
    df_m15['BB_Upper'] = df_m15['BB_Mid'] + (2 * df_m15['BB_Std'])
    df_m15['BB_Lower'] = df_m15['BB_Mid'] - (2 * df_m15['BB_Std'])
    
    # Z-Score
    df_m15['Z_Score'] = (df_m15['close'] - df_m15['BB_Mid']) / (df_m15['BB_Std'] + 1e-9)
    
    # ATR e ADX
    high_low = df_m15['high'] - df_m15['low']
    high_close = np.abs(df_m15['high'] - df_m15['close'].shift())
    low_close = np.abs(df_m15['low'] - df_m15['close'].shift())
    true_range = np.max(pd.concat([high_low, high_close, low_close], axis=1), axis=1)
    df_m15['ATR'] = true_range.rolling(14).mean()

    plus_dm = df_m15['high'].diff().clip(lower=0)
    minus_dm = df_m15['low'].diff().clip(lower=0)
    tr_rolling = true_range.rolling(14).sum()
    plus_di = 100 * (plus_dm.rolling(14).sum() / tr_rolling)
    minus_di = 100 * (minus_dm.rolling(14).sum() / tr_rolling)
    dx = (np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-9)) * 100
    df_m15['ADX'] = dx.rolling(14).mean()

    # Injeta a tendência do H4 em cada linha do M15
    df_m15['MACRO_TREND'] = macro_trend
    
    df_m15.dropna(inplace=True)
    return df_m15

def rodar_backtest_pro(df, classe_ativo):
    total = len(df)
    if total < 500: return "Dados insuficientes para Backtest Robusto."
    
    wins = 0; losses = 0; total_trades = 0
    profit_acc = 0 # EM Unidade de Risco
    
    risk_reward = 1.5 
    
    for i in range(200, total - 50):
        row = df.iloc[i]
        macro = row['MACRO_TREND']
        sinal = None 

        # --- ESTRATÉGIAS V3 (MTF CONFLUENCE) ---
        
        # 1. SPIKES (Protocolo A)
        if "PROTOCOL A" in classe_ativo:
            if "BOOM" in classe_ativo and macro == "BULLISH":
                 if row['close'] > row['EMA_200'] and row['RSI'] < 40: 
                     sinal = 'BUY'
            
            elif "CRASH" in classe_ativo and macro == "BEARISH":
                if row['close'] < row['EMA_200'] and row['RSI'] > 60:
                    sinal = 'SELL'

        # 2. VOLATILIDADE/STEP
        else:
            adx = row['ADX']
            if adx < 25:
                if row['close'] > row['BB_Upper'] and row['RSI'] > 70: sinal = 'SELL'
                if row['close'] < row['BB_Lower'] and row['RSI'] < 30: sinal = 'BUY'
            elif adx > 25:
                if macro == "BULLISH" and row['close'] > row['BB_Upper']: sinal = 'BUY'
                if macro == "BEARISH" and row['close'] < row['BB_Lower']: sinal = 'SELL'

        # --- EXECUÇÃO VIRTUAL ---
        if sinal:
            entry = row['close']
            atr = row['ATR']
            
            # SL Dinâmico 2.5x ATR
            atr_mult = 2.5
            
            if sinal == 'BUY':
                sl = entry - (atr * atr_mult) 
                tp = entry + (atr * atr_mult * risk_reward)
            else:
                sl = entry + (atr * atr_mult)
                tp = entry - (atr * atr_mult * risk_reward)
            
            total_trades += 1
            outcome = "OPEN"
            
            for future_i in range(i+1, min(i+100, total)):
                f_row = df.iloc[future_i]
                if sinal == 'BUY':
                    if f_row['low'] <= sl: outcome = "LOSS"; break
                    if f_row['high'] >= tp: outcome = "WIN"; break
                else:
                    if f_row['high'] >= sl: outcome = "LOSS"; break
                    if f_row['low'] <= tp: outcome = "WIN"; break
            
            if outcome == "WIN": 
                wins += 1; profit_acc += risk_reward
            elif outcome == "LOSS": 
                losses += 1; profit_acc -= 1

    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
    ev = (profit_acc / total_trades) if total_trades > 0 else 0
    
    color = "🟢" if ev > 0.3 else "🔴"
    
    return f"""
    [PRECISION ENGINE 3.0 LOGS]
    - H4/M15 Alignment Check: ACTIVE
    - Trades Found: {total_trades}
    - Win Rate: {win_rate:.1f}%
    - Expectancy (EV): {ev:.2f}R per trade
    - Strategy Bias: {color} {'POSITIVE' if ev > 0 else 'NEGATIVE'}
    """

def processar_dados_inteligentes(nome_ativo, c_m15_raw, c_h4_raw):
    df_m15 = pd.DataFrame(c_m15_raw)
    df_h4 = pd.DataFrame(c_h4_raw)
    
    df_m15 = math_common(df_m15)
    df_h4 = math_common(df_h4)
    
    # Processa indicadores
    df_final = math_advanced_indicators(df_m15, df_h4)
    
    if len(df_final) == 0:
        return "N/A", "Unknown", "Insufficient Data"
    
    last = df_final.iloc[-1]
    info_extra = f"Bias(H4): {last['MACRO_TREND']} | RSI: {last['RSI']:.1f} | ADX: {last['ADX']:.1f}"
    
    if "CRASH" in nome_ativo or "BOOM" in nome_ativo: 
        classe = "PROTOCOL A: SPIKE INDICES"
    elif "STEP" in nome_ativo: 
        classe = "PROTOCOL B: DISCRETE INDICES"
    else: 
        classe = "PROTOCOL C: FLUID INDICES"
        
    relatorio_backtest = rodar_backtest_pro(df_final, classe)
    
    return info_extra, classe, relatorio_backtest

def tentar_ler_ativo(img, model, lista_ativos):
    prompt = "Read the Asset Name exactly from the chart header (e.g., Crash 1000 Index). Return ONLY the name."
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
                     json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except: pass

# --- INTERFACE PRINCIPAL ---

st.sidebar.markdown("## ⚙️ Acesso Neural")
if "GEMINI_API_KEY" in st.secrets: api_key = st.secrets["GEMINI_API_KEY"]
else: api_key = st.sidebar.text_input("🔑 Gemini API Key", type="password")

st.sidebar.divider()
st.sidebar.markdown("## 📡 Rede Tática")
tg_token = st.sidebar.text_input("Bot Token", type="password")
tg_chat = st.sidebar.text_input("Chat ID")

st.sidebar.divider()
st.sidebar.markdown("## 🚀 Módulo")
modo_operacao = st.sidebar.radio("Escolha o modo:", ["Análise Visual (SI-APATECO)", "Radar Auto (Telegram)"])

with st.spinner("🔄 Estabelecendo Link Deriv..."):
    LISTA_ATIVOS = buscar_lista_ativos_deriv()
if not LISTA_ATIVOS: st.stop()

# ==========================================================
# MODO 1: ANÁLISE VISUAL SI-APATECO
# ==========================================================
if modo_operacao == "Análise Visual (SI-APATECO)":
    st.markdown("<h1 style='text-align: center; margin-bottom: 20px;'>💠 SI-APATECO <span style='font-size: 15px; color: #00ff88; vertical-align: top;'>PRO V3</span></h1>", unsafe_allow_html=True)
    
    with st.container():
        st.markdown("### 📤 Upload Tri-Force (SMC Data)")
        col1, col2, col3 = st.columns(3)
        with col1: img_m15 = st.file_uploader("📸 1. M15 (Entry Trigger)", type=['png', 'jpg'])
        with col2: img_h1 = st.file_uploader("📸 2. H1 (Structure)", type=['png', 'jpg'])
        with col3: img_h4 = st.file_uploader("📸 3. H4 (Liquidity)", type=['png', 'jpg'])
    
    st.divider()
    
    col_sel, col_btn = st.columns([2, 1])
    with col_sel:
        ativo_manual = st.selectbox("🛡️ Override Manual (Segurança):", ["Automático (IA)"] + list(LISTA_ATIVOS.keys()))
    
    with col_btn:
        st.write("")
        st.write("") 
        start_btn = st.button("🚀 EXECUTAR ANÁLISE")
    
    if start_btn:
        if not api_key: st.error("⚠️ Falta API Key."); st.stop()
        img_p = img_m15 if img_m15 else (img_h1 if img_h1 else img_h4)
        if not img_p: st.error("⚠️ Envie pelo menos uma imagem."); st.stop()
        
        status = st.status("🧠 Inicializando Core Neural (Gemini)...", expanded=True)
        genai.configure(api_key=api_key)
        
        # 1. Identificação
        nome_ativo = None; codigo_ativo = None
        if ativo_manual != "Automático (IA)":
            nome_ativo = ativo_manual; codigo_ativo = LISTA_ATIVOS[ativo_manual]
            status.write(f"🛡️ Modo Manual Ativado: **{nome_ativo}**")
        else:
            try: model_vision = genai.GenerativeModel("models/gemini-3-flash-preview")
            except: model_vision = genai.GenerativeModel("models/gemini-3-flash-preview")
            status.write("👁️ Vision AI escaneando ativo...")
            try:
                nome_ativo, codigo_ativo = tentar_ler_ativo(Image.open(img_p), model_vision, LISTA_ATIVOS)
            except Exception: pass
            
            # --- CORREÇÃO APLICADA AQUI: state='error' ---
            if not nome_ativo: 
                status.update(label="Erro de Leitura", state="error") 
                st.warning("⚠️ IA não leu o nome. Use o seletor manual acima."); st.stop()
        
        status.write(f"✅ Target Confirmado: **{nome_ativo}**")
        
        # 2. Dados
        status.write("📡 Extraindo dados H4/M15 (API Deriv)...")
        c_m15, c_h4, erro = asyncio.run(get_raw_data(codigo_ativo))
        if erro: 
            status.update(label="Erro Conexão", state="error"); st.error(f"❌ Erro de Rede: {erro}"); st.stop()
        
        # 3. Processamento Matemático
        status.write("🧮 Rodando Motor Matemático (MTF & RSI)...")
        math_info, classe_ativo, backtest_info = processar_dados_inteligentes(nome_ativo, c_m15, c_h4)
        
        status.write(f"🧬 Protocolo: **{classe_ativo}**")
        status.write(f"📈 Dados Puros: {math_info}")
        
        # 4. Prompt Gemini
        try: model_logic = genai.GenerativeModel("models/gemini-3-pro-preview", safety_settings=SAFETY_SETTINGS)
        except: model_logic = genai.GenerativeModel("models/gemini-3-flash-preview", safety_settings=SAFETY_SETTINGS)
        
        inputs = [SYSTEM_PROMPT]
        contexto = "CHARTS PROVIDED:\n"
        if img_m15: inputs.append(Image.open(img_m15)); contexto+="- M15\n"
        if img_h1: inputs.append(Image.open(img_h1)); contexto+="- H1\n"
        if img_h4: inputs.append(Image.open(img_h4)); contexto+="- H4\n"
        
        prompt_injecao = f"""
        TARGET ASSET: {nome_ativo}
        DETECTED CLASS: {classe_ativo}
        {contexto}
        
        === QUANTITATIVE TRUTH (FROM PYTHON CODE) ===
        {math_info}
        
        === BACKTEST PROJECTION (200 Candles) ===
        {backtest_info}
        
        TASK: Synthesize the Math (H4 Bias + RSI) with Visuals. Strict adherence to prompt.
        """
        inputs.append(prompt_injecao)
        
        try:
            status.write("🤖 Gerando Veredito Final...")
            resp = model_logic.generate_content(inputs)
            status.update(label="Análise Concluída", state="complete")
            
            st.divider()
            st.markdown(resp.text)
            
            with st.expander("📊 Debugger (Dados do Robô)"):
                st.text("Motor Backtest V3.0:")
                st.code(backtest_info, language="text")
                st.text("Sinais:")
                st.code(math_info, language="text")
                
        except Exception as e:
            # --- CORREÇÃO APLICADA AQUI TAMBÉM ---
            if "429" in str(e): 
                st.warning("⚠️ Limite Gemini atingido. Aguarde 30s.")
                status.update(label="Pausa (Rate Limit)", state="error")
            else: st.error(f"❌ Erro IA: {e}")

# ==========================================================
# MODO 2: RADAR AUTOMÁTICO (ATUALIZADO PARA H4 ALIGNMENT)
# ==========================================================
elif modo_operacao == "Radar Auto (Telegram)":
    st.markdown("<h1 style='text-align: center;'>📡 Radar Adaptativo (V3.0)</h1>", unsafe_allow_html=True)
    st.info("Filtra Sinais falsos verificando a Tendência H4 antes de alertar.")
    
    alvos = st.multiselect("🎯 Selecione os ativos:", list(LISTA_ATIVOS.keys()), default=["CRASH 1000 INDEX"])
    
    if st.button("🟢 ATIVAR VIGILÂNCIA"):
        if not tg_token: st.error("Falta Telegram Token."); st.stop()
        st.success("Radar Ativo com Filtro H4.")
        enviar_telegram(tg_token, tg_chat, "📡 RADAR SI-APATECO V3 INICIADO")
        
        ph = st.empty()
        log_container = []
        
        while True:
            for nome in alvos:
                try:
                    codigo = LISTA_ATIVOS[nome]
                    c_m15, c_h4, _ = asyncio.run(get_raw_data(codigo))
                    
                    if c_m15 and c_h4:
                        m_info, classe, _ = processar_dados_inteligentes(nome, c_m15, c_h4)
                        
                        msg = ""
                        # Filtro Aprimorado
                        if "Bias(H4): BULLISH" in m_info and "BOOM" in nome:
                            # Verifica se o M15 está 'barato'
                            if "RSI" in m_info and float(m_info.split("RSI: ")[1].split(" |")[0]) < 40:
                                msg = f"🚀 **{nome}** (STRONG BUY)\nH4 Alta + M15 Sobrevendido"
                                
                        elif "Bias(H4): BEARISH" in m_info and "CRASH" in nome:
                            if "RSI" in m_info and float(m_info.split("RSI: ")[1].split(" |")[0]) > 60:
                                msg = f"🔻 **{nome}** (STRONG SELL)\nH4 Baixa + M15 Sobrecomprado"
                        
                        elif "PROTOCOL C" in classe: # Indices Volatilidade
                            if "RSI: " in m_info:
                                rsi_val = float(m_info.split("RSI: ")[1].split(" |")[0])
                                if rsi_val > 75: msg = f"⚠️ **{nome}** - Alerta Topo (RSI {rsi_val:.0f})"
                                if rsi_val < 25: msg = f"⚠️ **{nome}** - Alerta Fundo (RSI {rsi_val:.0f})"
                        
                        timestamp = time.strftime("%H:%M:%S")
                        if msg:
                            enviar_telegram(tg_token, tg_chat, msg)
                            log_container.insert(0, f"[{timestamp}] {nome}: 🚨 SENT")
                        else:
                            log_container.insert(0, f"[{timestamp}] {nome}: Scanning...")
                            
                except: pass
                time.sleep(1.5) 
            
            if len(log_container) > 10: log_container = log_container[:10]
            ph.code("\n".join(log_container))
            time.sleep(60)














