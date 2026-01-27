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
    page_title="SI-APATECO PRO",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILO VISUAL (SI-APATECO NEXT-GEN UI) ---
st.markdown("""
<style>
    /* Importando Fonte Futurista */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Roboto:wght@300;400;700&display=swap');

    /* Animação de Entrada */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Fundo Global Cyberpunk Clean */
    .stApp {
        background-color: #050505;
        background-image: radial-gradient(circle at 50% 0%, #1a2e1a 0%, #050505 60%);
        font-family: 'Roboto', sans-serif;
    }

    /* Títulos Principais */
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
        letter-spacing: 1px;
    }

    /* Cards e Containers (Glassmorphism) */
    div[data-testid="stExpander"], div.stFileUploader {
        background: rgba(20, 20, 25, 0.6);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        transition: transform 0.2s ease, border-color 0.2s ease;
        animation: fadeIn 0.6s ease-out;
    }
    
    div[data-testid="stExpander"]:hover {
        border-color: rgba(0, 255, 136, 0.4);
    }

    /* BOTÃO DE AÇÃO (MODERNO E ANIMADO) */
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
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(0, 255, 136, 0.2);
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        position: relative;
        overflow: hidden;
    }

    .stButton>button:hover {
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 8px 30px rgba(0, 255, 136, 0.6);
        background: linear-gradient(135deg, #00d4bb 0%, #aee04d 100%);
    }

    .stButton>button:active {
        transform: translateY(1px) scale(0.98);
        box-shadow: 0 2px 10px rgba(0, 255, 136, 0.3);
    }

    /* Inputs e Selects */
    .stSelectbox>div>div>div, .stTextInput>div>div>input {
        background-color: rgba(255, 255, 255, 0.05);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 6px;
    }
    
    /* Multiselect Tag */
    .stMultiSelect span[data-baseweb="tag"] {
        background-color: rgba(0, 255, 136, 0.2);
        border: 1px solid rgba(0, 255, 136, 0.5);
    }

    /* Status Messages */
    .stSuccess, .stInfo, .stWarning, .stError {
        border-radius: 8px;
        backdrop-filter: blur(5px);
        font-weight: 500;
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
# PROMPT MESTRE (SMC & INSTITUTIONAL v2.0)
# ==============================================================================
SYSTEM_PROMPT = """
( ROLE & SYSTEM KERNEL v2.0
You are "SI-APATECO PRIME", an Elite Quantitative Analyst for Deriv Markets.
Your analysis combines Python Statistical Data with Institutional Price Action (SMC).

>> HIERARCHY OF TRUTH:
1. MATH (ADX, Z-Score, Backtest) determines the REGIME (Trending vs Ranging).
2. STRUCTURE (H4) determines the DIRECTION.
3. SMC (Smart Money Concepts) determines the ENTRY.

>> DYNAMIC ASSET PROTOCOLS:

<PROTOCOL_A: SPIKE_INDICES (Crash/Boom)>
- PHYSICS: Asymmetric risk.
- SMC RULE: Look for "Order Blocks" or "Breaker Blocks" at the origin of previous moves.
- FILTER: If Python says "ADX > 30" in the opposite direction of the spike, SIGNAL IS INVALID (Do not catch a falling knife).
- TRIGGER: Price tapping an H1/H4 Order Block + M15 Rejection candle.

<PROTOCOL_B: DISCRETE_INDICES (Step/Jump)>
- PHYSICS: Accumulation vs Distribution.
- SMC RULE: Identify "Liquidity Sweeps" (Fakeouts) above/below consolidation boxes.
- TRIGGER: Break of Structure (BOS) after a Liquidity Sweep.

<PROTOCOL_C: FLUID_INDICES (Volatilities)>
- PHYSICS: Brownian Motion.
- QUANT RULE: Check Python Data "Strategy Lock". 
  - If "FOLLOW TREND": Ignore Overbought/Oversold. Buy high, Sell higher.
  - If "MEAN REVERSION": Short at Bollinger Upper Band + RSI > 70.
- TRIGGER: Fair Value Gap (FVG) retest or Equilibrium of the range.

 CRITICAL INPUT PROTOCOL
User provides:
A) Charts (Visual Price Action).
B) MATH DATA (ADX, ATR, Z-Score, Bollinger Status).
C) BACKTEST REALITY (Historical probability).

 OUTPUT TERMINAL (Strict Format):

/// SI-APATECO PRIME VERDICT ///
[ASSET: {Asset} | REGIME: {Trending/Ranging}]

>> QUANTITATIVE CHECK:
   - TREND STRENGTH (ADX): {Value} (Is the trend exhausted?)
   - STATISTICAL PROBABILITY: {Backtest Win Rate}%

>> SMC ANALYSIS (Vision AI):
   - STRUCTURE: {Bullish/Bearish Market Structure}
   - LIQUIDITY: {Where is the money? e.g., "Equal Highs above"}
   - INTEREST ZONE: {Order Block / FVG / Breaker Block}

>> EXECUTION PLAN:
    SIGNAL: {BUY / SELL / WAIT}
    CONFIDENCE: {0-100}%
    ENTRY ZONE: {Exact Price Area}
    STOP LOSS: {Structural Level}
    TAKE PROFIT: {Next Liquidity Pool}

>> REASONING:
    {Explain using SMC terms: "Price swept liquidity at low and rejected H4 Order Block with ADX supporting valid volatility."}
)
"""

# --- FUNÇÕES API COM TIMEOUT ---

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
            # Baixa 2000 velas de M15 para o Backtest Robusto
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

# --- NÚCLEOS MATEMÁTICOS ADAPTATIVOS 2.0 (High Precision) ---

def rodar_backtest_pro(df, classe_ativo):
    total = len(df)
    if total < 500: return "Dados insuficientes para Backtest Robusto."
    
    # Métricas
    wins = 0
    losses = 0
    total_trades = 0
    consecutive_loss = 0
    max_consecutive_loss = 0
    profit_accumulator = 0 # Para calcular Expectativa Matemática
    
    # Configuração de Risco (Simulação)
    risk_reward_ratio = 1.5 # Busca ganhar 1.5x o que arrisca
    atr_multiplier_sl = 2.0 # Stop Loss = 2x ATR
    
    for i in range(100, total - 50): # Margem segura
        row = df.iloc[i]
        
        # --- LÓGICA DE SINAL (GATILHOS) ---
        sinal = None # 'BUY' ou 'SELL'
        
        # Lógica para BOOM/CRASH (Spikes)
        if "PROTOCOL A" in classe_ativo:
            # Compra em Crash (Contra tendência - Perigoso, ignorar) ou Favor da Trend
            # Vamos testar apenas Trend Following (Segurança)
            if "BOOM" in classe_ativo and row['close'] > row['EMA_200']:
                # Pullback na média curta
                if row['low'] <= row['EMA_20'] and row['close'] > row['EMA_20']:
                    sinal = 'BUY'
            elif "CRASH" in classe_ativo and row['close'] < row['EMA_200']:
                if row['high'] >= row['EMA_20'] and row['close'] < row['EMA_20']:
                    sinal = 'SELL'
                    
        # Lógica para VOLATILITY/STEP (Reversão com Filtro ADX)
        elif "PROTOCOL B" in classe_ativo or "PROTOCOL C" in classe_ativo:
            adx = row['ADX'] if not pd.isna(row['ADX']) else 0
            
            # Se mercado lateral (ADX < 25), opera reversão (Z-Score)
            if adx < 25:
                if row['Z_Score'] > 2.0: sinal = 'SELL'
                elif row['Z_Score'] < -2.0: sinal = 'BUY'
            
            # Se mercado tendência (ADX > 25), opera rompimento (Bollinger)
            elif adx > 25:
                # Exemplo simples de Trend Follow
                if row['close'] > row['BB_Upper']: sinal = 'BUY'
                elif row['close'] < row['BB_Lower']: sinal = 'SELL'

        # --- SIMULAÇÃO DO TRADE (EVENT DRIVEN) ---
        if sinal:
            total_trades += 1
            entry_price = row['close']
            atr = row['ATR'] if not pd.isna(row['ATR']) else (entry_price * 0.001)
            
            # Definindo SL e TP Dinâmicos
            if sinal == 'BUY':
                sl_price = entry_price - (atr * atr_multiplier_sl)
                tp_price = entry_price + (atr * atr_multiplier_sl * risk_reward_ratio)
            else: # SELL
                sl_price = entry_price + (atr * atr_multiplier_sl)
                tp_price = entry_price - (atr * atr_multiplier_sl * risk_reward_ratio)
            
            # Caminhando no futuro para ver o resultado
            outcome = "OPEN"
            for future_i in range(i+1, min(i+100, total)): # Olha até 100 velas à frente
                f_row = df.iloc[future_i]
                
                if sinal == 'BUY':
                    if f_row['low'] <= sl_price: outcome = "LOSS"; break
                    if f_row['high'] >= tp_price: outcome = "WIN"; break
                else: # SELL
                    if f_row['high'] >= sl_price: outcome = "LOSS"; break
                    if f_row['low'] <= tp_price: outcome = "WIN"; break
            
            # Contabilização
            if outcome == "WIN":
                wins += 1
                profit_accumulator += (risk_reward_ratio) # Ganhou 1.5R
                consecutive_loss = 0
            elif outcome == "LOSS":
                losses += 1
                profit_accumulator -= 1.0 # Perdeu 1.0R
                consecutive_loss += 1
                if consecutive_loss > max_consecutive_loss: max_consecutive_loss = consecutive_loss

    # --- CÁLCULO DAS MÉTRICAS AVANÇADAS ---
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
    profit_factor = "N/A" # Evitar divisão por zero
    if losses > 0:
        # Simplificação: Como usamos Risco fixo, Profit Factor ≈ (Wins * Reward) / (Losses * 1)
        gross_profit = wins * risk_reward_ratio
        gross_loss = losses * 1.0
        pf_value = gross_profit / gross_loss
        profit_factor = f"{pf_value:.2f}"
    
    expected_value = (profit_accumulator / total_trades) if total_trades > 0 else 0
    
    # Classificação da Estratégia
    status_msg = "🔴 UNPROFITABLE"
    if expected_value > 0.2: status_msg = "🟡 MARGINAL"
    if expected_value > 0.5: status_msg = "🟢 PROFITABLE"
    if expected_value > 1.0: status_msg = "💎 HOLY GRAIL"

    return f"""
    [REALITY ENGINE v3.0 - SIMULATION]
    - Sample Size: {total_trades} trades found in history
    - Win Rate: {win_rate:.1f}%
    - Risk/Reward Used: 1:{risk_reward_ratio}
    - Profit Factor: {profit_factor} ( > 1.5 is Good)
    - Max Consecutive Losses: {max_consecutive_loss} (Risk Warning)
    - Mathematical Expectancy: {expected_value:.2f}R per trade
    >> VERDICT: {status_msg}
    """

def processar_dados_inteligentes(nome_ativo, df_m15):
    df_m15 = math_common(df_m15)
    df_m15 = math_advanced_indicators(df_m15)
    
    info_extra = ""
    classe = ""
    
    # Diagnóstico de Regime
    adx_atual = df_m15.iloc[-1]['ADX']
    regime = "TRENDING (Strong)" if adx_atual > 25 else "RANGING (Weak)"
    
    if "CRASH" in nome_ativo or "BOOM" in nome_ativo:
        classe = "PROTOCOL A: SPIKE INDICES"
        df_final = math_boom_crash(df_m15, nome_ativo)
        total_spikes = df_final['is_spike'].sum()
        trend = "BEARISH" if df_final.iloc[-1]['close'] < df_final.iloc[-1]['EMA_200'] else "BULLISH"
        
        info_extra = f"""
        [SPIKE DATA]
        - Market Regime: {regime} (ADX: {adx_atual:.2f})
        - Macro Trend: {trend}
        - Spikes (Last 1000): {total_spikes}
        """
        
    elif "STEP" in nome_ativo or "JUMP" in nome_ativo:
        classe = "PROTOCOL B: DISCRETE INDICES"
        atr = df_m15.iloc[-1]['ATR']
        info_extra = f"""
        [DISCRETE DATA]
        - Volatility (ATR): {atr:.4f}
        - Trend Strength: {adx_atual:.2f}
        - RSI: {df_m15.iloc[-1]['RSI']:.2f}
        """
    else: 
        classe = "PROTOCOL C: FLUID INDICES"
        # Lógica de Bloqueio de Estratégia
        sugestao = "FOLLOW TREND (Pullbacks)" if adx_atual > 25 else "MEAN REVERSION (Extremes)"
        
        info_extra = f"""
        [FLUID DATA]
        - Market Regime: {regime}
        - Strategy Lock: {sugestao}
        - Z-Score Deviation: {df_m15.iloc[-1]['Z_Score']:.2f}
        - Bollinger Band: {'Touching Upper' if df_m15.iloc[-1]['close'] > df_m15.iloc[-1]['BB_Upper'] else ('Touching Lower' if df_m15.iloc[-1]['close'] < df_m15.iloc[-1]['BB_Lower'] else 'Inside')}
        """
        
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
modo_operacao = st.sidebar.radio(
    "Escolha o modo:",
    ["Análise Visual (SI-APATECO)", "Radar Auto (Telegram)"]
)

with st.spinner("🔄 Estabelecendo Link Deriv..."):
    LISTA_ATIVOS = buscar_lista_ativos_deriv()
if not LISTA_ATIVOS: st.stop()

# ==========================================================
# MODO 1: ANÁLISE VISUAL SI-APATECO
# ==========================================================
if modo_operacao == "Análise Visual (SI-APATECO)":
    st.markdown("<h1 style='text-align: center; margin-bottom: 20px;'>💠 SI-APATECO <span style='font-size: 15px; color: #00ff88; vertical-align: top;'>PRO</span></h1>", unsafe_allow_html=True)
    
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
        st.write("") # Espaçamento
        st.write("") 
        start_btn = st.button("🚀 EXECUTAR ANÁLISE")
    
    if start_btn:
        if not api_key: st.error("⚠️ Falta API Key."); st.stop()
        img_p = img_m15 if img_m15 else (img_h1 if img_h1 else img_h4)
        if not img_p: st.error("⚠️ Envie pelo menos uma imagem."); st.stop()
        
        status = st.status("🧠 Inicializando Core Neural (Gemini 3.0)...", expanded=True)
        genai.configure(api_key=api_key)
        
        # 1. Identificação - USANDO GEMINI 3 FLASH PREVIEW
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
            
            if not nome_ativo: status.update(label="Erro de Leitura", state="warning"); st.warning("⚠️ IA não leu o nome. Use o seletor manual acima."); st.stop()
        
        status.write(f"✅ Target Confirmado: **{nome_ativo}**")
        
        # 2. Dados
        status.write("📡 Extraindo dados institucionais (Deriv API)...")
        c_m15, c_h4, erro = asyncio.run(get_raw_data(codigo_ativo))
        if erro: 
            status.update(label="Erro Conexão", state="error")
            st.error(f"❌ Erro de Rede: {erro}"); st.stop()
        
        # 3. Processamento
        status.write("🧮 Calculando ADX, Bollinger e Backtest...")
        df_m15 = pd.DataFrame(c_m15)
        relatorio_math, classe_ativo, relatorio_backtest = processar_dados_inteligentes(nome_ativo, df_m15)
        
        status.write(f"🧬 Protocolo: **{classe_ativo}**")
        
        # 4. Prompt Gemini - USANDO GEMINI 3 PRO PREVIEW (MAIS INTELIGENTE)
        try: model_logic = genai.GenerativeModel("models/gemini-3-pro-preview", safety_settings=SAFETY_SETTINGS)
        except: model_logic = genai.GenerativeModel("models/gemini-3-flash-preview", safety_settings=SAFETY_SETTINGS)
        
        inputs = [SYSTEM_PROMPT]
        contexto = "CHARTS PROVIDED:\n"
        if img_m15: inputs.append(Image.open(img_m15)); contexto+="- M15\n"
        if img_h1: inputs.append(Image.open(img_h1)); contexto+="- H1\n"
        if img_h4: inputs.append(Image.open(img_h4)); contexto+="- H4\n"
        
        prompt_injecao = f"""
        TARGET: {nome_ativo}
        DETECTED CLASS: {classe_ativo}
        {contexto}
        
        === QUANTITATIVE DATA (TRUTH) ===
        {relatorio_math}
        
        === HISTORICAL REALITY (BACKTEST) ===
        {relatorio_backtest}
        
        TASK: Synthesize the Math Data with SMC visual concepts to form a high-precision trade idea.
        """
        inputs.append(prompt_injecao)
        
        try:
            status.write("🤖 Gerando Veredito SMC (SI-APATECO)...")
            resp = model_logic.generate_content(inputs)
            status.update(label="Análise Concluída", state="complete")
            
            st.divider()
            st.markdown(resp.text)
            
            with st.expander("📊 Ver Dados do Motor Matemático"):
                st.code(relatorio_backtest, language="text")
                st.code(relatorio_math, language="text")
                
        except Exception as e:
            if "429" in str(e): st.warning("⚠️ Limite de cota Gemini atingido. Aguarde 30s."); status.update(label="Pausa", state="warning")
            else: st.error(f"❌ Erro IA: {e}")

# ==========================================================
# MODO 2: RADAR AUTOMÁTICO (COM FILTRO ADX)
# ==========================================================
elif modo_operacao == "Radar Auto (Telegram)":
    st.markdown("<h1 style='text-align: center;'>📡 Radar Adaptativo (24/7)</h1>", unsafe_allow_html=True)
    st.info("Este módulo monitora o mercado e só avisa se o ADX confirmar a força do movimento.")
    
    alvos = st.multiselect("🎯 Selecione os ativos:", list(LISTA_ATIVOS.keys()), default=["CRASH 1000 INDEX"])
    
    if st.button("🟢 ATIVAR VIGILÂNCIA"):
        if not tg_token: st.error("Falta Telegram Token."); st.stop()
        st.success("Radar Ativo! Pode minimizar esta aba.")
        enviar_telegram(tg_token, tg_chat, "📡 RADAR SI-APATECO INICIADO")
        
        ph = st.empty()
        log_container = []
        
        while True:
            for nome in alvos:
                try:
                    codigo = LISTA_ATIVOS[nome]
                    c_m15, c_h4, _ = asyncio.run(get_raw_data(codigo))
                    
                    if c_m15:
                        df_m15 = pd.DataFrame(c_m15)
                        math_report, classe, _ = processar_dados_inteligentes(nome, df_m15)
                        
                        msg = ""
                        # Filtro Simples para Alerta
                        if "SPIKE" in classe:
                            if "Trend: BULLISH" in math_report and "BOOM" in nome:
                                msg = f"🚀 **{nome}**\nProtocolo A: Tendência de Alta Confirmada"
                            elif "Trend: BEARISH" in math_report and "CRASH" in nome:
                                msg = f"🔻 **{nome}**\nProtocolo A: Tendência de Baixa Confirmada"
                        elif "Strategy Lock: MEAN REVERSION" in math_report: 
                             if "Touching Upper" in math_report or "Touching Lower" in math_report:
                                msg = f"⚡ **{nome}**\nProtocolo C: Possível Reversão (Bollinger)"
                        
                        timestamp = time.strftime("%H:%M:%S")
                        if msg:
                            enviar_telegram(tg_token, tg_chat, msg)
                            log_container.insert(0, f"[{timestamp}] {nome}: 🚨 ALERTA")
                        else:
                            log_container.insert(0, f"[{timestamp}] {nome}: Monitorando...")
                            
                except: pass
                time.sleep(1) # Delay anti-spam
            
            # Mantém apenas as últimas 10 linhas de log
            if len(log_container) > 10: log_container = log_container[:10]
            ph.code("\n".join(log_container))
            time.sleep(30)









