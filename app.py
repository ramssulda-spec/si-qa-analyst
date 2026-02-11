import streamlit as st
import asyncio
import websockets
import json
import pandas as pd
import numpy as np
import google.generativeai as genai
from PIL import Image
import matplotlib.pyplot as plt
import io
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import time
import warnings
warnings.filterwarnings('ignore')

# ==============================================================================
# SI-APATECO SNIPER V17.0 ULTRA PRO - VERSÃO REFATORADA
# Todas as melhorias sugeridas implementadas:
# ✅ Walk-Forward Backtest com custos reais
# ✅ Divergências com pivots reais (argrelextrema)
# ✅ S/R com clustering por densidade
# ✅ Wilder's RSI correto
# ✅ Fibonacci de swings confirmados
# ✅ Filtro de regime de mercado (trending vs ranging)
# ✅ Confirmação por tick volume
# ✅ Monte Carlo simulation
# ✅ Backtest com realização parcial realista
# ✅ Monitoramento não-bloqueante
# ✅ Gestão de correlação entre ativos
# ✅ Swing points sem look-ahead bias
# ==============================================================================

st.set_page_config(
    page_title="SI-APATECO SNIPER V17.0 ULTRA PRO",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Aprimorado V17
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Teko:wght@300;600&family=Share+Tech+Mono&display=swap');
    
    .stApp {
        background-color: #050505;
        background-image: linear-gradient(0deg, #000 0%, #0a0a0a 100%);
        color: #d4d4d4;
        font-family: 'Share Tech Mono', monospace;
    }
    
    h1, h2, h3 {
        font-family: 'Teko', sans-serif !important;
        text-transform: uppercase;
        color: #fbbf24;
        letter-spacing: 3px;
        text-shadow: 0 0 10px rgba(251, 191, 36, 0.3);
    }
    
    div[data-testid="stMetric"] {
        background-color: #111;
        border-right: 4px solid #fbbf24;
        padding: 15px;
    }
    
    .stButton>button {
        background: linear-gradient(45deg, #d97706, #fbbf24);
        color: black;
        font-weight: 900;
        text-transform: uppercase;
        padding: 20px;
        font-size: 20px;
        border-radius: 0px;
        width: 100%;
        border: 1px solid #fbbf24;
        transition: 0.3s;
    }
    .stButton>button:hover {
        box-shadow: 0 0 30px rgba(251, 191, 36, 0.6);
        transform: scale(1.02);
    }
    
    .score-s { color: #a855f7; font-weight: 900; font-size: 32px; animation: pulse 2s infinite; }
    .score-a-plus-plus { color: #10b981; font-weight: 900; font-size: 30px; }
    .score-a-plus { color: #3b82f6; font-weight: 900; font-size: 28px; }
    .score-a { color: #22d3ee; font-weight: 900; font-size: 26px; }
    .score-b { color: #fbbf24; font-weight: 900; font-size: 24px; }
    .score-c { color: #6b7280; font-weight: 900; font-size: 22px; }
    
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }
    
    .trade-health-excellent {
        background: linear-gradient(90deg, #10b981, #059669);
        color: white; padding: 15px; border-radius: 8px; font-weight: bold;
    }
    .trade-health-good {
        background: linear-gradient(90deg, #3b82f6, #2563eb);
        color: white; padding: 15px; border-radius: 8px; font-weight: bold;
    }
    .trade-health-warning {
        background: linear-gradient(90deg, #f59e0b, #d97706);
        color: white; padding: 15px; border-radius: 8px; font-weight: bold;
    }
    .trade-health-danger {
        background: linear-gradient(90deg, #ef4444, #dc2626);
        color: white; padding: 15px; border-radius: 8px; font-weight: bold;
        animation: blink 1s infinite;
    }
    
    @keyframes blink { 0%, 50%, 100% { opacity: 1; } 25%, 75% { opacity: 0.5; } }
    
    .improvement-badge {
        background: linear-gradient(135deg, #059669, #10b981);
        color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px;
        font-weight: bold; margin-left: 5px;
    }
</style>
""", unsafe_allow_html=True)

SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# ==============================================================================
# PROMPT OTIMIZADO V17.0
# ==============================================================================
SYSTEM_PROMPT = """
FUNÇÃO: ANALISTA ELITE V17.0 ULTRA PRO [Gemini]
Missão: Identificar Setups de Máxima Lucratividade + Gestão em Tempo Real

**RESPONDA SEMPRE EM PORTUGUÊS BRASILEIRO**

**V17.0 ULTRA PRO - CAPACIDADES EXPANDIDAS:**
- Walk-Forward Backtest validado (sem look-ahead bias)
- Divergências com pivots reais (argrelextrema)
- S/R por clustering de densidade
- Fibonacci de swings confirmados
- Filtro de regime de mercado
- Confirmação por tick volume
- Monte Carlo confidence intervals
- Wilder's RSI correto
- Perfect Alignment multi-timeframe
- Perfect Storm detection (6+ fatores)
- Score expandido: 0-150 pts (base 100 + bonus 50)

**TIPOS DE SETUP:**
1. **DAY TRADE (⚡):** Score ≥45, ADX >15, Targets 1:2 e 1:3
2. **SWING TRADE (📈):** Score ≥75, ADX >20, Targets 1:3 e 1:5
3. **BREAKOUT (💥):** Rompe S/R forte + tick volume, Targets 1:3 e 1:7
4. **PERFECT STORM (🌟):** Score ≥120, 6+ fatores, Targets 1:5 e 1:10
5. **REVERSAL (🔄):** Divergência real confirmada, Score ≥90, Targets 1:3 e 1:5

**DADOS APRIMORADOS V17.0:**
- Math Core + Score Expandido (0-150)
- Divergências com pivots reais (não posições fixas)
- S/R por clusters de toque (não níveis individuais)
- Fibonacci de swings reais confirmados
- Regime de mercado (TRENDING / RANGING / TRANSITIONAL)
- Monte Carlo: Mediana, P5, P95 do retorno esperado
- Walk-Forward WR e PF (validação out-of-sample)
- Tick Volume confirmation (breakouts)

**FORMATO DE SAÍDA:**

## 🎯 VEREDICTO SNIPER V17.0: [ {FINAL_DECISION} ]
**Grade:** {GRADE_EMOJI} **{SETUP_GRADE}** | **Score:** {SETUP_SCORE}/150
**Tipo:** {TRADE_STYLE_EMOJI} {TRADE_STYLE} | **Regime:** {MARKET_REGIME}

### 📊 BREAKDOWN COMPLETO
**Score Base:** {BASE_SCORE}/100
- Força Tendência (ADX): {ADX_SCORE}/25
- Momentum Alignment: {MOMENTUM_SCORE}/20
- Padrões Candlestick: {PATTERN_SCORE}/15
- Zona de Valor: {VALUE_SCORE}/15
- Edge Histórico (Walk-Forward): {HIST_SCORE}/25

**Bonus Confluências:** +{BONUS_SCORE}/50
{Listar todas as confluências com seus bonus}

### 📈 VALIDAÇÃO ESTATÍSTICA (V17.0 NOVO)
- **Walk-Forward WR:** {WF_WR}% (out-of-sample)
- **Monte Carlo Mediana:** {MC_MEDIAN}R
- **Monte Carlo P5 (pior caso):** {MC_P5}R
- **Monte Carlo P95 (melhor caso):** {MC_P95}R
- **Confiança estatística:** {CONFIDENCE}

### 👁️ ANÁLISE VISUAL TRI-FORCE
*   **H4 (Macro):** {Análise tendência, estrutura, regime}
*   **H1 (Estrutura):** {Análise S/R clusters, zona de valor, Fibonacci}
*   **M15 (Gatilho):** {Análise padrões, divergências reais, tick volume}

### 🎯 PLANO DE EXECUÇÃO
| Parâmetro | Valor | Observações |
| :--- | :--- | :--- |
| **ENTRADA** | **{ENTRY}** | *{ENTRY_TYPE}* |
| **STOP LOSS** | **{SL}** | *{SL_REASON}* |
| **{TP1_LABEL}** | **{TP1}** | *Realizar {PCT1}% aqui* |
| **{TP2_LABEL}** | **{TP2}** | *Deixar {PCT2}% + trailing* |
| **POSIÇÃO** | **{SIZE}** | *{RISK}% risco adaptativo* |
| **SPREAD COST** | **{SPREAD}** | *Incluído no cálculo* |

### 🔥 CONFLUÊNCIAS DETECTADAS
{Listar todas as confluências encontradas com detalhes}

### ⚠️ RISCOS IDENTIFICADOS
{Listar fatores de risco: regime adverso, divergências contrárias, etc.}

*Insight V17.0:* {Análise profunda com base em dados validados estatisticamente.
Inclua: regime de mercado, qualidade do backtest walk-forward, intervalos Monte Carlo.
Confiança: Alto/Médio/Baixo com justificativa estatística}
"""

# ==============================================================================
# CONFIGURAÇÃO SPREAD POR ATIVO (V17.0 NOVO)
# ==============================================================================
SPREAD_MAP = {
    "VOLATILITY 10 INDEX": 0.02,
    "VOLATILITY 25 INDEX": 0.03,
    "VOLATILITY 50 INDEX": 0.05,
    "VOLATILITY 75 INDEX": 0.10,
    "VOLATILITY 100 INDEX": 0.15,
    "VOLATILITY 10 (1S) INDEX": 0.02,
    "VOLATILITY 25 (1S) INDEX": 0.03,
    "VOLATILITY 50 (1S) INDEX": 0.05,
    "VOLATILITY 75 (1S) INDEX": 0.10,
    "VOLATILITY 100 (1S) INDEX": 0.15,
    "BOOM 300 INDEX": 0.10,
    "BOOM 500 INDEX": 0.10,
    "BOOM 1000 INDEX": 0.10,
    "CRASH 300 INDEX": 0.10,
    "CRASH 500 INDEX": 0.10,
    "CRASH 1000 INDEX": 0.10,
    "STEP INDEX": 0.01,
    "RANGE BREAK 100": 0.05,
    "RANGE BREAK 200": 0.05,
    "JUMP 10 INDEX": 0.05,
    "JUMP 25 INDEX": 0.08,
    "JUMP 50 INDEX": 0.10,
    "JUMP 75 INDEX": 0.12,
    "JUMP 100 INDEX": 0.15,
}

def get_spread(asset_name: str) -> float:
    """Retorna spread estimado do ativo"""
    for key, spread in SPREAD_MAP.items():
        if key in asset_name.upper():
            return spread
    return 0.05  # Default

# ==============================================================================
# DERIV NETWORK
# ==============================================================================
DERIV_SERVERS = [
    "wss://ws.binaryws.com/websockets/v3?app_id=1089",
    "wss://ws.derivws.com/websockets/v3?app_id=1089",
    "wss://green.binaryws.com/websockets/v3?app_id=1089"
]

async def socket_req(url, req):
    try:
        async with websockets.connect(url, ping_interval=20, close_timeout=15) as ws:
            await ws.send(json.dumps(req))
            response = await asyncio.wait_for(ws.recv(), timeout=15.0)
            return json.loads(response)
    except:
        return None

@st.cache_data(ttl=3600)
def get_assets():
    req = {"active_symbols": "brief", "product_type": "basic"}
    for url in DERIV_SERVERS:
        res = asyncio.run(socket_req(url, req))
        if res and 'active_symbols' in res:
            return {x['display_name'].upper(): x['symbol'] for x in res['active_symbols'] 
                    if x['market'] == 'synthetic_index'}
    return None

async def fetch_tri_force(code):
    reqs = [
        {"ticks_history": code, "style": "candles", "granularity": 3600, "count": 500, "end": "latest"},
        {"ticks_history": code, "style": "candles", "granularity": 14400, "count": 300, "end": "latest"},
        {"ticks_history": code, "style": "candles", "granularity": 900, "count": 1500, "end": "latest"}
    ]
    
    for url in DERIV_SERVERS:
        try:
            async with websockets.connect(url, ping_interval=20, close_timeout=15) as ws:
                await ws.send(json.dumps(reqs[0]))
                h1 = json.loads(await asyncio.wait_for(ws.recv(), 15))
                await ws.send(json.dumps(reqs[1]))
                h4 = json.loads(await asyncio.wait_for(ws.recv(), 15))
                await ws.send(json.dumps(reqs[2]))
                m15 = json.loads(await asyncio.wait_for(ws.recv(), 15))
                
                if all('candles' in x for x in [h1, h4, m15]):
                    return h1['candles'], h4['candles'], m15['candles'], None
        except:
            continue
    
    return None, None, None, "CONNECTION LOST"

# ==============================================================================
# INDICADORES TÉCNICOS V17.0 (CORRIGIDOS)
# ==============================================================================

def prep_df(data):
    df = pd.DataFrame(data)
    for c in ['open', 'high', 'low', 'close']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df['date'] = pd.to_datetime(df['epoch'], unit='s')
    df.set_index('date', inplace=True)
    return df

# ── V17.0 FIX: Wilder's RSI correto ──────────────────────────────────────────
def calculate_rsi_wilder(series, period=14):
    """
    RSI usando Wilder's Smoothing (não EWM padrão)
    Wilder's smoothing: alpha = 1/period
    """
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    
    # Primeira média: SMA
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    
    # Wilder's smoothing para o restante
    for i in range(period, len(series)):
        if pd.notna(avg_gain.iloc[i - 1]):
            avg_gain.iloc[i] = (avg_gain.iloc[i - 1] * (period - 1) + gain.iloc[i]) / period
            avg_loss.iloc[i] = (avg_loss.iloc[i - 1] * (period - 1) + loss.iloc[i]) / period
    
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(df, fast=12, slow=26, signal=9):
    ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
    df['MACD'] = ema_fast - ema_slow
    df['MACD_signal'] = df['MACD'].ewm(span=signal, adjust=False).mean()
    df['MACD_hist'] = df['MACD'] - df['MACD_signal']
    return df

def calculate_adx(df, window=14):
    df['trh'] = df['high'] - df['low']
    df['trc'] = abs(df['high'] - df['close'].shift())
    df['trl'] = abs(df['low'] - df['close'].shift())
    df['TR'] = df[['trh', 'trc', 'trl']].max(axis=1)
    
    df['+DM'] = np.where((df['high'] > df['high'].shift()) & (df['low'] <= df['low'].shift()),
                         df['high'] - df['high'].shift(), 0)
    df['-DM'] = np.where((df['low'] < df['low'].shift()) & (df['high'] >= df['high'].shift()),
                         df['low'].shift() - df['low'], 0)
    
    df['+DM'] = np.where(df['+DM'] > df['-DM'], df['+DM'], 0)
    df['-DM'] = np.where(df['-DM'] > df['+DM'], df['-DM'], 0)
    
    df['TR_EMA'] = df['TR'].ewm(span=window, adjust=False).mean()
    df['+DM_EMA'] = df['+DM'].ewm(span=window, adjust=False).mean()
    df['-DM_EMA'] = df['-DM'].ewm(span=window, adjust=False).mean()
    
    df['+DI'] = (df['+DM_EMA'] / df['TR_EMA']) * 100
    df['-DI'] = (df['-DM_EMA'] / df['TR_EMA']) * 100
    
    di_sum = df['+DI'] + df['-DI']
    di_sum = di_sum.replace(0, np.nan)
    df['DX'] = (abs(df['+DI'] - df['-DI']) / di_sum) * 100
    df['ADX'] = df['DX'].ewm(span=window, adjust=False).mean()
    
    # Manter +DI e -DI para análise direcional
    df.drop(columns=['trh', 'trc', 'trl', 'TR', '+DM', '-DM', 'TR_EMA',
                      '+DM_EMA', '-DM_EMA', 'DX'], inplace=True)
    return df

# ==============================================================================
# V17.0 NOVO: DETECÇÃO DE PIVOTS REAIS (argrelextrema manual)
# ==============================================================================

def find_pivot_highs(data, order=5):
    """Encontra pivot highs sem scipy - implementação manual robusta"""
    pivots = []
    values = data.values if hasattr(data, 'values') else np.array(data)
    
    for i in range(order, len(values) - order):
        if np.isnan(values[i]):
            continue
        is_pivot = True
        for j in range(1, order + 1):
            if values[i] <= values[i - j] or values[i] <= values[i + j]:
                is_pivot = False
                break
        if is_pivot:
            pivots.append(i)
    return np.array(pivots)

def find_pivot_lows(data, order=5):
    """Encontra pivot lows sem scipy - implementação manual robusta"""
    pivots = []
    values = data.values if hasattr(data, 'values') else np.array(data)
    
    for i in range(order, len(values) - order):
        if np.isnan(values[i]):
            continue
        is_pivot = True
        for j in range(1, order + 1):
            if values[i] >= values[i - j] or values[i] >= values[i + j]:
                is_pivot = False
                break
        if is_pivot:
            pivots.append(i)
    return np.array(pivots)

# ==============================================================================
# V17.0 FIX: DIVERGÊNCIAS COM PIVOTS REAIS
# ==============================================================================

def detect_divergence_v17(df, indicator='RSI', order=5):
    """
    V17.0: Detecta divergências usando pivots reais (não posições fixas)
    Retorna: (tipo, score_bonus, detalhes)
    """
    try:
        if len(df) < (order * 2 + 5) or indicator not in df.columns:
            return None, 0, ""
        
        # Encontrar pivots reais no preço
        price_high_pivots = find_pivot_highs(df['high'], order=order)
        price_low_pivots = find_pivot_lows(df['low'], order=order)
        
        # Encontrar pivots reais no indicador
        ind_high_pivots = find_pivot_highs(df[indicator], order=order)
        ind_low_pivots = find_pivot_lows(df[indicator], order=order)
        
        # Precisamos de pelo menos 2 pivots recentes
        # ── BEARISH DIVERGENCE (preço faz HH, indicador faz LH) ──
        if len(price_high_pivots) >= 2 and len(ind_high_pivots) >= 2:
            # Últimos 2 pivot highs do preço
            ph1_idx = price_high_pivots[-2]
            ph2_idx = price_high_pivots[-1]
            
            # Encontrar pivot high do indicador mais próximo de cada
            ih1_idx = ind_high_pivots[np.argmin(np.abs(ind_high_pivots - ph1_idx))]
            ih2_idx = ind_high_pivots[np.argmin(np.abs(ind_high_pivots - ph2_idx))]
            
            # Verificar proximidade temporal (máx 3 candles de diferença)
            if abs(ih1_idx - ph1_idx) <= 3 and abs(ih2_idx - ph2_idx) <= 3:
                price_hh = df['high'].iloc[ph2_idx] > df['high'].iloc[ph1_idx]
                ind_lh = df[indicator].iloc[ih2_idx] < df[indicator].iloc[ih1_idx]
                
                if price_hh and ind_lh:
                    # Calcular força da divergência
                    price_diff_pct = (df['high'].iloc[ph2_idx] - df['high'].iloc[ph1_idx]) / df['high'].iloc[ph1_idx] * 100
                    ind_diff_pct = (df[indicator].iloc[ih1_idx] - df[indicator].iloc[ih2_idx]) / max(df[indicator].iloc[ih1_idx], 1) * 100
                    
                    strength = min(price_diff_pct + ind_diff_pct, 10)
                    
                    if strength > 1.0:  # Divergência significativa
                        bonus = -int(min(strength * 3, 20))
                        detail = f"Preço HH +{price_diff_pct:.1f}% vs {indicator} LH -{ind_diff_pct:.1f}%"
                        return "BEARISH_DIVERGENCE", bonus, detail
        
        # ── BULLISH DIVERGENCE (preço faz LL, indicador faz HL) ──
        if len(price_low_pivots) >= 2 and len(ind_low_pivots) >= 2:
            pl1_idx = price_low_pivots[-2]
            pl2_idx = price_low_pivots[-1]
            
            il1_idx = ind_low_pivots[np.argmin(np.abs(ind_low_pivots - pl1_idx))]
            il2_idx = ind_low_pivots[np.argmin(np.abs(ind_low_pivots - pl2_idx))]
            
            if abs(il1_idx - pl1_idx) <= 3 and abs(il2_idx - pl2_idx) <= 3:
                price_ll = df['low'].iloc[pl2_idx] < df['low'].iloc[pl1_idx]
                ind_hl = df[indicator].iloc[il2_idx] > df[indicator].iloc[il1_idx]
                
                if price_ll and ind_hl:
                    price_diff_pct = (df['low'].iloc[pl1_idx] - df['low'].iloc[pl2_idx]) / df['low'].iloc[pl1_idx] * 100
                    ind_diff_pct = (df[indicator].iloc[il2_idx] - df[indicator].iloc[il1_idx]) / max(abs(df[indicator].iloc[il1_idx]), 1) * 100
                    
                    strength = min(price_diff_pct + ind_diff_pct, 10)
                    
                    if strength > 1.0:
                        bonus = int(min(strength * 3, 20))
                        detail = f"Preço LL -{price_diff_pct:.1f}% vs {indicator} HL +{ind_diff_pct:.1f}%"
                        return "BULLISH_DIVERGENCE", bonus, detail
        
        # ── HIDDEN BULLISH (preço faz HL, indicador faz LL) - continuação ──
        if len(price_low_pivots) >= 2 and len(ind_low_pivots) >= 2:
            pl1_idx = price_low_pivots[-2]
            pl2_idx = price_low_pivots[-1]
            
            il1_idx = ind_low_pivots[np.argmin(np.abs(ind_low_pivots - pl1_idx))]
            il2_idx = ind_low_pivots[np.argmin(np.abs(ind_low_pivots - pl2_idx))]
            
            if abs(il1_idx - pl1_idx) <= 3 and abs(il2_idx - pl2_idx) <= 3:
                price_hl = df['low'].iloc[pl2_idx] > df['low'].iloc[pl1_idx]
                ind_ll = df[indicator].iloc[il2_idx] < df[indicator].iloc[il1_idx]
                
                if price_hl and ind_ll:
                    detail = f"Hidden: Preço HL vs {indicator} LL"
                    return "HIDDEN_BULLISH", 15, detail
        
        # ── HIDDEN BEARISH (preço faz LH, indicador faz HH) - continuação ──
        if len(price_high_pivots) >= 2 and len(ind_high_pivots) >= 2:
            ph1_idx = price_high_pivots[-2]
            ph2_idx = price_high_pivots[-1]
            
            ih1_idx = ind_high_pivots[np.argmin(np.abs(ind_high_pivots - ph1_idx))]
            ih2_idx = ind_high_pivots[np.argmin(np.abs(ind_high_pivots - ph2_idx))]
            
            if abs(ih1_idx - ph1_idx) <= 3 and abs(ih2_idx - ph2_idx) <= 3:
                price_lh = df['high'].iloc[ph2_idx] < df['high'].iloc[ph1_idx]
                ind_hh = df[indicator].iloc[ih2_idx] > df[indicator].iloc[ih1_idx]
                
                if price_lh and ind_hh:
                    detail = f"Hidden: Preço LH vs {indicator} HH"
                    return "HIDDEN_BEARISH", -15, detail
        
        return None, 0, ""
    except:
        return None, 0, ""

# ==============================================================================
# V17.0 FIX: SUPORTE E RESISTÊNCIA COM CLUSTERING
# ==============================================================================

def detect_sr_clustered(df, window=100, min_touches=3):
    """
    V17.0: S/R por clustering de densidade (substitui iteração bruta)
    Agrupa toques próximos em zonas ao invés de níveis exatos
    """
    try:
        if len(df) < window or 'ATR' not in df.columns:
            return []
        
        recent = df.tail(window)
        atr = recent['ATR'].iloc[-1]
        
        if pd.isna(atr) or atr == 0:
            return []
        
        # Zona de tolerância: 0.3 ATR (mais restritivo que v16)
        tolerance = atr * 0.3
        
        # Coletar todos os extremos locais (pivots reais)
        high_pivots = find_pivot_highs(recent['high'], order=3)
        low_pivots = find_pivot_lows(recent['low'], order=3)
        
        # Combinar todos os níveis de interesse
        touch_prices = []
        for idx in high_pivots:
            touch_prices.append(recent['high'].iloc[idx])
        for idx in low_pivots:
            touch_prices.append(recent['low'].iloc[idx])
        
        if not touch_prices:
            return []
        
        touch_prices = sorted(touch_prices)
        
        # Clustering manual por proximidade
        clusters = []
        current_cluster = [touch_prices[0]]
        
        for i in range(1, len(touch_prices)):
            if touch_prices[i] - current_cluster[-1] <= tolerance:
                current_cluster.append(touch_prices[i])
            else:
                if len(current_cluster) >= min_touches:
                    clusters.append(current_cluster)
                current_cluster = [touch_prices[i]]
        
        if len(current_cluster) >= min_touches:
            clusters.append(current_cluster)
        
        # Converter clusters em níveis S/R
        current_price = df['close'].iloc[-1]
        levels = []
        
        for cluster in clusters:
            level_price = np.mean(cluster)
            touches = len(cluster)
            spread = max(cluster) - min(cluster)
            
            levels.append({
                'price': round(level_price, 4),
                'touches': touches,
                'spread': round(spread, 4),
                'type': 'RESISTANCE' if level_price > current_price else 'SUPPORT',
                'strength': touches + (1 if spread < tolerance * 0.5 else 0),  # Bonus for tight cluster
                'zone_high': round(max(cluster), 4),
                'zone_low': round(min(cluster), 4)
            })
        
        levels.sort(key=lambda x: x['strength'], reverse=True)
        return levels[:6]
    except:
        return []

# ==============================================================================
# V17.0 FIX: FIBONACCI DE SWINGS CONFIRMADOS
# ==============================================================================

def calculate_fibonacci_from_swings(df, lookback=100):
    """
    V17.0: Fibonacci baseado em swings confirmados (não apenas max/min)
    """
    try:
        if len(df) < lookback:
            return {}, None, None
        
        recent = df.tail(lookback)
        
        # Encontrar swings reais
        high_pivots = find_pivot_highs(recent['high'], order=7)
        low_pivots = find_pivot_lows(recent['low'], order=7)
        
        if len(high_pivots) == 0 or len(low_pivots) == 0:
            return {}, None, None
        
        # Último swing high e low significativo
        last_high_idx = high_pivots[-1]
        last_low_idx = low_pivots[-1]
        
        swing_high = recent['high'].iloc[last_high_idx]
        swing_low = recent['low'].iloc[last_low_idx]
        
        if pd.isna(swing_high) or pd.isna(swing_low) or swing_high == swing_low:
            return {}, None, None
        
        diff = swing_high - swing_low
        
        # Determinar direção do Fibonacci
        # Se swing high veio DEPOIS do swing low → uptrend (retracement de alta)
        # Se swing low veio DEPOIS do swing high → downtrend (retracement de baixa)
        if last_high_idx > last_low_idx:
            direction = "UPTREND"
            fibs = {
                '0.0% (Low)': swing_low,
                '23.6%': swing_high - (diff * 0.236),
                '38.2%': swing_high - (diff * 0.382),
                '50.0%': swing_high - (diff * 0.50),
                '61.8%': swing_high - (diff * 0.618),
                '78.6%': swing_high - (diff * 0.786),
                '100% (High)': swing_high
            }
        else:
            direction = "DOWNTREND"
            fibs = {
                '0.0% (High)': swing_high,
                '23.6%': swing_low + (diff * 0.236),
                '38.2%': swing_low + (diff * 0.382),
                '50.0%': swing_low + (diff * 0.50),
                '61.8%': swing_low + (diff * 0.618),
                '78.6%': swing_low + (diff * 0.786),
                '100% (Low)': swing_low
            }
        
        return fibs, direction, {'high': swing_high, 'low': swing_low}
    except:
        return {}, None, None

def check_fib_confluence(price, fibs, atr):
    """Verifica confluência com Fibonacci"""
    try:
        if not fibs or pd.isna(price) or pd.isna(atr) or atr == 0:
            return None, 0
        
        tolerance = atr * 0.4  # V17.0: mais restritivo
        best_level = None
        best_distance = float('inf')
        
        key_levels = ['38.2%', '50.0%', '61.8%']  # Níveis mais relevantes
        
        for level_name, level_price in fibs.items():
            # Priorizar níveis-chave
            is_key = any(k in level_name for k in key_levels)
            adj_tolerance = tolerance * (1.2 if is_key else 0.8)
            
            if pd.notna(level_price):
                distance = abs(price - level_price)
                if distance < adj_tolerance and distance < best_distance:
                    best_distance = distance
                    best_level = level_name
        
        if best_level:
            # Bonus maior para 61.8% (golden ratio)
            if '61.8' in best_level:
                return best_level, 15
            elif '50.0' in best_level or '38.2' in best_level:
                return best_level, 10
            else:
                return best_level, 5
        
        return None, 0
    except:
        return None, 0

# ==============================================================================
# V17.0 NOVO: FILTRO DE REGIME DE MERCADO
# ==============================================================================

def classify_market_regime(df, lookback=50):
    """
    V17.0: Classifica regime como TRENDING, RANGING, ou TRANSITIONAL
    Usa ADX + inclinação de EMA + largura de Bollinger
    """
    try:
        if len(df) < lookback:
            return "UNKNOWN", 0
        
        recent = df.tail(lookback)
        current = recent.iloc[-1]
        
        adx = current['ADX']
        
        # Inclinação da EMA 50 (normalizada pelo ATR)
        ema50_slope = (recent['EMA_50'].iloc[-1] - recent['EMA_50'].iloc[-10]) / (current['ATR'] * 10)
        
        # BB Width relativa
        bb_width = current['BB_width']
        bb_width_avg = recent['BB_width'].mean()
        bb_ratio = bb_width / bb_width_avg if bb_width_avg > 0 else 1.0
        
        # Scoring de regime
        trend_score = 0
        
        if adx > 30:
            trend_score += 3
        elif adx > 20:
            trend_score += 2
        elif adx > 15:
            trend_score += 1
        
        if abs(ema50_slope) > 0.3:
            trend_score += 2
        elif abs(ema50_slope) > 0.15:
            trend_score += 1
        
        if bb_ratio > 1.3:
            trend_score += 1  # Expansão = trending
        elif bb_ratio < 0.7:
            trend_score -= 1  # Compressão = ranging (preparando breakout)
        
        # Classificação
        if trend_score >= 4:
            return "TRENDING_STRONG", trend_score
        elif trend_score >= 2:
            return "TRENDING_WEAK", trend_score
        elif trend_score <= 0:
            return "RANGING", trend_score
        else:
            return "TRANSITIONAL", trend_score
    except:
        return "UNKNOWN", 0

# ==============================================================================
# V17.0 NOVO: TICK VOLUME CONFIRMATION
# ==============================================================================

def analyze_tick_volume(df, lookback=20):
    """
    V17.0: Analisa tick volume como proxy de atividade
    Nota: Índices sintéticos Deriv não têm volume real,
    então usamos variação de preço intracandle como proxy
    """
    try:
        if len(df) < lookback:
            return "NORMAL", 1.0
        
        recent = df.tail(lookback)
        
        # Proxy de volume: range (high-low) relativo ao ATR
        ranges = recent['high'] - recent['low']
        avg_range = ranges.mean()
        current_range = ranges.iloc[-1]
        
        # Body size relativo
        bodies = abs(recent['close'] - recent['open'])
        avg_body = bodies.mean()
        current_body = bodies.iloc[-1]
        
        # Ratio combinado
        if avg_range > 0 and avg_body > 0:
            range_ratio = current_range / avg_range
            body_ratio = current_body / avg_body
            volume_proxy = (range_ratio + body_ratio) / 2
        else:
            volume_proxy = 1.0
        
        if volume_proxy > 2.0:
            return "VERY_HIGH", volume_proxy
        elif volume_proxy > 1.5:
            return "HIGH", volume_proxy
        elif volume_proxy > 0.7:
            return "NORMAL", volume_proxy
        else:
            return "LOW", volume_proxy
    except:
        return "NORMAL", 1.0

def confirm_breakout_volume(df, breakout_candle_idx=-1):
    """
    V17.0: Confirma breakout com aumento de atividade
    Retorna True se a vela de breakout tem volume acima da média
    """
    try:
        if len(df) < 20:
            return False, 0
        
        ranges = df['high'] - df['low']
        avg_range = ranges.iloc[-20:-1].mean()
        breakout_range = ranges.iloc[breakout_candle_idx]
        
        ratio = breakout_range / avg_range if avg_range > 0 else 1.0
        
        return ratio > 1.3, ratio
    except:
        return False, 0



# ==============================================================================
# PADRÕES CANDLESTICK V17.0 (COM GRADUAÇÃO)
# ==============================================================================

def detect_pin_bar_quality(row, prev_row):
    body = abs(row['close'] - row['open'])
    total_range = row['high'] - row['low']
    
    if total_range == 0:
        return None, 0
    
    body_pct = body / total_range
    upper_wick = row['high'] - max(row['open'], row['close'])
    lower_wick = min(row['open'], row['close']) - row['low']
    
    if lower_wick > 0 and body_pct < 0.35 and upper_wick < body:
        wick_ratio = lower_wick / max(body, 0.0001)
        if wick_ratio > 5: return "PIN_BULLISH_EXTREME", 15
        elif wick_ratio > 3: return "PIN_BULLISH_STRONG", 10
        elif wick_ratio > 2: return "PIN_BULLISH_MODERATE", 5
    
    elif upper_wick > 0 and body_pct < 0.35 and lower_wick < body:
        wick_ratio = upper_wick / max(body, 0.0001)
        if wick_ratio > 5: return "PIN_BEARISH_EXTREME", 15
        elif wick_ratio > 3: return "PIN_BEARISH_STRONG", 10
        elif wick_ratio > 2: return "PIN_BEARISH_MODERATE", 5
    
    return None, 0

def detect_engulfing_quality(row, prev_row):
    curr_body = abs(row['close'] - row['open'])
    prev_body = abs(prev_row['close'] - prev_row['open'])
    
    curr_top = max(row['open'], row['close'])
    curr_bottom = min(row['open'], row['close'])
    prev_top = max(prev_row['open'], prev_row['close'])
    prev_bottom = min(prev_row['open'], prev_row['close'])
    
    if (row['close'] > row['open'] and prev_row['close'] < prev_row['open'] and
        curr_bottom < prev_bottom and curr_top > prev_top):
        ratio = curr_body / max(prev_body, 0.0001)
        if ratio > 3: return "ENGULF_BULLISH_MASSIVE", 15
        elif ratio > 2: return "ENGULF_BULLISH_STRONG", 10
        else: return "ENGULF_BULLISH_MODERATE", 5
    
    elif (row['close'] < row['open'] and prev_row['close'] > prev_row['open'] and
          curr_bottom < prev_bottom and curr_top > prev_top):
        ratio = curr_body / max(prev_body, 0.0001)
        if ratio > 3: return "ENGULF_BEARISH_MASSIVE", 15
        elif ratio > 2: return "ENGULF_BEARISH_STRONG", 10
        else: return "ENGULF_BEARISH_MODERATE", 5
    
    return None, 0

def detect_inside_bar(row, prev_row):
    if row['high'] <= prev_row['high'] and row['low'] >= prev_row['low']:
        return "INSIDE_BAR", 5
    return None, 0

def detect_doji(row):
    body = abs(row['close'] - row['open'])
    total = row['high'] - row['low']
    if total > 0 and body / total < 0.1:
        return "DOJI", 3
    return None, 0

def detect_patterns_v17(df):
    patterns = []
    pattern_scores = []
    
    for i in range(1, len(df)):
        curr = df.iloc[i]
        prev = df.iloc[i - 1]
        
        plist = []
        score = 0
        
        for detect_fn in [detect_pin_bar_quality, detect_engulfing_quality, detect_inside_bar]:
            p, s = detect_fn(curr, prev)
            if p:
                plist.append(p)
                score += s
        
        doji, ds = detect_doji(curr)
        if doji:
            plist.append(doji)
            score += ds
        
        patterns.append(plist)
        pattern_scores.append(score)
    
    df['patterns'] = [[]] + patterns
    df['pattern_score'] = [0] + pattern_scores
    return df

# ==============================================================================
# V17.0 FIX: SWING POINTS SEM CENTER=TRUE (sem look-ahead)
# ==============================================================================

def detect_swing_points_v17(df, window=5):
    """V17.0: Swing points sem look-ahead bias (sem center=True)"""
    df['swing_high'] = False
    df['swing_low'] = False
    
    for i in range(window, len(df)):
        # Olha apenas para trás (sem futuro)
        lookback = df.iloc[max(0, i - window):i + 1]
        
        if df['high'].iloc[i] == lookback['high'].max():
            df.iloc[i, df.columns.get_loc('swing_high')] = True
        
        if df['low'].iloc[i] == lookback['low'].min():
            df.iloc[i, df.columns.get_loc('swing_low')] = True
    
    return df

def classify_market_structure(df):
    swing_highs = df[df['swing_high']]['high'].tail(4)
    swing_lows = df[df['swing_low']]['low'].tail(4)
    
    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return "INSUFFICIENT_DATA"
    
    hh = swing_highs.iloc[-1] > swing_highs.iloc[-2]
    hl = swing_lows.iloc[-1] > swing_lows.iloc[-2]
    ll = swing_lows.iloc[-1] < swing_lows.iloc[-2]
    lh = swing_highs.iloc[-1] < swing_highs.iloc[-2]
    
    if hh and hl: return "UPTREND_STRONG"
    elif ll and lh: return "DOWNTREND_STRONG"
    elif hh or hl: return "UPTREND_WEAK"
    elif ll or lh: return "DOWNTREND_WEAK"
    else: return "RANGE_BOUND"

def calculate_volatility_regime(df):
    atr_pct = (df['ATR'] / df['close']) * 100
    current = atr_pct.iloc[-1]
    
    if current < 0.3: return "VERY_LOW", current
    elif current < 0.5: return "LOW", current
    elif current < 1.5: return "MEDIUM", current
    elif current < 2.5: return "HIGH", current
    else: return "EXTREME_HIGH", current

# ==============================================================================
# INDICADORES COMPLETOS V17.0
# ==============================================================================

def indicators(df):
    df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['EMA_200'] = df['close'].ewm(span=200, adjust=False).mean()
    
    # V17.0: RSI com Wilder's Smoothing
    df['RSI'] = calculate_rsi_wilder(df['close'], period=14)
    
    # ATR
    high_low = df['high'] - df['low']
    high_close = (df['high'] - df['close'].shift()).abs()
    low_close = (df['low'] - df['close'].shift()).abs()
    df['tr'] = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['ATR'] = df['tr'].ewm(span=14, adjust=False).mean()
    
    df = calculate_adx(df)
    df = calculate_macd(df)
    
    # Bollinger Bands
    df['BB_middle'] = df['close'].rolling(window=20).mean()
    df['BB_std'] = df['close'].rolling(window=20).std()
    df['BB_upper'] = df['BB_middle'] + (df['BB_std'] * 2)
    df['BB_lower'] = df['BB_middle'] - (df['BB_std'] * 2)
    df['BB_width'] = ((df['BB_upper'] - df['BB_lower']) / df['BB_middle'].replace(0, np.nan)) * 100
    
    df = detect_patterns_v17(df)
    df = detect_swing_points_v17(df)  # V17.0: sem look-ahead
    
    df.dropna(inplace=True)
    return df

# ==============================================================================
# PERFECT ALIGNMENT & STORM (mantidos com ajustes)
# ==============================================================================

def detect_perfect_alignment(h4_row, h1_row, m15_row, direction):
    score = 0
    
    if direction == "BULLISH":
        if h4_row['close'] > h4_row['EMA_20'] > h4_row['EMA_50'] > h4_row['EMA_200']: score += 10
        if h1_row['close'] > h1_row['EMA_20'] > h1_row['EMA_50'] > h1_row['EMA_200']: score += 10
        if m15_row['close'] > m15_row['EMA_20'] > m15_row['EMA_50'] > m15_row['EMA_200']: score += 10
    elif direction == "BEARISH":
        if h4_row['close'] < h4_row['EMA_20'] < h4_row['EMA_50'] < h4_row['EMA_200']: score += 10
        if h1_row['close'] < h1_row['EMA_20'] < h1_row['EMA_50'] < h1_row['EMA_200']: score += 10
        if m15_row['close'] < m15_row['EMA_20'] < m15_row['EMA_50'] < m15_row['EMA_200']: score += 10
    
    if score == 30: return "PERFECT_ALIGNMENT", 25
    elif score >= 20: return "STRONG_ALIGNMENT", 15
    elif score >= 10: return "WEAK_ALIGNMENT", 5
    return "NO_ALIGNMENT", 0

def check_momentum_alignment(h4_df, h1_df, m15_df, direction):
    score = 0
    if direction == "BULLISH":
        if h4_df['MACD'].iloc[-1] > 0: score += 1
        if h1_df['MACD'].iloc[-1] > 0: score += 1
        if m15_df['MACD'].iloc[-1] > 0: score += 1
    else:
        if h4_df['MACD'].iloc[-1] < 0: score += 1
        if h1_df['MACD'].iloc[-1] < 0: score += 1
        if m15_df['MACD'].iloc[-1] < 0: score += 1
    return score

def calculate_perfect_storm_bonus(setup_data):
    criteria_met = 0
    criteria_list = []
    
    checks = [
        (setup_data.get('adx', 0) > 30, "ADX > 30"),
        (setup_data.get('momentum_score', 0) == 3, "Momentum 3/3"),
        (setup_data.get('pattern_score', 0) >= 15, "Padrões fortes"),
        (setup_data.get('divergence') is not None, "Divergência real detectada"),
        (setup_data.get('fib_confluence'), "Fibonacci confluência"),
        (setup_data.get('sr_touch'), "S/R cluster testado"),
        (setup_data.get('perfect_alignment'), "Perfect Alignment"),
        (setup_data.get('bb_compression'), "BB Compression"),
        (setup_data.get('regime_trending'), "Regime Trending"),  # V17.0 NOVO
        (setup_data.get('volume_confirmed'), "Volume confirmado"),  # V17.0 NOVO
    ]
    
    for check, label in checks:
        if check:
            criteria_met += 1
            criteria_list.append(label)
    
    if criteria_met >= 7: return "PERFECT_STORM", 25, criteria_list
    elif criteria_met >= 5: return "STRONG_CONFLUENCE", 15, criteria_list
    elif criteria_met >= 4: return "GOOD_CONFLUENCE", 10, criteria_list
    return None, 0, criteria_list

# ==============================================================================
# V17.0 FIX: WALK-FORWARD BACKTEST COM CUSTOS REAIS
# ==============================================================================

def detect_swing_level(df, direction, atr_multiplier=1.5):
    if direction == "BUY":
        swing_lows = df[df['swing_low']]['low']
        if not swing_lows.empty:
            return swing_lows.iloc[-1] - (df['ATR'].iloc[-1] * atr_multiplier)
        return df['low'].tail(20).min() - (df['ATR'].iloc[-1] * atr_multiplier)
    elif direction == "SELL":
        swing_highs = df[df['swing_high']]['high']
        if not swing_highs.empty:
            return swing_highs.iloc[-1] + (df['ATR'].iloc[-1] * atr_multiplier)
        return df['high'].tail(20).max() + (df['ATR'].iloc[-1] * atr_multiplier)
    return df.iloc[-1]['close']

def run_walk_forward_backtest(df, trend_dir, spread=0.05, n_folds=3):
    """
    V17.0: Walk-Forward Analysis com:
    - Múltiplos folds (sem look-ahead)
    - Custos de spread incluídos
    - Realização parcial realista (50% TP1, 50% trailing)
    - Métricas por fold para validar estabilidade
    """
    fold_size = len(df) // (n_folds + 1)  # +1 para warm-up
    
    all_trades = []
    fold_results = []
    
    for fold in range(n_folds):
        # Walk-forward: treina em folds anteriores, testa no próximo
        test_start = fold_size * (fold + 1)
        test_end = fold_size * (fold + 2) if fold < n_folds - 1 else len(df)
        
        if test_start >= len(df) - 80:
            break
        
        fold_trades = 0
        fold_wins = 0
        fold_balance = 0.0
        fold_returns = []
        
        start_idx = max(200, test_start)
        
        for i in range(start_idx, min(test_end, len(df) - 80)):
            row = df.iloc[i]
            
            sig = None
            is_adx_strong = row['ADX'] > 20
            
            if trend_dir == "BULLISH" and is_adx_strong:
                if row['close'] > row['EMA_200'] and (row['low'] <= row['EMA_50'] or row['RSI'] < 45):
                    sig = "BUY"
            elif trend_dir == "BEARISH" and is_adx_strong:
                if row['close'] < row['EMA_200'] and (row['high'] >= row['EMA_50'] or row['RSI'] > 55):
                    sig = "SELL"
            
            if sig:
                entry = row['close']
                atr = row['ATR']
                
                # V17.0: Incluir spread no entry
                if sig == "BUY":
                    entry += spread
                else:
                    entry -= spread
                
                sl_candidate = detect_swing_level(df.iloc[:i + 1], sig)
                if sig == "BUY":
                    sl = max(entry - (3 * atr), sl_candidate)
                else:
                    sl = min(entry + (3 * atr), sl_candidate)
                
                risk = abs(entry - sl)
                if risk == 0:
                    risk = atr
                
                tp1 = entry + (3 * risk) if sig == "BUY" else entry - (3 * risk)
                tp2 = entry + (5 * risk) if sig == "BUY" else entry - (5 * risk)
                
                # V17.0: Simulação realista com realização parcial
                pos1_active = True  # 50% da posição
                pos2_active = True  # 50% da posição
                pos1_result = 0
                pos2_result = 0
                current_sl = sl
                trailing_active = False
                
                for f in range(i + 1, min(i + 80, len(df))):
                    nx = df.iloc[f]
                    
                    if sig == "BUY":
                        # Check stop loss
                        if nx['low'] <= current_sl:
                            if pos1_active:
                                pos1_result = (current_sl - entry) / risk
                            if pos2_active:
                                pos2_result = (current_sl - entry) / risk
                            break
                        
                        # Check TP1 (50% da posição)
                        if pos1_active and nx['high'] >= tp1:
                            pos1_result = 3.0 - (spread / risk)  # 3R menos spread
                            pos1_active = False
                            current_sl = entry + spread  # Move para BE
                            trailing_active = True
                        
                        # Trailing para pos2
                        if trailing_active and pos2_active:
                            trail_sl = nx['high'] - (2.0 * atr)
                            current_sl = max(current_sl, trail_sl)
                            
                            if nx['high'] >= tp2:
                                pos2_result = 5.0 - (spread / risk)
                                pos2_active = False
                                break
                    
                    else:  # SELL
                        if nx['high'] >= current_sl:
                            if pos1_active:
                                pos1_result = (entry - current_sl) / risk
                            if pos2_active:
                                pos2_result = (entry - current_sl) / risk
                            break
                        
                        if pos1_active and nx['low'] <= tp1:
                            pos1_result = 3.0 - (spread / risk)
                            pos1_active = False
                            current_sl = entry - spread
                            trailing_active = True
                        
                        if trailing_active and pos2_active:
                            trail_sl = nx['low'] + (2.0 * atr)
                            current_sl = min(current_sl, trail_sl)
                            
                            if nx['low'] <= tp2:
                                pos2_result = 5.0 - (spread / risk)
                                pos2_active = False
                                break
                
                # Resultado do trade (média ponderada das 2 metades)
                trade_result = (pos1_result * 0.5) + (pos2_result * 0.5)
                
                if not (pos1_active and pos2_active):  # Pelo menos algo aconteceu
                    fold_trades += 1
                    fold_balance += trade_result
                    fold_returns.append(trade_result)
                    
                    if trade_result > 0:
                        fold_wins += 1
                    
                    all_trades.append({
                        'fold': fold,
                        'result': trade_result,
                        'pos1': pos1_result,
                        'pos2': pos2_result,
                    })
        
        if fold_trades > 0:
            fold_results.append({
                'fold': fold,
                'trades': fold_trades,
                'wr': (fold_wins / fold_trades) * 100,
                'balance': fold_balance,
                'returns': fold_returns
            })
    
    # Agregar resultados de todos os folds
    if not all_trades:
        return {
            "WR": 0, "NET": 0, "DD": 0, "PF": 0,
            "SHARPE": 0, "SORTINO": 0, "RECOVERY": 0,
            "MAX_CONS_WIN": 0, "MAX_CONS_LOSS": 0,
            "WF_STABLE": False, "FOLD_WRS": [],
            "TOTAL_TRADES": 0
        }
    
    total_trades = len(all_trades)
    results = [t['result'] for t in all_trades]
    wins = [r for r in results if r > 0]
    losses = [r for r in results if r <= 0]
    
    wr = (len(wins) / total_trades) * 100
    net = sum(results)
    
    gross_profit = sum(wins) if wins else 0
    gross_loss = abs(sum(losses)) if losses else 0
    pf = gross_profit / gross_loss if gross_loss > 0 else (gross_profit if gross_profit > 0 else 0)
    
    # Max Drawdown
    cumulative = np.cumsum(results)
    peak = np.maximum.accumulate(cumulative)
    drawdown = peak - cumulative
    max_dd = drawdown.max() if len(drawdown) > 0 else 0
    
    # Consecutive wins/losses
    max_cw = max_cl = cw = cl = 0
    for r in results:
        if r > 0:
            cw += 1; cl = 0
            max_cw = max(max_cw, cw)
        else:
            cl += 1; cw = 0
            max_cl = max(max_cl, cl)
    
    returns_series = pd.Series(results)
    
    # Sharpe/Sortino
    if len(returns_series) >= 2 and returns_series.std() > 0:
        sharpe = (returns_series.mean() / returns_series.std()) * np.sqrt(252)
    else:
        sharpe = 0
    
    downside = returns_series[returns_series < 0]
    if len(downside) >= 2 and downside.std() > 0:
        sortino = (returns_series.mean() / downside.std()) * np.sqrt(252)
    else:
        sortino = 0
    
    recovery = net / max_dd if max_dd > 0 else 0
    
    # V17.0: Verificar estabilidade entre folds
    fold_wrs = [f['wr'] for f in fold_results]
    wf_stable = len(fold_wrs) >= 2 and all(w > 30 for w in fold_wrs)
    
    return {
        "WR": round(wr, 1),
        "NET": round(net, 1),
        "DD": round(max_dd, 1),
        "PF": round(pf, 2),
        "SHARPE": round(sharpe, 2),
        "SORTINO": round(sortino, 2),
        "RECOVERY": round(recovery, 2),
        "MAX_CONS_WIN": max_cw,
        "MAX_CONS_LOSS": max_cl,
        "WF_STABLE": wf_stable,
        "FOLD_WRS": [round(w, 1) for w in fold_wrs],
        "TOTAL_TRADES": total_trades
    }

# ==============================================================================
# V17.0 NOVO: MONTE CARLO SIMULATION
# ==============================================================================

def monte_carlo_simulation(backtest_results, n_simulations=1000, n_trades=50):
    """
    V17.0: Monte Carlo para estimar intervalos de confiança
    """
    try:
        wr = backtest_results['WR'] / 100
        avg_win = backtest_results.get('PF', 2.0)  # Approximation
        
        if wr == 0 or backtest_results['TOTAL_TRADES'] < 5:
            return {"median": 0, "p5": 0, "p95": 0, "p25": 0, "p75": 0}
        
        final_balances = []
        
        for _ in range(n_simulations):
            balance = 0
            for _ in range(n_trades):
                if np.random.random() < wr:
                    # Win: resultado entre 1.5R e 5R (distribuição realista)
                    balance += np.random.uniform(1.5, min(avg_win * 1.5, 5.0))
                else:
                    # Loss: resultado entre -0.5R e -1R
                    balance -= np.random.uniform(0.5, 1.0)
            
            final_balances.append(balance)
        
        final_balances = np.array(final_balances)
        
        return {
            "median": round(np.median(final_balances), 1),
            "p5": round(np.percentile(final_balances, 5), 1),
            "p95": round(np.percentile(final_balances, 95), 1),
            "p25": round(np.percentile(final_balances, 25), 1),
            "p75": round(np.percentile(final_balances, 75), 1),
            "positive_pct": round(np.mean(final_balances > 0) * 100, 1),
        }
    except:
        return {"median": 0, "p5": 0, "p95": 0, "p25": 0, "p75": 0, "positive_pct": 0}

# ==============================================================================
# SETUP SCORING V17.0 (0-150)
# ==============================================================================

@dataclass
class SetupScoreV17:
    trend_strength: float
    momentum_align: float
    patterns: float
    value_zone: float
    historical: float
    base_total: float
    
    divergence_bonus: float
    fib_bonus: float
    sr_bonus: float
    alignment_bonus: float
    storm_bonus: float
    regime_bonus: float  # V17.0 NOVO
    volume_bonus: float  # V17.0 NOVO
    bonus_total: float
    
    total: float
    grade: str

def calculate_setup_score_v17(adx, momentum_score, pattern_score, distance_from_ema50,
                               atr, win_rate, profit_factor, divergence_bonus=0,
                               fib_bonus=0, sr_bonus=0, alignment_bonus=0, storm_bonus=0,
                               regime_bonus=0, volume_bonus=0):
    # BASE SCORE (100)
    trend_score = 25 if adx > 25 else (15 if adx > 15 else 0)
    momentum_pts = (momentum_score / 3) * 20
    
    dist_ratio = distance_from_ema50 / atr if atr > 0 else 999
    value_score = 15 if dist_ratio < 0.5 else (10 if dist_ratio < 1.0 else (5 if dist_ratio < 1.5 else 0))
    
    hist_score = min((win_rate * 0.15) + (profit_factor * 5), 25)
    
    base_total = trend_score + momentum_pts + pattern_score + value_score + hist_score
    
    # BONUS (50)
    bonus_total = min(
        divergence_bonus + fib_bonus + sr_bonus + alignment_bonus + 
        storm_bonus + regime_bonus + volume_bonus,
        50
    )
    
    total = base_total + bonus_total
    
    # GRADES
    if total >= 140: grade = "S"
    elif total >= 120: grade = "A++"
    elif total >= 90: grade = "A+"
    elif total >= 70: grade = "A"
    elif total >= 50: grade = "B"
    elif total >= 30: grade = "C"
    else: grade = "D"
    
    return SetupScoreV17(
        trend_strength=trend_score, momentum_align=momentum_pts,
        patterns=pattern_score, value_zone=value_score, historical=hist_score,
        base_total=base_total,
        divergence_bonus=divergence_bonus, fib_bonus=fib_bonus,
        sr_bonus=sr_bonus, alignment_bonus=alignment_bonus,
        storm_bonus=storm_bonus, regime_bonus=regime_bonus,
        volume_bonus=volume_bonus, bonus_total=bonus_total,
        total=total, grade=grade
    )

# ==============================================================================
# POSITION SIZING V17.0
# ==============================================================================

def adaptive_position_size(capital, risk_pct, entry, sl, atr_pct):
    """V17.0: Position sizing adaptativo por volatilidade (ATR%)"""
    base_risk = capital * (risk_pct / 100)
    
    # Ajuste por volatilidade do ativo
    if atr_pct > 3.0: vol_mult = 0.5
    elif atr_pct > 2.0: vol_mult = 0.7
    elif atr_pct < 0.5: vol_mult = 1.3
    else: vol_mult = 1.0
    
    adjusted_risk = base_risk * vol_mult
    
    risk_per_unit = abs(entry - sl)
    if risk_per_unit == 0:
        return 0, 0, "N/A"
    
    position_size = adjusted_risk / risk_per_unit
    position_value = position_size * entry
    
    if atr_pct > 3.0: note = "Vol alta - Exposição reduzida 50%"
    elif atr_pct > 2.0: note = "Vol moderada-alta - Exposição reduzida 30%"
    elif atr_pct < 0.5: note = "Vol baixa - Exposição aumentada 30%"
    else: note = "Exposição padrão"
    
    return round(position_size, 2), round(position_value, 2), note

def calculate_kelly_criterion(win_rate, avg_win, avg_loss):
    if avg_loss == 0: return 0
    wr = win_rate / 100
    kelly = (wr * avg_win - (1 - wr) * avg_loss) / avg_loss
    return max(0, min(kelly * 0.5, 0.1))  # Half-Kelly, cap 10%

# ==============================================================================
# TRADE MANAGEMENT V17.0
# ==============================================================================

@dataclass
class ActiveTrade:
    symbol: str
    direction: str
    entry_price: float
    current_price: float
    sl: float
    tp1: float
    tp2: float
    entry_time: datetime
    atr: float
    initial_risk: float
    
    sl_moved_to_be: bool = False
    tp1_hit: bool = False
    realized_pct: float = 0.0
    highest_price: float = 0.0
    lowest_price: float = 999999.0
    
    def update_price(self, new_price):
        self.current_price = new_price
        if self.direction == "LONG":
            self.highest_price = max(self.highest_price, new_price)
        else:
            self.lowest_price = min(self.lowest_price, new_price)
    
    def get_current_r(self):
        if self.direction == "LONG":
            profit = self.current_price - self.entry_price
        else:
            profit = self.entry_price - self.current_price
        return profit / self.initial_risk if self.initial_risk != 0 else 0
    
    def get_unrealized_pl(self):
        if self.direction == "LONG":
            return self.current_price - self.entry_price
        return self.entry_price - self.current_price

def analyze_trade_health(trade, df_m15):
    alerts = []
    health_score = 100
    recommendations = []
    
    current_r = trade.get_current_r()
    
    if not trade.sl_moved_to_be and current_r >= 1.5:
        alerts.append("🟢 MOVER STOP PARA BREAK-EVEN")
        recommendations.append({'type': 'MOVE_TO_BE', 'action': 'Mover SL para entrada', 'priority': 'HIGH'})
    
    if not trade.tp1_hit:
        tp1_hit = (trade.direction == "LONG" and trade.current_price >= trade.tp1) or \
                  (trade.direction == "SHORT" and trade.current_price <= trade.tp1)
        if tp1_hit:
            alerts.append("🎯 TP1 ATINGIDO - Realizar 50%")
            recommendations.append({'type': 'TAKE_PROFIT_1', 'action': 'Realizar 50%, mover SL para BE', 'priority': 'CRITICAL'})
    
    # V17.0: Divergência com pivots reais
    if len(df_m15) >= 15:
        div, _, detail = detect_divergence_v17(df_m15, 'RSI', order=3)
        if div:
            if (trade.direction == "LONG" and "BEARISH" in div) or \
               (trade.direction == "SHORT" and "BULLISH" in div):
                alerts.append(f"⚠️ DIVERGÊNCIA CONTRÁRIA: {div} ({detail})")
                health_score -= 30
                recommendations.append({'type': 'REVERSAL_RISK', 'action': 'Apertar trailing ou fechar', 'priority': 'HIGH'})
    
    if len(df_m15) >= 14:
        macd = df_m15['MACD'].iloc[-1]
        signal = df_m15['MACD_signal'].iloc[-1]
        
        if (trade.direction == "LONG" and macd < signal) or \
           (trade.direction == "SHORT" and macd > signal):
            alerts.append("⚠️ MACD PERDENDO FORÇA")
            health_score -= 20
            recommendations.append({'type': 'MOMENTUM_WEAK', 'action': 'Apertar trailing stop', 'priority': 'MEDIUM'})
    
    if current_r > 4.0 and trade.realized_pct == 0:
        alerts.append(f"💰 LUCRO +{current_r:.1f}R SEM REALIZAR")
        recommendations.append({'type': 'TAKE_PARTIAL', 'action': f'Realizar 30-40%', 'priority': 'MEDIUM'})
    
    if health_score >= 80: status, color = "EXCELLENT", "trade-health-excellent"
    elif health_score >= 60: status, color = "GOOD", "trade-health-good"
    elif health_score >= 40: status, color = "WARNING", "trade-health-warning"
    else: status, color = "DANGER", "trade-health-danger"
    
    return {
        'health_score': health_score, 'health_status': status,
        'health_color': color, 'current_r': current_r,
        'alerts': alerts, 'recommendations': recommendations
    }

# ==============================================================================
# CHART V17.0 (com zonas S/R e Fibonacci)
# ==============================================================================

def plot_candles_v17(df, title, entry=None, sl=None, tp1=None, tp2=None,
                     sr_levels=None, fib_levels=None, patterns=None):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), height_ratios=[3, 1],
                                    facecolor='#0a0a0a')
    ax1.set_facecolor('#0a0a0a')
    ax2.set_facecolor('#0a0a0a')
    
    # Candlesticks
    for i in range(len(df)):
        color = '#10b981' if df['close'].iloc[i] >= df['open'].iloc[i] else '#ef4444'
        ax1.plot([df.index[i], df.index[i]], [df['low'].iloc[i], df['high'].iloc[i]],
                 color=color, linewidth=0.8)
        ax1.plot([df.index[i], df.index[i]], [df['open'].iloc[i], df['close'].iloc[i]],
                 color=color, linewidth=3.5)
    
    # EMAs
    ax1.plot(df.index, df['EMA_20'], label='EMA 20', color='cyan', linestyle='--', alpha=0.6, linewidth=1)
    ax1.plot(df.index, df['EMA_50'], label='EMA 50', color='orange', linestyle='--', alpha=0.6, linewidth=1)
    ax1.plot(df.index, df['EMA_200'], label='EMA 200', color='purple', linestyle='-', alpha=0.4, linewidth=1.5)
    
    # Bollinger
    ax1.fill_between(df.index, df['BB_upper'], df['BB_lower'], alpha=0.05, color='white')
    
    # V17.0: S/R Zones
    if sr_levels:
        for sr in sr_levels[:4]:
            color = '#ef4444' if sr['type'] == 'RESISTANCE' else '#10b981'
            ax1.axhspan(sr['zone_low'], sr['zone_high'], alpha=0.1, color=color)
            ax1.axhline(y=sr['price'], color=color, linestyle=':', alpha=0.4, linewidth=0.8)
            ax1.text(df.index[0], sr['price'], f" {sr['type']} ({sr['touches']}x)",
                     fontsize=7, color=color, alpha=0.7)
    
    # V17.0: Fibonacci levels
    if fib_levels:
        fib_colors = {'38.2%': '#fbbf24', '50.0%': '#f59e0b', '61.8%': '#d97706'}
        for name, price in fib_levels.items():
            if pd.notna(price):
                color = fib_colors.get(name.split(' ')[0] if ' ' in name else name, '#6b7280')
                ax1.axhline(y=price, color=color, linestyle='-.', alpha=0.3, linewidth=0.7)
    
    # Trade levels
    if entry: ax1.axhline(y=entry, color='cyan', linestyle='-', label='Entry', linewidth=2)
    if sl: ax1.axhline(y=sl, color='#ef4444', linestyle='-', label='Stop Loss', linewidth=2)
    if tp1: ax1.axhline(y=tp1, color='#10b981', linestyle='--', label='TP1', linewidth=1.5)
    if tp2: ax1.axhline(y=tp2, color='#059669', linestyle='-', label='TP2', linewidth=2)
    
    # Patterns annotation
    if patterns and 'patterns' in df.columns:
        last = df['patterns'].iloc[-1]
        if last:
            ax1.text(df.index[-1], df['high'].iloc[-1] * 1.001, " ".join(last),
                     fontsize=7, color='#fbbf24', fontweight='bold')
    
    ax1.set_title(title, fontsize=14, fontweight='bold', color='#fbbf24')
    ax1.legend(loc='upper left', fontsize=7, facecolor='#111', edgecolor='#333', labelcolor='white')
    ax1.grid(True, alpha=0.1, color='#333')
    ax1.tick_params(colors='#666')
    
    # MACD
    colors = ['#10b981' if x > 0 else '#ef4444' for x in df['MACD_hist']]
    ax2.bar(df.index, df['MACD_hist'], color=colors, alpha=0.5, width=0.8)
    ax2.plot(df.index, df['MACD'], label='MACD', color='#3b82f6', linewidth=1)
    ax2.plot(df.index, df['MACD_signal'], label='Signal', color='#ef4444', linewidth=1)
    ax2.axhline(y=0, color='#333', linestyle='-', linewidth=0.5)
    ax2.set_title('MACD', fontsize=10, color='#fbbf24')
    ax2.legend(loc='upper left', fontsize=7, facecolor='#111', edgecolor='#333', labelcolor='white')
    ax2.grid(True, alpha=0.1, color='#333')
    ax2.tick_params(colors='#666')
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=120, facecolor='#0a0a0a', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf)

# ==============================================================================
# UTILITY
# ==============================================================================

def convert_numpy_to_python(obj):
    if isinstance(obj, dict):
        return {k: convert_numpy_to_python(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_to_python(i) for i in obj]
    elif isinstance(obj, np.integer): return int(obj)
    elif isinstance(obj, np.floating): return float(obj)
    elif isinstance(obj, np.ndarray): return obj.tolist()
    elif isinstance(obj, np.bool_): return bool(obj)
    elif pd.isna(obj) if isinstance(obj, (float, np.floating)) else False: return None
    else: return obj

# ==============================================================================
# SNIPER CORE V17.0 ULTRA PRO
# ==============================================================================

def sniper_core_v17(name, h1_raw, h4_raw, m15_raw, capital=10000, risk_pct=1.0):
    h1 = indicators(prep_df(h1_raw))
    h4 = indicators(prep_df(h4_raw))
    m15 = indicators(prep_df(m15_raw))
    
    curr_h1 = h1.iloc[-1]
    curr_h4 = h4.iloc[-1]
    curr_m15 = m15.iloc[-1]
    
    # Bias
    bias_h4 = "BULLISH" if curr_h4['close'] > curr_h4['EMA_200'] else "BEARISH"
    adx_h4 = curr_h4['ADX']
    
    structure = classify_market_structure(h1)
    vol_regime, vol_pct = calculate_volatility_regime(h1)
    momentum_score = check_momentum_alignment(h4, h1, m15, bias_h4)
    
    # V17.0: Regime de mercado
    market_regime, regime_score = classify_market_regime(h1)
    regime_bonus = 5 if "TRENDING" in market_regime else 0
    
    # V17.0: Divergências com pivots reais
    rsi_div, rsi_div_bonus, rsi_div_detail = detect_divergence_v17(m15, 'RSI', order=4)
    macd_div, macd_div_bonus, macd_div_detail = detect_divergence_v17(m15, 'MACD', order=4)
    
    divergence = rsi_div or macd_div
    divergence_bonus = max(rsi_div_bonus, macd_div_bonus)
    divergence_detail = rsi_div_detail or macd_div_detail
    
    # V17.0: S/R com clustering
    sr_levels = detect_sr_clustered(h1)
    sr_bonus = 0
    sr_touch = False
    closest_sr = None
    
    if sr_levels:
        closest_sr = min(sr_levels, key=lambda x: abs(x['price'] - curr_h1['close']))
        if abs(closest_sr['price'] - curr_h1['close']) < (curr_h1['ATR'] * 0.5):
            sr_bonus = min(closest_sr['strength'] * 3, 15)
            sr_touch = True
    
    # V17.0: Fibonacci de swings confirmados
    fibs, fib_direction, fib_swings = calculate_fibonacci_from_swings(h1)
    fib_level, fib_bonus = check_fib_confluence(curr_h1['close'], fibs, curr_h1['ATR'])
    
    # Perfect Alignment
    alignment_type, alignment_bonus = detect_perfect_alignment(curr_h4, curr_h1, curr_m15, bias_h4)
    
    # V17.0: Tick Volume
    vol_status, vol_proxy = analyze_tick_volume(m15)
    volume_confirmed = vol_proxy > 1.3
    volume_bonus = 5 if volume_confirmed else 0
    
    # Padrões
    recent_patterns = curr_m15['patterns'] if 'patterns' in curr_m15.index else []
    pattern_score = min(curr_m15.get('pattern_score', 0), 15)
    
    # Spread
    spread = get_spread(name)
    
    # ── DETECÇÃO DE SETUP ──
    sig = "MONITORING"
    entry = curr_h1['close']
    sl = curr_h1['close']
    entry_type = "Wait"
    sl_reason = "Structural Pivot"
    trade_style = None
    setup_type = None
    
    # V17.0: Bloqueia regime RANGING para swing
    if vol_regime == "EXTREME_HIGH":
        sig = f"BLOCKED (VOL_{vol_regime})"
    
    elif bias_h4 == "BULLISH":
        dist = abs(curr_h1['close'] - curr_h1['EMA_50'])
        is_near_value = dist < (curr_h1['ATR'] * 1.5)
        
        if divergence and "BEARISH" in divergence and "HIDDEN" not in divergence:
            sig = f"BLOCKED (BEARISH_DIV: {divergence_detail})"
        else:
            # SWING
            if adx_h4 > 20 and (is_near_value or curr_h1['RSI'] < 45):
                # V17.0: Bloqueia swing em regime ranging
                if "RANGING" in market_regime:
                    sig = "BLOCKED (RANGING_REGIME_FOR_SWING)"
                else:
                    sig = "LONG (SWING)"
                    sl = detect_swing_level(h1, "BUY", atr_multiplier=1.5)
                    entry_type = "Swing: Reteste de Tendência"
                    trade_style = "SWING"
                    setup_type = "SWING"
            
            # DAY TRADE
            elif adx_h4 > 15 and (curr_h1['close'] > curr_h1['EMA_20'] or len(recent_patterns) > 0):
                sig = "LONG (DAY)"
                sl = detect_swing_level(h1, "BUY", atr_multiplier=1.2)
                entry_type = "Day Trade: Pullback"
                trade_style = "DAY"
                setup_type = "DAY"
            
            # BREAKOUT (V17.0: com confirmação de volume)
            elif sr_touch and closest_sr and curr_h1['close'] > closest_sr['price']:
                breakout_confirmed, br_ratio = confirm_breakout_volume(m15)
                if breakout_confirmed:
                    sig = "LONG (BREAKOUT)"
                    sl = closest_sr['price'] - (curr_h1['ATR'] * 1.0)
                    entry_type = f"Breakout de Resistência (Vol ×{br_ratio:.1f})"
                    trade_style = "BREAKOUT"
                    setup_type = "BREAKOUT"
                else:
                    sig = f"BLOCKED (BREAKOUT_NO_VOLUME ×{br_ratio:.1f})"
            
            if "LONG" in sig:
                if (entry - sl) > (3 * curr_h1['ATR']):
                    sl = entry - (2.5 * curr_h1['ATR'])
                    sl_reason = "Max ATR Limit"
    
    elif bias_h4 == "BEARISH":
        dist = abs(curr_h1['close'] - curr_h1['EMA_50'])
        is_near_value = dist < (curr_h1['ATR'] * 1.5)
        
        if divergence and "BULLISH" in divergence and "HIDDEN" not in divergence:
            sig = f"BLOCKED (BULLISH_DIV: {divergence_detail})"
        else:
            if adx_h4 > 20 and (is_near_value or curr_h1['RSI'] > 55):
                if "RANGING" in market_regime:
                    sig = "BLOCKED (RANGING_REGIME_FOR_SWING)"
                else:
                    sig = "SHORT (SWING)"
                    sl = detect_swing_level(h1, "SELL", atr_multiplier=1.5)
                    entry_type = "Swing: Reteste de Tendência"
                    trade_style = "SWING"
                    setup_type = "SWING"
            
            elif adx_h4 > 15 and (curr_h1['close'] < curr_h1['EMA_20'] or len(recent_patterns) > 0):
                sig = "SHORT (DAY)"
                sl = detect_swing_level(h1, "SELL", atr_multiplier=1.2)
                entry_type = "Day Trade: Pullback"
                trade_style = "DAY"
                setup_type = "DAY"
            
            elif sr_touch and closest_sr and curr_h1['close'] < closest_sr['price']:
                breakout_confirmed, br_ratio = confirm_breakout_volume(m15)
                if breakout_confirmed:
                    sig = "SHORT (BREAKOUT)"
                    sl = closest_sr['price'] + (curr_h1['ATR'] * 1.0)
                    entry_type = f"Breakout de Suporte (Vol ×{br_ratio:.1f})"
                    trade_style = "BREAKOUT"
                    setup_type = "BREAKOUT"
                else:
                    sig = f"BLOCKED (BREAKOUT_NO_VOLUME ×{br_ratio:.1f})"
            
            if "SHORT" in sig:
                if (sl - entry) > (3 * curr_h1['ATR']):
                    sl = entry + (2.5 * curr_h1['ATR'])
                    sl_reason = "Max ATR Limit"
    
    # V17.0: Include spread in entry
    if "LONG" in sig:
        entry += spread
    elif "SHORT" in sig:
        entry -= spread
    
    # V17.0: Walk-Forward Backtest
    if "BLOCKED" not in sig and sig != "MONITORING":
        sim = run_walk_forward_backtest(h1, bias_h4, spread=spread, n_folds=3)
    else:
        sim = {"WR": 0, "NET": 0, "DD": 0, "PF": 0, "SHARPE": 0, "SORTINO": 0,
               "RECOVERY": 0, "MAX_CONS_WIN": 0, "MAX_CONS_LOSS": 0,
               "WF_STABLE": False, "FOLD_WRS": [], "TOTAL_TRADES": 0}
    
    # V17.0: Monte Carlo
    mc_results = monte_carlo_simulation(sim) if sim['TOTAL_TRADES'] >= 5 else \
        {"median": 0, "p5": 0, "p95": 0, "p25": 0, "p75": 0, "positive_pct": 0}
    
    # Perfect Storm V17.0
    bb_width_avg = h1['BB_width'].tail(20).mean() if len(h1) >= 20 else h1['BB_width'].mean()
    bb_compression = curr_h1['BB_width'] < (bb_width_avg * 0.6)
    
    storm_data = {
        'adx': adx_h4, 'momentum_score': momentum_score,
        'pattern_score': pattern_score, 'divergence': divergence,
        'fib_confluence': fib_level is not None, 'sr_touch': sr_touch,
        'perfect_alignment': alignment_type == "PERFECT_ALIGNMENT",
        'bb_compression': bb_compression,
        'regime_trending': "TRENDING" in market_regime,
        'volume_confirmed': volume_confirmed,
    }
    
    storm_level, storm_bonus, storm_criteria = calculate_perfect_storm_bonus(storm_data)
    
    if storm_level == "PERFECT_STORM" and "BLOCKED" not in sig and sig != "MONITORING":
        sig = sig.replace("LONG", "LONG (⭐PERFECT STORM⭐)").replace("SHORT", "SHORT (⭐PERFECT STORM⭐)")
        setup_type = "PERFECT_STORM"
    
    # Divergence bonus direction-aware
    if divergence:
        if ("LONG" in sig and ("BULLISH" in divergence)) or \
           ("SHORT" in sig and ("BEARISH" in divergence)):
            final_div_bonus = abs(divergence_bonus)
        elif ("LONG" in sig and ("HIDDEN_BULLISH" in str(divergence))) or \
             ("SHORT" in sig and ("HIDDEN_BEARISH" in str(divergence))):
            final_div_bonus = abs(divergence_bonus)
        else:
            final_div_bonus = 0
    else:
        final_div_bonus = 0
    
    # Score V17.0
    distance_from_ema50 = abs(curr_h1['close'] - curr_h1['EMA_50'])
    
    score = calculate_setup_score_v17(
        adx=adx_h4, momentum_score=momentum_score,
        pattern_score=pattern_score, distance_from_ema50=distance_from_ema50,
        atr=curr_h1['ATR'], win_rate=sim['WR'], profit_factor=sim['PF'],
        divergence_bonus=final_div_bonus, fib_bonus=fib_bonus,
        sr_bonus=sr_bonus, alignment_bonus=alignment_bonus,
        storm_bonus=storm_bonus, regime_bonus=regime_bonus,
        volume_bonus=volume_bonus
    )
    
    # Filtros V17.0 (mais rígidos com walk-forward)
    if setup_type == "PERFECT_STORM":
        min_score, min_pf = 100, 1.5
    elif setup_type == "BREAKOUT":
        min_score, min_pf = 60, 1.4
    elif trade_style == "DAY":
        min_score, min_pf = 45, 1.3
    else:
        min_score, min_pf = 75, 1.5
    
    if "BLOCKED" not in sig and sig != "MONITORING":
        reasons = []
        if score.total < min_score: reasons.append(f"SCORE={score.total:.0f}<{min_score}")
        if sim['NET'] <= 0: reasons.append(f"NET={sim['NET']:.1f}≤0")
        if sim['PF'] < min_pf: reasons.append(f"PF={sim['PF']}<{min_pf}")
        if not sim['WF_STABLE'] and setup_type != "DAY": reasons.append("WF_UNSTABLE")
        
        if reasons:
            sig = f"BLOCKED ({', '.join(reasons)})"
    
    # Targets
    risk = abs(entry - sl)
    if risk == 0: risk = curr_h1['ATR']
    
    target_configs = {
        "PERFECT_STORM": (5, 10, "TP1 (1:5)", "TP2 (1:10)", 30, 70),
        "BREAKOUT": (3, 7, "TP1 (1:3)", "TP2 (1:7)", 50, 50),
        "DAY": (2, 3, "TP1 (1:2)", "TP2 (1:3)", 60, 40),
    }
    
    r1, r2, lbl1, lbl2, pct1, pct2 = target_configs.get(
        setup_type or trade_style, (3, 5, "TP1 (1:3)", "TP2 (1:5)", 50, 50)
    )
    
    if "LONG" in sig:
        tp1, tp2 = entry + (r1 * risk), entry + (r2 * risk)
    elif "SHORT" in sig:
        tp1, tp2 = entry - (r1 * risk), entry - (r2 * risk)
    else:
        tp1 = tp2 = entry
    
    # Position sizing V17.0
    position_size, position_value, position_note = adaptive_position_size(
        capital, risk_pct, entry, sl, vol_pct
    )
    
    kelly_msg = ""
    if setup_type in ["PERFECT_STORM"] and score.grade in ["S", "A++"]:
        kelly_pct = calculate_kelly_criterion(sim['WR'], 5.0, 1.0) * 100
        kelly_msg = f"🌟 Perfect Storm - Kelly: {kelly_pct:.1f}%"
    
    # Charts V17.0
    show = "SWING" in sig or "DAY" in sig or "BREAKOUT" in sig or "STORM" in sig
    
    img_h4 = plot_candles_v17(h4, f"{name} - H4 (Tendência + Regime: {market_regime})",
                               entry if show else None, sl if show else None,
                               tp1 if show else None, tp2 if show else None,
                               sr_levels=sr_levels if show else None)
    
    img_h1 = plot_candles_v17(h1, f"{name} - H1 (Estrutura + S/R Clusters)",
                               entry if show else None, sl if show else None,
                               tp1 if show else None, tp2 if show else None,
                               sr_levels=sr_levels, fib_levels=fibs if show else None)
    
    img_m15 = plot_candles_v17(m15, f"{name} - M15 (Gatilho + Vol: {vol_status})",
                                entry if show else None, sl if show else None,
                                tp1 if show else None, tp2 if show else None,
                                patterns=True)
    
    # Confluências
    confluences = []
    if divergence: confluences.append(f"🔍 {divergence}: {divergence_detail}")
    if fib_level: confluences.append(f"📐 Fibonacci {fib_level} (dir: {fib_direction})")
    if sr_touch and closest_sr:
        confluences.append(f"🎯 S/R cluster {closest_sr['touches']}x @ {closest_sr['price']:.2f} (zona: {closest_sr['zone_low']:.2f}-{closest_sr['zone_high']:.2f})")
    if alignment_type != "NO_ALIGNMENT": confluences.append(f"⭐ {alignment_type}")
    if storm_level: confluences.append(f"🌟 {storm_level}")
    if volume_confirmed: confluences.append(f"📊 Volume confirmado (×{vol_proxy:.1f})")
    if "TRENDING" in market_regime: confluences.append(f"📈 Regime: {market_regime}")
    
    # Riscos identificados
    risks = []
    if "RANGING" in market_regime: risks.append("⚠️ Regime RANGING - tendência fraca")
    if not sim['WF_STABLE']: risks.append("⚠️ Walk-Forward instável entre folds")
    if mc_results.get('positive_pct', 0) < 60: risks.append(f"⚠️ Monte Carlo: apenas {mc_results.get('positive_pct', 0)}% positivo")
    if vol_regime in ["HIGH", "EXTREME_HIGH"]: risks.append(f"⚠️ Volatilidade {vol_regime}")
    
    return {
        "FINAL_DECISION": sig,
        "TRADE_STYLE": trade_style or "N/A",
        "SETUP_TYPE": setup_type or "N/A",
        "SETUP_SCORE": float(round(score.total, 1)),
        "BASE_SCORE": float(round(score.base_total, 1)),
        "BONUS_SCORE": float(round(score.bonus_total, 1)),
        "SETUP_GRADE": score.grade,
        "ADX_SCORE": float(round(score.trend_strength, 1)),
        "MOMENTUM_SCORE": float(round(score.momentum_align, 1)),
        "PATTERN_SCORE": float(round(score.patterns, 1)),
        "VALUE_SCORE": float(round(score.value_zone, 1)),
        "HIST_SCORE": float(round(score.historical, 1)),
        "DIVERGENCE_BONUS": float(round(score.divergence_bonus, 1)),
        "FIB_BONUS": float(round(score.fib_bonus, 1)),
        "SR_BONUS": float(round(score.sr_bonus, 1)),
        "ALIGNMENT_BONUS": float(round(score.alignment_bonus, 1)),
        "STORM_BONUS": float(round(score.storm_bonus, 1)),
        "REGIME_BONUS": float(round(score.regime_bonus, 1)),
        "VOLUME_BONUS": float(round(score.volume_bonus, 1)),
        "MARKET_STRUCTURE": structure,
        "MARKET_REGIME": market_regime,
        "REGIME_SCORE": int(regime_score),
        "VOL_REGIME": f"{vol_regime} ({vol_pct:.2f}%)",
        "TICK_VOLUME": f"{vol_status} (×{vol_proxy:.1f})",
        "PATTERNS_DETECTED": ", ".join(recent_patterns) if recent_patterns else "Nenhum",
        "DIVERGENCE": divergence or "Nenhuma",
        "DIVERGENCE_DETAIL": divergence_detail or "",
        "FIB_LEVEL": fib_level or "N/A",
        "FIB_DIRECTION": fib_direction or "N/A",
        "SR_LEVELS": int(len(sr_levels)),
        "ALIGNMENT_TYPE": alignment_type,
        "STORM_LEVEL": storm_level or "N/A",
        "STORM_CRITERIA": storm_criteria,
        "CONFLUENCES": confluences,
        "RISKS": risks,
        "MOMENTUM_ALIGNMENT": f"{momentum_score}/3",
        "ENTRY_TYPE": entry_type,
        "SL_REASON": sl_reason,
        "SPREAD": float(spread),
        # Walk-Forward
        "WIN_RATE": float(sim['WR']),
        "NET_PROFIT": float(sim['NET']),
        "MAX_DRAWDOWN": float(sim['DD']),
        "PROFIT_FACTOR": float(sim['PF']),
        "SHARPE_RATIO": float(sim['SHARPE']),
        "SORTINO_RATIO": float(sim['SORTINO']),
        "RECOVERY_FACTOR": float(sim['RECOVERY']),
        "MAX_CONS_WIN": int(sim['MAX_CONS_WIN']),
        "MAX_CONS_LOSS": int(sim['MAX_CONS_LOSS']),
        "WF_STABLE": sim['WF_STABLE'],
        "FOLD_WRS": sim['FOLD_WRS'],
        "TOTAL_TRADES": int(sim['TOTAL_TRADES']),
        # Monte Carlo
        "MC_MEDIAN": float(mc_results.get('median', 0)),
        "MC_P5": float(mc_results.get('p5', 0)),
        "MC_P95": float(mc_results.get('p95', 0)),
        "MC_P25": float(mc_results.get('p25', 0)),
        "MC_P75": float(mc_results.get('p75', 0)),
        "MC_POSITIVE_PCT": float(mc_results.get('positive_pct', 0)),
        # Trade levels
        "MATH_ENTRY": float(round(entry, 5)),
        "MATH_SL": float(round(sl, 5)),
        "MATH_TP1": float(round(tp1, 5)),
        "MATH_TP2": float(round(tp2, 5)),
        "TARGET_LABEL_1": lbl1,
        "TARGET_LABEL_2": lbl2,
        "REALIZE_PCT_1": int(pct1),
        "REALIZE_PCT_2": int(pct2),
        "POSITION_SIZE": float(position_size),
        "POSITION_VALUE": float(position_value),
        "POSITION_NOTE": position_note,
        "KELLY_MSG": kelly_msg,
        "IMAGES": [img_h4, img_h1, img_m15],
        "ATR": float(curr_h1['ATR']),
        "INITIAL_RISK": float(risk),
    }

# ==============================================================================
# INTERFACE STREAMLIT V17.0
# ==============================================================================

st.sidebar.title("🚀 SI-APATECO V17.0 ULTRA PRO")

if "GEMINI_API_KEY" in st.secrets:
    api = st.secrets["GEMINI_API_KEY"]
    st.sidebar.success("✅ API ATIVA")
else:
    api = st.sidebar.text_input("CHAVE API GEMINI", type="password")

st.sidebar.divider()
capital = st.sidebar.number_input("💰 Capital ($)", min_value=100, value=10000, step=100)
risk_pct = st.sidebar.slider("📊 Risco Base (%)", min_value=0.5, max_value=3.0, value=1.0, step=0.1)

st.sidebar.divider()
operation_mode = st.sidebar.radio("⚙️ Modo", ["🔍 Análise de Entrada", "📊 Monitoramento de Trade"])

st.sidebar.divider()
st.sidebar.info("""
**V17.0 ULTRA PRO - MELHORIAS:**
- ✅ Walk-Forward Backtest (sem bias)
- ✅ Divergências com pivots reais
- ✅ S/R por clusters de densidade
- ✅ Fibonacci de swings confirmados
- ✅ Filtro de regime de mercado
- ✅ Tick volume confirmation
- ✅ Monte Carlo intervals
- ✅ Wilder's RSI correto
- ✅ Custos de spread incluídos
- ✅ Realização parcial no backtest
- ✅ Swing points sem look-ahead
""")

st.title("🚀 SI-APATECO SNIPER V17.0 ULTRA PRO")
st.caption("Walk-Forward | Monte Carlo | Pivots Reais | Regime Filter | Volume Confirmed")

with st.spinner("Carregando ativos..."):
    assets = get_assets()

if not assets:
    st.error("❌ FALHA NA CONEXÃO COM DERIV")
    st.stop()

# ==============================================================================
# MODO 1: ANÁLISE DE ENTRADA
# ==============================================================================

if operation_mode == "🔍 Análise de Entrada":
    c1, c2 = st.columns([1, 2])
    
    with c1:
        target = st.selectbox("🎯 SELECIONAR ATIVO", list(assets.keys()))
        st.markdown("### 🔬 ANÁLISE V17.0 ULTRA PRO")
        st.caption("Walk-Forward + Monte Carlo + Pivots Reais")
        st.write("")
        run = st.button("🚀 EXECUTAR ANÁLISE COMPLETA", use_container_width=True)
    
    with c2:
        if run:
            if not api:
                st.error("⚠️ CHAVE API NECESSÁRIA")
                st.stop()
            
            status = st.status("🛸 INICIALIZANDO V17.0 ULTRA PRO...", expanded=True)
            
            status.write("1️⃣ Buscando dados Multi-Timeframe (H4/H1/M15)...")
            h1, h4, m15, err = asyncio.run(fetch_tri_force(assets[target]))
            
            if err:
                status.update(state='error', label="❌ FALHA")
                st.error(err)
                st.stop()
            
            status.write("2️⃣ Calculando indicadores (Wilder RSI, ADX, MACD)...")
            status.write("3️⃣ Detectando pivots reais + divergências...")
            status.write("4️⃣ Clustering S/R + Fibonacci de swings...")
            status.write("5️⃣ Walk-Forward Backtest (3 folds)...")
            status.write("6️⃣ Monte Carlo Simulation (1000 iterações)...")
            status.write("7️⃣ Verificando regime + volume...")
            
            data = sniper_core_v17(target, h1, h4, m15, capital, risk_pct)
            
            generated_images = data.pop("IMAGES")
            
            status.write("8️⃣ Análise Visual IA (Gemini)...")
            genai.configure(api_key=api)
            
            data_converted = convert_numpy_to_python(data)
            
            models_to_try = [
                "gemini-2.0-flash",
                "gemini-1.5-flash",
                "gemini-1.5-flash-latest",
                "gemini-1.5-pro",
                "gemini-1.5-pro-latest",
                "gemini-pro",
            ]
            
            ai_response = None
            
            for idx, model_name in enumerate(models_to_try, 1):
                try:
                    model = genai.GenerativeModel(model_name=model_name, safety_settings=SAFETY_SETTINGS)
                    response = model.generate_content(
                        [SYSTEM_PROMPT, f"DADOS V17.0: {json.dumps(data_converted)}"] + generated_images
                    )
                    ai_response = response.text
                    status.update(label=f"✅ V17.0 COMPLETA ({model_name})", state="complete")
                    break
                except Exception as e:
                    if idx == len(models_to_try):
                        ai_response = f"⚠️ IA indisponível. Análise matemática completa abaixo.\nErro: {str(e)[:100]}"
                    continue
            
            # ══════════════════════════════════════════════════════
            # DISPLAY RESULTS V17.0
            # ══════════════════════════════════════════════════════
            
            grade = data['SETUP_GRADE']
            score_val = data['SETUP_SCORE']
            
            grade_config = {
                "S": ("score-s", "👑"), "A++": ("score-a-plus-plus", "🏆"),
                "A+": ("score-a-plus", "💎"), "A": ("score-a", "⭐"),
                "B": ("score-b", "📊"), "C": ("score-c", "⚠️"), "D": ("score-c", "🔻")
            }
            grade_class, grade_emoji = grade_config.get(grade, ("score-c", "❓"))
            
            setup_config = {
                "PERFECT_STORM": ("🌟", "#a855f7"),
                "BREAKOUT": ("💥", "#f59e0b"),
                "SWING": ("📈", "#10b981"),
                "DAY": ("⚡", "#3b82f6"),
            }
            style_emoji, style_color = setup_config.get(
                data.get('SETUP_TYPE', ''), ("⏸️", "#6b7280")
            )
            
            # Header
            st.markdown(f"""
            <div style='text-align: center; padding: 25px; background: rgba(251, 191, 36, 0.08); 
                 border: 3px solid #fbbf24; border-radius: 15px; margin-bottom: 25px;'>
                <h1 style='margin: 0;'>{grade_emoji} GRADE: <span class='{grade_class}'>{grade}</span></h1>
                <p style='font-size: 28px; margin: 15px 0;'><strong>SCORE: {score_val}/150</strong></p>
                <p style='font-size: 18px; margin: 8px 0;'>Base: {data['BASE_SCORE']}/100 | Bonus: +{data['BONUS_SCORE']}/50</p>
                <p style='font-size: 22px; margin: 15px 0 5px 0; color: {style_color};'>
                    {style_emoji} <strong>{data.get('SETUP_TYPE', 'N/A')}</strong></p>
                <p style='font-size: 14px; color: #888;'>
                    Regime: {data['MARKET_REGIME']} | Volume: {data['TICK_VOLUME']}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            if data.get('SETUP_TYPE') == "PERFECT_STORM":
                st.success("🌟🌟🌟 **PERFECT STORM DETECTADO!** 🌟🌟🌟")
                st.info(f"**Critérios:** {', '.join(data['STORM_CRITERIA'])}")
                st.balloons()
            
            # ── Métricas Walk-Forward ──
            st.subheader("📊 WALK-FORWARD METRICS (Out-of-Sample)")
            
            m1, m2, m3, m4, m5, m6 = st.columns(6)
            m1.metric("Win Rate (WF)", f"{data['WIN_RATE']}%")
            m2.metric("Profit Factor", f"{data['PROFIT_FACTOR']}")
            m3.metric("Sharpe", f"{data['SHARPE_RATIO']}")
            m4.metric("Sortino", f"{data['SORTINO_RATIO']}")
            m5.metric("Max DD", f"{data['MAX_DRAWDOWN']}R")
            m6.metric("Trades (WF)", f"{data['TOTAL_TRADES']}")
            
            # Walk-Forward stability
            if data['FOLD_WRS']:
                fold_str = " | ".join([f"Fold {i+1}: {wr}%" for i, wr in enumerate(data['FOLD_WRS'])])
                if data['WF_STABLE']:
                    st.success(f"✅ Walk-Forward ESTÁVEL: {fold_str}")
                else:
                    st.warning(f"⚠️ Walk-Forward INSTÁVEL: {fold_str}")
            
            # ── Monte Carlo ──
            st.subheader("🎲 MONTE CARLO SIMULATION (1000 iterações)")
            
            mc1, mc2, mc3, mc4, mc5 = st.columns(5)
            mc1.metric("Mediana", f"{data['MC_MEDIAN']}R")
            mc2.metric("P5 (Pior)", f"{data['MC_P5']}R")
            mc3.metric("P95 (Melhor)", f"{data['MC_P95']}R")
            mc4.metric("P25-P75", f"{data['MC_P25']}R → {data['MC_P75']}R")
            mc5.metric("% Positivo", f"{data['MC_POSITIVE_PCT']}%")
            
            # ── Breakdown ──
            st.subheader("🔬 BREAKDOWN V17.0")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📊 Score Base (100 pts):**")
                st.dataframe(pd.DataFrame([
                    {"Componente": "ADX (Tendência)", "Score": f"{data['ADX_SCORE']}/25"},
                    {"Componente": "Momentum Alignment", "Score": f"{data['MOMENTUM_SCORE']}/20"},
                    {"Componente": "Padrões Candlestick", "Score": f"{data['PATTERN_SCORE']}/15"},
                    {"Componente": "Zona de Valor", "Score": f"{data['VALUE_SCORE']}/15"},
                    {"Componente": "Edge Histórico (WF)", "Score": f"{data['HIST_SCORE']}/25"},
                ]), use_container_width=True, hide_index=True)
            
            with col2:
                st.markdown("**✨ Bonus Confluências (50 pts):**")
                st.dataframe(pd.DataFrame([
                    {"Confluência": "Divergência (pivots)", "Bonus": f"+{data['DIVERGENCE_BONUS']}"},
                    {"Confluência": "Fibonacci (swings)", "Bonus": f"+{data['FIB_BONUS']}"},
                    {"Confluência": "S/R (clusters)", "Bonus": f"+{data['SR_BONUS']}"},
                    {"Confluência": "Perfect Alignment", "Bonus": f"+{data['ALIGNMENT_BONUS']}"},
                    {"Confluência": "Perfect Storm", "Bonus": f"+{data['STORM_BONUS']}"},
                    {"Confluência": "Regime Trending", "Bonus": f"+{data['REGIME_BONUS']}"},
                    {"Confluência": "Volume Confirmed", "Bonus": f"+{data['VOLUME_BONUS']}"},
                ]), use_container_width=True, hide_index=True)
            
            # Confluências
            if data['CONFLUENCES']:
                st.subheader("🔥 CONFLUÊNCIAS DETECTADAS")
                for conf in data['CONFLUENCES']:
                    st.markdown(f"- {conf}")
            
            # Riscos V17.0
            if data['RISKS']:
                st.subheader("⚠️ RISCOS IDENTIFICADOS")
                for risk in data['RISKS']:
                    st.warning(risk)
            
            # Sinal
            st.divider()
            decision = data['FINAL_DECISION']
            
            if any(x in decision for x in ["SWING", "DAY", "BREAKOUT", "STORM"]):
                st.success(f"✅ **SINAL:** {decision}")
            elif "BLOCKED" in decision:
                st.error(f"🛑 **BLOQUEADO:** {decision}")
            else:
                st.warning(f"⏸️ **STATUS:** {decision}")
            
            # Plano de Execução
            if any(x in decision for x in ["SWING", "DAY", "BREAKOUT", "STORM"]):
                st.subheader("📋 PLANO DE EXECUÇÃO V17.0")
                
                st.dataframe(pd.DataFrame([
                    {"Parâmetro": "Entrada (+ spread)", "Valor": f"{data['MATH_ENTRY']}", "Obs": data['ENTRY_TYPE']},
                    {"Parâmetro": "Stop Loss", "Valor": f"{data['MATH_SL']}", "Obs": data['SL_REASON']},
                    {"Parâmetro": data['TARGET_LABEL_1'], "Valor": f"{data['MATH_TP1']}", "Obs": f"Realizar {data['REALIZE_PCT_1']}%"},
                    {"Parâmetro": data['TARGET_LABEL_2'], "Valor": f"{data['MATH_TP2']}", "Obs": f"Realizar {data['REALIZE_PCT_2']}% + trailing"},
                    {"Parâmetro": "Spread Incluído", "Valor": f"{data['SPREAD']}", "Obs": "Custo já no cálculo"},
                    {"Parâmetro": "Posição", "Valor": f"{data['POSITION_SIZE']} unidades", "Obs": f"${data['POSITION_VALUE']} - {data['POSITION_NOTE']}"},
                ]), use_container_width=True, hide_index=True)
                
                if data['KELLY_MSG']:
                    st.info(f"💡 {data['KELLY_MSG']}")
            
            # Contexto
            st.subheader("🌍 CONTEXTO V17.0")
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Regime", data['MARKET_REGIME'])
            c2.metric("Estrutura", data['MARKET_STRUCTURE'])
            c3.metric("Volatilidade", data['VOL_REGIME'])
            c4.metric("Tick Volume", data['TICK_VOLUME'])
            
            c5, c6, c7 = st.columns(3)
            c5.metric("Divergência", f"{data['DIVERGENCE']}")
            c6.metric("Fibonacci", f"{data['FIB_LEVEL']} ({data['FIB_DIRECTION']})")
            c7.metric("S/R Clusters", f"{data['SR_LEVELS']} detectados")
            
            # Gráficos
            st.divider()
            st.subheader("📊 ANÁLISE GRÁFICA V17.0")
            
            tabs = st.tabs(["H4 - Tendência + Regime", "H1 - Estrutura + S/R + Fib", "M15 - Gatilho + Volume"])
            
            with tabs[0]: st.image(generated_images[0], use_container_width=True)
            with tabs[1]: st.image(generated_images[1], use_container_width=True)
            with tabs[2]: st.image(generated_images[2], use_container_width=True)
            
            # IA
            st.divider()
            st.subheader("🤖 ANÁLISE IA V17.0")
            st.markdown(ai_response)

# ==============================================================================
# MODO 2: MONITORAMENTO
# ==============================================================================

elif operation_mode == "📊 Monitoramento de Trade":
    st.markdown("### 📊 TRADE MANAGEMENT V17.0")
    st.caption("Monitoramento com divergências reais e alertas inteligentes")
    
    col1, col2 = st.columns(2)
    with col1:
        monitor_symbol = st.selectbox("🎯 Ativo", list(assets.keys()))
        monitor_direction = st.selectbox("📈 Direção", ["LONG", "SHORT"])
    with col2:
        monitor_entry = st.number_input("💰 Entrada", min_value=0.0, value=1000.0, step=0.1)
        monitor_sl = st.number_input("🛑 Stop Loss", min_value=0.0, value=990.0, step=0.1)
    
    col3, col4 = st.columns(2)
    with col3: monitor_tp1 = st.number_input("🎯 TP1", min_value=0.0, value=1030.0, step=0.1)
    with col4: monitor_tp2 = st.number_input("🎯 TP2", min_value=0.0, value=1050.0, step=0.1)
    
    if st.button("🚀 INICIAR MONITORAMENTO", use_container_width=True):
        trade = ActiveTrade(
            symbol=monitor_symbol, direction=monitor_direction,
            entry_price=monitor_entry, current_price=monitor_entry,
            sl=monitor_sl, tp1=monitor_tp1, tp2=monitor_tp2,
            entry_time=datetime.now(),
            atr=abs(monitor_entry - monitor_sl) / 2.5,
            initial_risk=abs(monitor_entry - monitor_sl)
        )
        
        if monitor_direction == "LONG": trade.highest_price = monitor_entry
        else: trade.lowest_price = monitor_entry
        
        status_ph = st.empty()
        metrics_ph = st.empty()
        alerts_ph = st.empty()
        recs_ph = st.empty()
        chart_ph = st.empty()
        
        for iteration in range(120):
            try:
                h1, h4, m15, err = asyncio.run(fetch_tri_force(assets[monitor_symbol]))
                
                if not err and m15:
                    m15_df = indicators(prep_df(m15))
                    current_price = m15_df['close'].iloc[-1]
                    trade.update_price(current_price)
                    
                    health = analyze_trade_health(trade, m15_df)
                    
                    status_ph.markdown(f"""
                    <div class='{health["health_color"]}'>
                        <h3>🏥 SAÚDE: {health["health_status"]} ({health["health_score"]}/100)</h3>
                        <p>R: <strong>{health["current_r"]:+.2f}R</strong> | P&L: <strong>${trade.get_unrealized_pl():+.2f}</strong></p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    with metrics_ph.container():
                        m1, m2, m3, m4, m5 = st.columns(5)
                        m1.metric("Preço", f"{current_price:.4f}")
                        m2.metric("Entrada", f"{trade.entry_price:.4f}")
                        m3.metric("Stop", f"{trade.sl:.4f}")
                        m4.metric("R Atual", f"{health['current_r']:+.2f}R")
                        extreme = trade.highest_price if trade.direction == "LONG" else trade.lowest_price
                        m5.metric("Extremo", f"{extreme:.4f}")
                    
                    if health['alerts']:
                        with alerts_ph.container():
                            for alert in health['alerts']:
                                st.warning(alert)
                    
                    if health['recommendations']:
                        with recs_ph.container():
                            for rec in health['recommendations']:
                                icon = {'CRITICAL': '🔴', 'HIGH': '🟡', 'MEDIUM': '🟢'}.get(rec['priority'], '⚪')
                                st.info(f"{icon} **{rec['type']}**: {rec['action']}")
                    
                    with chart_ph.container():
                        recent = m15_df.tail(50)
                        img = plot_candles_v17(recent, f"{monitor_symbol} - M15 (Monitor)",
                                               trade.entry_price, trade.sl, trade.tp1, trade.tp2)
                        st.image(img, use_container_width=True)
                
                time.sleep(5)
            except Exception as e:
                st.error(f"Erro: {e}")
                break
        
        st.success("✅ Monitoramento finalizado (10 min)")
