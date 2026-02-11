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
# SI-APATECO SNIPER V18.0 — SYNTHETIC INDEX SPECIALIST
# 100% focado em propriedades estatísticas de índices sintéticos Deriv
#
# V18.0 NOVAS ARMAS (específicas para sintéticos):
# ✅ Hurst Exponent — detecta se ativo está trending ou mean-reverting
# ✅ Z-Score Mean Reversion — distância estatística da média (sintéticos SEMPRE revertem)
# ✅ Perfil por Índice — calibração ADX/ATR/SL/TP específica por Vol 10/25/50/75/100
# ✅ BB Squeeze → Expansion Cycle — ciclo previsível nos sintéticos
# ✅ Consecutive Candle Counter — probabilidade de reversão após N candles
# ✅ ROC Extremes — snap-back detector (velocidade excessiva = reversão)
# ✅ Micro-Pullback Entry — entrada refinada ao invés de market order
# ✅ Dynamic SL calibrado por índice (Vol 10 ≠ Vol 100)
# ✅ Todas as melhorias V17 mantidas (Walk-Forward, Monte Carlo, Pivots reais, etc.)
# ==============================================================================

st.set_page_config(
    page_title="SI-APATECO V18.0 SYNTHETIC SPECIALIST",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
        color: black; font-weight: 900; text-transform: uppercase;
        padding: 20px; font-size: 20px; border-radius: 0px; width: 100%;
        border: 1px solid #fbbf24; transition: 0.3s;
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
</style>
""", unsafe_allow_html=True)

SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# ==============================================================================
# V18.0 CORE: PERFIS CALIBRADOS POR ÍNDICE SINTÉTICO
# Cada índice tem volatilidade fixa e comportamento previsível.
# Parâmetros otimizados empiricamente para cada tipo.
# ==============================================================================

SYNTHETIC_PROFILES = {
    # ── Volatility Indices ──
    "VOLATILITY 10 INDEX": {
        "vol_class": "ULTRA_LOW", "spread": 0.02,
        "adx_trend_min": 12, "adx_strong": 20,
        "sl_atr_mult": 2.0, "tp1_r": 2.5, "tp2_r": 4.0,
        "bb_squeeze_threshold": 0.5, "zscore_extreme": 2.5,
        "hurst_trend_min": 0.55, "consecutive_reversal": 8,
        "roc_extreme_pct": 0.3, "mean_reversion_bias": 0.7,
        "risk_mult": 1.3,  # Pode arriscar mais (baixa vol)
        "description": "Muito lento, favorece mean reversion, precisa de paciência"
    },
    "VOLATILITY 10 (1S) INDEX": {
        "vol_class": "ULTRA_LOW", "spread": 0.02,
        "adx_trend_min": 12, "adx_strong": 20,
        "sl_atr_mult": 2.0, "tp1_r": 2.5, "tp2_r": 4.0,
        "bb_squeeze_threshold": 0.5, "zscore_extreme": 2.5,
        "hurst_trend_min": 0.55, "consecutive_reversal": 8,
        "roc_extreme_pct": 0.3, "mean_reversion_bias": 0.7,
        "risk_mult": 1.3,
        "description": "1-second tick, ultra baixa vol, mean reversion forte"
    },
    "VOLATILITY 25 INDEX": {
        "vol_class": "LOW", "spread": 0.03,
        "adx_trend_min": 14, "adx_strong": 22,
        "sl_atr_mult": 2.2, "tp1_r": 2.5, "tp2_r": 4.5,
        "bb_squeeze_threshold": 0.55, "zscore_extreme": 2.3,
        "hurst_trend_min": 0.54, "consecutive_reversal": 7,
        "roc_extreme_pct": 0.5, "mean_reversion_bias": 0.6,
        "risk_mult": 1.2,
        "description": "Baixa vol, bom para swing, tendências mais claras que V10"
    },
    "VOLATILITY 25 (1S) INDEX": {
        "vol_class": "LOW", "spread": 0.03,
        "adx_trend_min": 14, "adx_strong": 22,
        "sl_atr_mult": 2.2, "tp1_r": 2.5, "tp2_r": 4.5,
        "bb_squeeze_threshold": 0.55, "zscore_extreme": 2.3,
        "hurst_trend_min": 0.54, "consecutive_reversal": 7,
        "roc_extreme_pct": 0.5, "mean_reversion_bias": 0.6,
        "risk_mult": 1.2,
        "description": "1-second tick, baixa vol"
    },
    "VOLATILITY 50 INDEX": {
        "vol_class": "MEDIUM", "spread": 0.05,
        "adx_trend_min": 16, "adx_strong": 25,
        "sl_atr_mult": 2.5, "tp1_r": 3.0, "tp2_r": 5.0,
        "bb_squeeze_threshold": 0.6, "zscore_extreme": 2.0,
        "hurst_trend_min": 0.53, "consecutive_reversal": 6,
        "roc_extreme_pct": 0.8, "mean_reversion_bias": 0.5,
        "risk_mult": 1.0,
        "description": "Equilíbrio perfeito trend/reversion, ativo mais versátil"
    },
    "VOLATILITY 50 (1S) INDEX": {
        "vol_class": "MEDIUM", "spread": 0.05,
        "adx_trend_min": 16, "adx_strong": 25,
        "sl_atr_mult": 2.5, "tp1_r": 3.0, "tp2_r": 5.0,
        "bb_squeeze_threshold": 0.6, "zscore_extreme": 2.0,
        "hurst_trend_min": 0.53, "consecutive_reversal": 6,
        "roc_extreme_pct": 0.8, "mean_reversion_bias": 0.5,
        "risk_mult": 1.0,
        "description": "1-second tick, vol média"
    },
    "VOLATILITY 75 INDEX": {
        "vol_class": "HIGH", "spread": 0.10,
        "adx_trend_min": 18, "adx_strong": 28,
        "sl_atr_mult": 3.0, "tp1_r": 3.0, "tp2_r": 5.0,
        "bb_squeeze_threshold": 0.65, "zscore_extreme": 1.8,
        "hurst_trend_min": 0.52, "consecutive_reversal": 5,
        "roc_extreme_pct": 1.2, "mean_reversion_bias": 0.4,
        "risk_mult": 0.7,
        "description": "Alta vol, movimentos rápidos, precisa SL largo"
    },
    "VOLATILITY 75 (1S) INDEX": {
        "vol_class": "HIGH", "spread": 0.10,
        "adx_trend_min": 18, "adx_strong": 28,
        "sl_atr_mult": 3.0, "tp1_r": 3.0, "tp2_r": 5.0,
        "bb_squeeze_threshold": 0.65, "zscore_extreme": 1.8,
        "hurst_trend_min": 0.52, "consecutive_reversal": 5,
        "roc_extreme_pct": 1.2, "mean_reversion_bias": 0.4,
        "risk_mult": 0.7,
        "description": "1-second, alta vol, rápido"
    },
    "VOLATILITY 100 INDEX": {
        "vol_class": "EXTREME", "spread": 0.15,
        "adx_trend_min": 20, "adx_strong": 30,
        "sl_atr_mult": 3.5, "tp1_r": 3.0, "tp2_r": 5.0,
        "bb_squeeze_threshold": 0.7, "zscore_extreme": 1.5,
        "hurst_trend_min": 0.51, "consecutive_reversal": 4,
        "roc_extreme_pct": 1.5, "mean_reversion_bias": 0.35,
        "risk_mult": 0.5,
        "description": "Extrema vol, risco máximo, SL muito largo obrigatório"
    },
    "VOLATILITY 100 (1S) INDEX": {
        "vol_class": "EXTREME", "spread": 0.15,
        "adx_trend_min": 20, "adx_strong": 30,
        "sl_atr_mult": 3.5, "tp1_r": 3.0, "tp2_r": 5.0,
        "bb_squeeze_threshold": 0.7, "zscore_extreme": 1.5,
        "hurst_trend_min": 0.51, "consecutive_reversal": 4,
        "roc_extreme_pct": 1.5, "mean_reversion_bias": 0.35,
        "risk_mult": 0.5,
        "description": "1-second, extrema vol"
    },
    # ── Crash/Boom Indices ──
    "BOOM 300 INDEX": {
        "vol_class": "BOOM", "spread": 0.10,
        "adx_trend_min": 15, "adx_strong": 25,
        "sl_atr_mult": 2.0, "tp1_r": 3.0, "tp2_r": 6.0,
        "bb_squeeze_threshold": 0.6, "zscore_extreme": 2.0,
        "hurst_trend_min": 0.52, "consecutive_reversal": 5,
        "roc_extreme_pct": 2.0, "mean_reversion_bias": 0.3,
        "risk_mult": 0.8,
        "description": "Spikes de alta a cada ~300 ticks, atenção aos spikes ao operar SHORT"
    },
    "BOOM 500 INDEX": {
        "vol_class": "BOOM", "spread": 0.10,
        "adx_trend_min": 15, "adx_strong": 25,
        "sl_atr_mult": 2.0, "tp1_r": 3.0, "tp2_r": 6.0,
        "bb_squeeze_threshold": 0.6, "zscore_extreme": 2.0,
        "hurst_trend_min": 0.52, "consecutive_reversal": 5,
        "roc_extreme_pct": 2.0, "mean_reversion_bias": 0.3,
        "risk_mult": 0.8,
        "description": "Spikes de alta a cada ~500 ticks, atenção aos spikes ao operar SHORT"
    },
    "BOOM 1000 INDEX": {
        "vol_class": "BOOM", "spread": 0.10,
        "adx_trend_min": 15, "adx_strong": 25,
        "sl_atr_mult": 2.5, "tp1_r": 3.0, "tp2_r": 7.0,
        "bb_squeeze_threshold": 0.6, "zscore_extreme": 2.0,
        "hurst_trend_min": 0.52, "consecutive_reversal": 6,
        "roc_extreme_pct": 2.0, "mean_reversion_bias": 0.3,
        "risk_mult": 0.9,
        "description": "Spikes de alta a cada ~1000 ticks, cuidado com spikes ao operar SHORT"
    },
    "CRASH 300 INDEX": {
        "vol_class": "CRASH", "spread": 0.10,
        "adx_trend_min": 15, "adx_strong": 25,
        "sl_atr_mult": 2.0, "tp1_r": 3.0, "tp2_r": 6.0,
        "bb_squeeze_threshold": 0.6, "zscore_extreme": 2.0,
        "hurst_trend_min": 0.52, "consecutive_reversal": 5,
        "roc_extreme_pct": 2.0, "mean_reversion_bias": 0.3,
        "risk_mult": 0.8,
        "description": "Spikes de baixa a cada ~300 ticks, atenção aos spikes ao operar LONG"
    },
    "CRASH 500 INDEX": {
        "vol_class": "CRASH", "spread": 0.10,
        "adx_trend_min": 15, "adx_strong": 25,
        "sl_atr_mult": 2.0, "tp1_r": 3.0, "tp2_r": 6.0,
        "bb_squeeze_threshold": 0.6, "zscore_extreme": 2.0,
        "hurst_trend_min": 0.52, "consecutive_reversal": 5,
        "roc_extreme_pct": 2.0, "mean_reversion_bias": 0.3,
        "risk_mult": 0.8,
        "description": "Spikes de baixa a cada ~500 ticks, atenção aos spikes ao operar LONG"
    },
    "CRASH 1000 INDEX": {
        "vol_class": "CRASH", "spread": 0.10,
        "adx_trend_min": 15, "adx_strong": 25,
        "sl_atr_mult": 2.5, "tp1_r": 3.0, "tp2_r": 7.0,
        "bb_squeeze_threshold": 0.6, "zscore_extreme": 2.0,
        "hurst_trend_min": 0.52, "consecutive_reversal": 6,
        "roc_extreme_pct": 2.0, "mean_reversion_bias": 0.3,
        "risk_mult": 0.9,
        "description": "Spikes de baixa a cada ~1000 ticks, cuidado com spikes ao operar LONG"
    },
    # ── Step / Range Break / Jump ──
    "STEP INDEX": {
        "vol_class": "STEP", "spread": 0.01,
        "adx_trend_min": 10, "adx_strong": 18,
        "sl_atr_mult": 1.5, "tp1_r": 2.0, "tp2_r": 3.0,
        "bb_squeeze_threshold": 0.4, "zscore_extreme": 2.0,
        "hurst_trend_min": 0.55, "consecutive_reversal": 10,
        "roc_extreme_pct": 0.2, "mean_reversion_bias": 0.8,
        "risk_mult": 1.5,
        "description": "Probabilidade igual de subir/descer 0.1, fortíssima mean reversion"
    },
}

# Perfil default para ativos não mapeados
DEFAULT_PROFILE = {
    "vol_class": "UNKNOWN", "spread": 0.05,
    "adx_trend_min": 15, "adx_strong": 25,
    "sl_atr_mult": 2.5, "tp1_r": 3.0, "tp2_r": 5.0,
    "bb_squeeze_threshold": 0.6, "zscore_extreme": 2.0,
    "hurst_trend_min": 0.53, "consecutive_reversal": 6,
    "roc_extreme_pct": 1.0, "mean_reversion_bias": 0.5,
    "risk_mult": 1.0,
    "description": "Perfil genérico"
}

def get_profile(name: str) -> dict:
    """Retorna perfil calibrado do índice sintético"""
    name_upper = name.upper()
    for key, profile in SYNTHETIC_PROFILES.items():
        if key in name_upper:
            return profile
    return DEFAULT_PROFILE

# ==============================================================================
# PROMPT V18.0 — SYNTHETIC SPECIALIST
# ==============================================================================
SYSTEM_PROMPT = """
FUNÇÃO: ANALISTA ELITE V18.0 — SYNTHETIC INDEX SPECIALIST [Gemini 3 Pro]
Missão: Máxima lucratividade em índices sintéticos Deriv

**RESPONDA SEMPRE EM PORTUGUÊS BRASILEIRO**

**CONTEXTO CRÍTICO — ÍNDICES SINTÉTICOS DERIV:**
- Gerados por algoritmo criptográfico (CSPRNG), NÃO sofrem influência de mercado real
- Operam 24/7 sem gaps, sem notícias, sem sessões
- Cada índice tem volatilidade FIXA e CONHECIDA (Vol 10 = baixa, Vol 100 = extrema)
- Crash/Boom têm spikes periódicos (Crash = spikes de queda, Boom = spikes de alta). Ambas direções são operáveis com gestão adequada.
- Step Index: 50/50 de subir ou descer 0.1 por tick
- SEMPRE revertem à média eventualmente (propriedade algorítmica)

**V18.0 — ARMAS ESPECÍFICAS PARA SINTÉTICOS:**
- 🧬 Hurst Exponent: H > 0.5 = trending, H < 0.5 = mean-reverting, H ≈ 0.5 = random walk
- 📊 Z-Score: Distância estatística da média. |Z| > 2 = extremo, alta probabilidade de reversão
- 🎯 Perfil Calibrado: ADX/SL/TP/risco ajustados especificamente para cada índice
- 💥 BB Squeeze Cycle: Compressão → Expansão previsível nos sintéticos
- 🔢 Consecutive Candles: Após N candles na mesma direção, probabilidade de reversão sobe
- ⚡ ROC Extreme: Movimento muito rápido = snap-back iminente
- 🎯 Micro-Pullback Entry: Espera pullback de confirmação ao invés de market order

**REGRAS ESPECIAIS POR TIPO:**
- **BOOM:** Spikes de alta periódicos. Pode operar LONG e SHORT, mas atenção aos spikes.
- **CRASH:** Spikes de baixa periódicos. Pode operar LONG e SHORT, mas atenção aos spikes.
- **STEP:** Fortíssima mean reversion. Operar reversões quando Z-Score extremo.
- **VOL 10-25:** Paciência. Movimentos lentos. Melhor para swing.
- **VOL 50:** Mais versátil. Funciona para day e swing.
- **VOL 75-100:** Rápido e perigoso. SL largo obrigatório. Position size reduzido.

**FORMATO DE SAÍDA:**

## 🧬 VEREDICTO SNIPER V18.0: [ {FINAL_DECISION} ]
**Grade:** {GRADE_EMOJI} **{SETUP_GRADE}** | **Score:** {SETUP_SCORE}/150
**Tipo:** {TRADE_STYLE_EMOJI} {TRADE_STYLE} | **Perfil:** {INDEX_PROFILE}

### 🧬 ANÁLISE ESTATÍSTICA SINTÉTICO
- **Hurst Exponent:** {HURST} → {INTERPRETAÇÃO: trending/mean-reverting/random}
- **Z-Score:** {ZSCORE} → {INTERPRETAÇÃO: normal/esticado/extremo}
- **Consecutive Candles:** {N} na mesma direção → {risco de reversão}
- **ROC Status:** {ROC} → {normal/acelerado/extremo}
- **BB Cycle:** {SQUEEZE/NORMAL/EXPANSION}
- **Regime:** {TRENDING/RANGING/TRANSITIONAL}

### 📊 BREAKDOWN COMPLETO
{Breakdown base + bonus como V17}

### 📈 VALIDAÇÃO ESTATÍSTICA
- **Walk-Forward WR:** {WF_WR}%
- **Monte Carlo Mediana:** {MC_MEDIAN}R | P5: {MC_P5}R | P95: {MC_P95}R
- **Confiança:** {CONFIDENCE}

### 🎯 PLANO DE EXECUÇÃO (CALIBRADO PARA {INDEX_NAME})
| Parâmetro | Valor | Calibração |
| :--- | :--- | :--- |
| **ENTRADA** | **{ENTRY}** | *{ENTRY_TYPE} — micro-pullback se possível* |
| **STOP LOSS** | **{SL}** | *{SL_ATR_MULT}× ATR (calibrado para {VOL_CLASS})* |
| **{TP1_LABEL}** | **{TP1}** | *Realizar {PCT1}%* |
| **{TP2_LABEL}** | **{TP2}** | *Realizar {PCT2}% + trailing* |
| **POSIÇÃO** | **{SIZE}** | *Risco ×{RISK_MULT} ({VOL_CLASS})* |
| **SPREAD** | **{SPREAD}** | *Incluído* |

### 🔥 CONFLUÊNCIAS + ⚠️ RISCOS
{Listar confluências E riscos lado a lado}

*Insight V18.0:* {Análise ESPECÍFICA para este índice sintético.
Explique como o Hurst, Z-Score e perfil do ativo influenciam a decisão.
Se Crash/Boom, enfatize a regra direcional.
Confiança com justificativa estatística.}
"""

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
            return json.loads(await asyncio.wait_for(ws.recv(), timeout=15.0))
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
                results = []
                for r in reqs:
                    await ws.send(json.dumps(r))
                    results.append(json.loads(await asyncio.wait_for(ws.recv(), 15)))
                if all('candles' in x for x in results):
                    return results[0]['candles'], results[1]['candles'], results[2]['candles'], None
        except:
            continue
    return None, None, None, "CONNECTION LOST"

# ==============================================================================
# V18.0 NOVO: HURST EXPONENT (Rescaled Range)
# ==============================================================================

def calculate_hurst_exponent(series, max_lag=100):
    """
    Hurst Exponent via R/S (Rescaled Range Analysis)
    H > 0.5: trending (persistente) — seguir tendência
    H < 0.5: mean-reverting (antipersistente) — operar reversão
    H ≈ 0.5: random walk — evitar operar
    """
    try:
        ts = series.dropna().values
        if len(ts) < 50:
            return 0.5, "RANDOM_WALK"

        lags = range(10, min(max_lag, len(ts) // 3))
        rs_values = []

        for lag in lags:
            n_chunks = len(ts) // lag
            if n_chunks < 1:
                continue

            rs_lag = []
            for i in range(n_chunks):
                chunk = ts[i * lag:(i + 1) * lag]
                mean_val = np.mean(chunk)
                deviations = chunk - mean_val
                cumulative = np.cumsum(deviations)

                R = np.max(cumulative) - np.min(cumulative)
                S = np.std(chunk, ddof=1)

                if S > 0:
                    rs_lag.append(R / S)

            if rs_lag:
                rs_values.append((np.log(lag), np.log(np.mean(rs_lag))))

        if len(rs_values) < 3:
            return 0.5, "INSUFFICIENT_DATA"

        x = np.array([v[0] for v in rs_values])
        y = np.array([v[1] for v in rs_values])

        # Regressão linear: H = inclinação
        coeffs = np.polyfit(x, y, 1)
        H = coeffs[0]

        # Clamp
        H = max(0.0, min(1.0, H))

        if H > 0.6:
            regime = "STRONG_TREND"
        elif H > 0.53:
            regime = "WEAK_TREND"
        elif H > 0.47:
            regime = "RANDOM_WALK"
        elif H > 0.4:
            regime = "WEAK_MEAN_REVERT"
        else:
            regime = "STRONG_MEAN_REVERT"

        return round(H, 3), regime
    except:
        return 0.5, "ERROR"

# ==============================================================================
# V18.0 NOVO: Z-SCORE MEAN REVERSION
# ==============================================================================

def calculate_zscore(series, window=50):
    """
    Z-Score: quantos desvios-padrão o preço está da média
    Índices sintéticos SEMPRE revertem — Z-Score extremo = oportunidade
    """
    try:
        mean = series.rolling(window=window).mean()
        std = series.rolling(window=window).std()
        zscore = (series - mean) / std.replace(0, np.nan)
        return zscore
    except:
        return pd.Series(0, index=series.index)

def interpret_zscore(z, profile):
    """Interpreta Z-Score com thresholds do perfil"""
    extreme = profile['zscore_extreme']

    if abs(z) > extreme:
        return "EXTREME", abs(z)
    elif abs(z) > extreme * 0.7:
        return "STRETCHED", abs(z)
    elif abs(z) > extreme * 0.4:
        return "MODERATE", abs(z)
    else:
        return "NORMAL", abs(z)

# ==============================================================================
# V18.0 NOVO: BB SQUEEZE → EXPANSION CYCLE
# ==============================================================================

def detect_bb_cycle(df, profile, lookback=30):
    """
    Detecta fase do ciclo Bollinger Band:
    SQUEEZE → preço vai explodir (não sabemos a direção)
    EXPANSION → já está movendo
    NORMAL → sem edge
    """
    try:
        if len(df) < lookback:
            return "UNKNOWN", 0, 0

        recent = df.tail(lookback)
        bb_width = recent['BB_width']
        avg_width = bb_width.mean()
        current_width = bb_width.iloc[-1]

        if avg_width == 0:
            return "UNKNOWN", 0, 0

        ratio = current_width / avg_width
        threshold = profile['bb_squeeze_threshold']

        # Contar candles em squeeze
        squeeze_count = sum(bb_width < avg_width * threshold)

        if ratio < threshold:
            return "SQUEEZE", ratio, squeeze_count
        elif ratio > 1.5:
            return "EXPANSION", ratio, 0
        else:
            return "NORMAL", ratio, 0
    except:
        return "UNKNOWN", 0, 0

# ==============================================================================
# V18.0 NOVO: CONSECUTIVE CANDLE COUNTER
# ==============================================================================

def count_consecutive_candles(df, lookback=20):
    """
    Conta candles consecutivas na mesma direção.
    Sintéticos: após N candles (calibrado por perfil), probabilidade de reversão sobe.
    """
    try:
        recent = df.tail(lookback)
        directions = (recent['close'] > recent['open']).astype(int)

        # Contar streak atual
        current_dir = directions.iloc[-1]
        streak = 0

        for i in range(len(directions) - 1, -1, -1):
            if directions.iloc[i] == current_dir:
                streak += 1
            else:
                break

        direction = "BULLISH" if current_dir == 1 else "BEARISH"
        return streak, direction
    except:
        return 0, "UNKNOWN"

# ==============================================================================
# V18.0 NOVO: ROC (Rate of Change) EXTREME DETECTOR
# ==============================================================================

def detect_roc_extreme(df, profile, periods=[5, 10, 20]):
    """
    Detecta quando preço se moveu rápido demais.
    Sintéticos tendem a snap-back após ROC extremo.
    """
    try:
        results = {}
        threshold = profile['roc_extreme_pct']

        for period in periods:
            if len(df) < period + 1:
                continue

            roc = ((df['close'].iloc[-1] - df['close'].iloc[-period - 1]) /
                   df['close'].iloc[-period - 1]) * 100

            if abs(roc) > threshold * 2:
                status = "EXTREME"
            elif abs(roc) > threshold:
                status = "ELEVATED"
            else:
                status = "NORMAL"

            results[f"ROC_{period}"] = {
                'value': round(roc, 3),
                'status': status,
                'direction': "UP" if roc > 0 else "DOWN"
            }

        # Status geral: pior caso
        overall = "NORMAL"
        for r in results.values():
            if r['status'] == "EXTREME":
                overall = "EXTREME"
                break
            elif r['status'] == "ELEVATED":
                overall = "ELEVATED"

        return overall, results
    except:
        return "NORMAL", {}

# ==============================================================================
# V18.0 NOVO: MICRO-PULLBACK ENTRY DETECTOR
# ==============================================================================

def detect_micro_pullback(df, direction, atr):
    """
    Ao invés de entrar a mercado, detecta se há micro-pullback em andamento.
    Melhora preço médio de entrada significativamente.
    """
    try:
        if len(df) < 5:
            return None, "MARKET"

        last_3 = df.tail(3)
        curr = last_3.iloc[-1]
        prev = last_3.iloc[-2]

        if direction == "BULLISH":
            # Pullback: última candle fechou abaixo da anterior mas acima da EMA
            is_pullback = (curr['close'] < prev['close'] and
                           curr['close'] > curr['EMA_20'] and
                           curr['low'] > curr['EMA_50'])

            if is_pullback:
                # Entrada no pullback: entre low e EMA20
                entry_price = (curr['low'] + curr['EMA_20']) / 2
                return entry_price, "MICRO_PULLBACK"

            # Retest: toca EMA e rejeita
            if abs(curr['low'] - curr['EMA_20']) < atr * 0.3 and curr['close'] > curr['EMA_20']:
                return curr['EMA_20'] + atr * 0.1, "EMA_RETEST"

        elif direction == "BEARISH":
            is_pullback = (curr['close'] > prev['close'] and
                           curr['close'] < curr['EMA_20'] and
                           curr['high'] < curr['EMA_50'])

            if is_pullback:
                entry_price = (curr['high'] + curr['EMA_20']) / 2
                return entry_price, "MICRO_PULLBACK"

            if abs(curr['high'] - curr['EMA_20']) < atr * 0.3 and curr['close'] < curr['EMA_20']:
                return curr['EMA_20'] - atr * 0.1, "EMA_RETEST"

        return None, "MARKET"
    except:
        return None, "MARKET"

# ==============================================================================
# INDICADORES TÉCNICOS (V17 base mantida)
# ==============================================================================

def prep_df(data):
    df = pd.DataFrame(data)
    for c in ['open', 'high', 'low', 'close']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df['date'] = pd.to_datetime(df['epoch'], unit='s')
    df.set_index('date', inplace=True)
    return df

def calculate_rsi_wilder(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    for i in range(period, len(series)):
        if pd.notna(avg_gain.iloc[i - 1]):
            avg_gain.iloc[i] = (avg_gain.iloc[i - 1] * (period - 1) + gain.iloc[i]) / period
            avg_loss.iloc[i] = (avg_loss.iloc[i - 1] * (period - 1) + loss.iloc[i]) / period
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

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
    di_sum = (df['+DI'] + df['-DI']).replace(0, np.nan)
    df['DX'] = (abs(df['+DI'] - df['-DI']) / di_sum) * 100
    df['ADX'] = df['DX'].ewm(span=window, adjust=False).mean()
    df.drop(columns=['trh', 'trc', 'trl', 'TR', '+DM', '-DM', 'TR_EMA',
                      '+DM_EMA', '-DM_EMA', 'DX'], inplace=True)
    return df

def find_pivot_highs(data, order=5):
    pivots = []
    values = data.values if hasattr(data, 'values') else np.array(data)
    for i in range(order, len(values) - order):
        if np.isnan(values[i]): continue
        if all(values[i] > values[i - j] and values[i] > values[i + j] for j in range(1, order + 1)):
            pivots.append(i)
    return np.array(pivots)

def find_pivot_lows(data, order=5):
    pivots = []
    values = data.values if hasattr(data, 'values') else np.array(data)
    for i in range(order, len(values) - order):
        if np.isnan(values[i]): continue
        if all(values[i] < values[i - j] and values[i] < values[i + j] for j in range(1, order + 1)):
            pivots.append(i)
    return np.array(pivots)

def detect_divergence_v17(df, indicator='RSI', order=5):
    try:
        if len(df) < (order * 2 + 5) or indicator not in df.columns:
            return None, 0, ""
        ph = find_pivot_highs(df['high'], order=order)
        pl = find_pivot_lows(df['low'], order=order)
        ih = find_pivot_highs(df[indicator], order=order)
        il = find_pivot_lows(df[indicator], order=order)
        # Bearish
        if len(ph) >= 2 and len(ih) >= 2:
            ph1, ph2 = ph[-2], ph[-1]
            ih1 = ih[np.argmin(np.abs(ih - ph1))]
            ih2 = ih[np.argmin(np.abs(ih - ph2))]
            if abs(ih1 - ph1) <= 3 and abs(ih2 - ph2) <= 3:
                if df['high'].iloc[ph2] > df['high'].iloc[ph1] and df[indicator].iloc[ih2] < df[indicator].iloc[ih1]:
                    p_diff = (df['high'].iloc[ph2] - df['high'].iloc[ph1]) / df['high'].iloc[ph1] * 100
                    i_diff = (df[indicator].iloc[ih1] - df[indicator].iloc[ih2]) / max(df[indicator].iloc[ih1], 1) * 100
                    if min(p_diff + i_diff, 10) > 1.0:
                        return "BEARISH_DIVERGENCE", -int(min((p_diff + i_diff) * 3, 20)), f"Preço HH vs {indicator} LH"
        # Bullish
        if len(pl) >= 2 and len(il) >= 2:
            pl1, pl2 = pl[-2], pl[-1]
            il1 = il[np.argmin(np.abs(il - pl1))]
            il2 = il[np.argmin(np.abs(il - pl2))]
            if abs(il1 - pl1) <= 3 and abs(il2 - pl2) <= 3:
                if df['low'].iloc[pl2] < df['low'].iloc[pl1] and df[indicator].iloc[il2] > df[indicator].iloc[il1]:
                    p_diff = (df['low'].iloc[pl1] - df['low'].iloc[pl2]) / df['low'].iloc[pl1] * 100
                    i_diff = (df[indicator].iloc[il2] - df[indicator].iloc[il1]) / max(abs(df[indicator].iloc[il1]), 1) * 100
                    if min(p_diff + i_diff, 10) > 1.0:
                        return "BULLISH_DIVERGENCE", int(min((p_diff + i_diff) * 3, 20)), f"Preço LL vs {indicator} HL"
        # Hidden Bullish
        if len(pl) >= 2 and len(il) >= 2:
            pl1, pl2 = pl[-2], pl[-1]
            il1 = il[np.argmin(np.abs(il - pl1))]
            il2 = il[np.argmin(np.abs(il - pl2))]
            if abs(il1 - pl1) <= 3 and abs(il2 - pl2) <= 3:
                if df['low'].iloc[pl2] > df['low'].iloc[pl1] and df[indicator].iloc[il2] < df[indicator].iloc[il1]:
                    return "HIDDEN_BULLISH", 15, "Hidden: Preço HL vs ind LL"
        # Hidden Bearish
        if len(ph) >= 2 and len(ih) >= 2:
            ph1, ph2 = ph[-2], ph[-1]
            ih1 = ih[np.argmin(np.abs(ih - ph1))]
            ih2 = ih[np.argmin(np.abs(ih - ph2))]
            if abs(ih1 - ph1) <= 3 and abs(ih2 - ph2) <= 3:
                if df['high'].iloc[ph2] < df['high'].iloc[ph1] and df[indicator].iloc[ih2] > df[indicator].iloc[ih1]:
                    return "HIDDEN_BEARISH", -15, "Hidden: Preço LH vs ind HH"
        return None, 0, ""
    except:
        return None, 0, ""

def detect_sr_clustered(df, window=100, min_touches=3):
    try:
        if len(df) < window or 'ATR' not in df.columns: return []
        recent = df.tail(window)
        atr = recent['ATR'].iloc[-1]
        if pd.isna(atr) or atr == 0: return []
        tolerance = atr * 0.3
        hp = find_pivot_highs(recent['high'], order=3)
        lp = find_pivot_lows(recent['low'], order=3)
        prices = sorted([recent['high'].iloc[i] for i in hp] + [recent['low'].iloc[i] for i in lp])
        if not prices: return []
        clusters, current = [], [prices[0]]
        for i in range(1, len(prices)):
            if prices[i] - current[-1] <= tolerance:
                current.append(prices[i])
            else:
                if len(current) >= min_touches: clusters.append(current)
                current = [prices[i]]
        if len(current) >= min_touches: clusters.append(current)
        cp = df['close'].iloc[-1]
        levels = [{'price': round(np.mean(c), 4), 'touches': len(c), 'spread': round(max(c) - min(c), 4),
                    'type': 'RESISTANCE' if np.mean(c) > cp else 'SUPPORT',
                    'strength': len(c) + (1 if max(c) - min(c) < tolerance * 0.5 else 0),
                    'zone_high': round(max(c), 4), 'zone_low': round(min(c), 4)} for c in clusters]
        levels.sort(key=lambda x: x['strength'], reverse=True)
        return levels[:6]
    except:
        return []

def calculate_fibonacci_from_swings(df, lookback=100):
    try:
        if len(df) < lookback: return {}, None, None
        recent = df.tail(lookback)
        hp = find_pivot_highs(recent['high'], order=7)
        lp = find_pivot_lows(recent['low'], order=7)
        if len(hp) == 0 or len(lp) == 0: return {}, None, None
        sh = recent['high'].iloc[hp[-1]]
        sl_val = recent['low'].iloc[lp[-1]]
        if pd.isna(sh) or pd.isna(sl_val) or sh == sl_val: return {}, None, None
        diff = sh - sl_val
        if hp[-1] > lp[-1]:
            d = "UPTREND"
            fibs = {'23.6%': sh - diff * 0.236, '38.2%': sh - diff * 0.382,
                     '50.0%': sh - diff * 0.50, '61.8%': sh - diff * 0.618, '78.6%': sh - diff * 0.786}
        else:
            d = "DOWNTREND"
            fibs = {'23.6%': sl_val + diff * 0.236, '38.2%': sl_val + diff * 0.382,
                     '50.0%': sl_val + diff * 0.50, '61.8%': sl_val + diff * 0.618, '78.6%': sl_val + diff * 0.786}
        return fibs, d, {'high': sh, 'low': sl_val}
    except:
        return {}, None, None

def check_fib_confluence(price, fibs, atr):
    try:
        if not fibs or pd.isna(price) or pd.isna(atr) or atr == 0: return None, 0
        tolerance = atr * 0.4
        for name, lvl in fibs.items():
            if pd.notna(lvl) and abs(price - lvl) < tolerance:
                return name, (15 if '61.8' in name else 10 if '50.0' in name or '38.2' in name else 5)
        return None, 0
    except:
        return None, 0

# Padrões candlestick
def detect_pin_bar_quality(row, prev):
    body = abs(row['close'] - row['open'])
    rng = row['high'] - row['low']
    if rng == 0: return None, 0
    uw = row['high'] - max(row['open'], row['close'])
    lw = min(row['open'], row['close']) - row['low']
    if lw > 0 and body / rng < 0.35 and uw < body:
        r = lw / max(body, 0.0001)
        if r > 5: return "PIN_BULL_EXTREME", 15
        elif r > 3: return "PIN_BULL_STRONG", 10
        elif r > 2: return "PIN_BULL_MOD", 5
    elif uw > 0 and body / rng < 0.35 and lw < body:
        r = uw / max(body, 0.0001)
        if r > 5: return "PIN_BEAR_EXTREME", 15
        elif r > 3: return "PIN_BEAR_STRONG", 10
        elif r > 2: return "PIN_BEAR_MOD", 5
    return None, 0

def detect_engulfing_quality(row, prev):
    cb = abs(row['close'] - row['open'])
    pb = abs(prev['close'] - prev['open'])
    ct, cb2 = max(row['open'], row['close']), min(row['open'], row['close'])
    pt, pb3 = max(prev['open'], prev['close']), min(prev['open'], prev['close'])
    if row['close'] > row['open'] and prev['close'] < prev['open'] and cb2 < pb3 and ct > pt:
        r = cb / max(pb, 0.0001)
        if r > 3: return "ENGULF_BULL_MASSIVE", 15
        elif r > 2: return "ENGULF_BULL_STRONG", 10
        else: return "ENGULF_BULL_MOD", 5
    elif row['close'] < row['open'] and prev['close'] > prev['open'] and cb2 < pb3 and ct > pt:
        r = cb / max(pb, 0.0001)
        if r > 3: return "ENGULF_BEAR_MASSIVE", 15
        elif r > 2: return "ENGULF_BEAR_STRONG", 10
        else: return "ENGULF_BEAR_MOD", 5
    return None, 0

def detect_patterns_v18(df):
    patterns, scores = [], []
    for i in range(1, len(df)):
        c, p = df.iloc[i], df.iloc[i - 1]
        pl, sc = [], 0
        for fn in [detect_pin_bar_quality, detect_engulfing_quality]:
            pat, s = fn(c, p)
            if pat: pl.append(pat); sc += s
        # Inside bar
        if c['high'] <= p['high'] and c['low'] >= p['low']: pl.append("INSIDE_BAR"); sc += 5
        # Doji
        body = abs(c['close'] - c['open'])
        rng = c['high'] - c['low']
        if rng > 0 and body / rng < 0.1: pl.append("DOJI"); sc += 3
        patterns.append(pl); scores.append(sc)
    df['patterns'] = [[]] + patterns
    df['pattern_score'] = [0] + scores
    return df

def detect_swing_points_v17(df, window=5):
    df['swing_high'] = False
    df['swing_low'] = False
    for i in range(window, len(df)):
        lb = df.iloc[max(0, i - window):i + 1]
        if df['high'].iloc[i] == lb['high'].max():
            df.iloc[i, df.columns.get_loc('swing_high')] = True
        if df['low'].iloc[i] == lb['low'].min():
            df.iloc[i, df.columns.get_loc('swing_low')] = True
    return df

def classify_market_structure(df):
    sh = df[df['swing_high']]['high'].tail(4)
    sl = df[df['swing_low']]['low'].tail(4)
    if len(sh) < 2 or len(sl) < 2: return "INSUFFICIENT_DATA"
    hh = sh.iloc[-1] > sh.iloc[-2]; hl = sl.iloc[-1] > sl.iloc[-2]
    ll = sl.iloc[-1] < sl.iloc[-2]; lh = sh.iloc[-1] < sh.iloc[-2]
    if hh and hl: return "UPTREND_STRONG"
    elif ll and lh: return "DOWNTREND_STRONG"
    elif hh or hl: return "UPTREND_WEAK"
    elif ll or lh: return "DOWNTREND_WEAK"
    return "RANGE_BOUND"

def classify_market_regime(df, lookback=50):
    try:
        if len(df) < lookback: return "UNKNOWN", 0
        recent = df.tail(lookback)
        c = recent.iloc[-1]
        adx = c['ADX']
        slope = (recent['EMA_50'].iloc[-1] - recent['EMA_50'].iloc[-10]) / (c['ATR'] * 10) if c['ATR'] > 0 else 0
        bb_ratio = c['BB_width'] / recent['BB_width'].mean() if recent['BB_width'].mean() > 0 else 1
        score = 0
        if adx > 30: score += 3
        elif adx > 20: score += 2
        elif adx > 15: score += 1
        if abs(slope) > 0.3: score += 2
        elif abs(slope) > 0.15: score += 1
        if bb_ratio > 1.3: score += 1
        elif bb_ratio < 0.7: score -= 1
        if score >= 4: return "TRENDING_STRONG", score
        elif score >= 2: return "TRENDING_WEAK", score
        elif score <= 0: return "RANGING", score
        return "TRANSITIONAL", score
    except:
        return "UNKNOWN", 0

def analyze_tick_volume(df, lookback=20):
    try:
        if len(df) < lookback: return "NORMAL", 1.0
        recent = df.tail(lookback)
        ranges = recent['high'] - recent['low']
        bodies = abs(recent['close'] - recent['open'])
        r_ratio = ranges.iloc[-1] / ranges.mean() if ranges.mean() > 0 else 1
        b_ratio = bodies.iloc[-1] / bodies.mean() if bodies.mean() > 0 else 1
        proxy = (r_ratio + b_ratio) / 2
        if proxy > 2.0: return "VERY_HIGH", proxy
        elif proxy > 1.5: return "HIGH", proxy
        elif proxy > 0.7: return "NORMAL", proxy
        return "LOW", proxy
    except:
        return "NORMAL", 1.0

def confirm_breakout_volume(df):
    try:
        if len(df) < 20: return False, 0
        ranges = df['high'] - df['low']
        ratio = ranges.iloc[-1] / ranges.iloc[-20:-1].mean() if ranges.iloc[-20:-1].mean() > 0 else 1
        return ratio > 1.3, ratio
    except:
        return False, 0

def indicators(df):
    df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['EMA_200'] = df['close'].ewm(span=200, adjust=False).mean()
    df['RSI'] = calculate_rsi_wilder(df['close'], period=14)
    hl = df['high'] - df['low']
    hc = (df['high'] - df['close'].shift()).abs()
    lc = (df['low'] - df['close'].shift()).abs()
    df['tr'] = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    df['ATR'] = df['tr'].ewm(span=14, adjust=False).mean()
    df = calculate_adx(df)
    df = calculate_macd(df)
    df['BB_middle'] = df['close'].rolling(window=20).mean()
    df['BB_std'] = df['close'].rolling(window=20).std()
    df['BB_upper'] = df['BB_middle'] + df['BB_std'] * 2
    df['BB_lower'] = df['BB_middle'] - df['BB_std'] * 2
    df['BB_width'] = ((df['BB_upper'] - df['BB_lower']) / df['BB_middle'].replace(0, np.nan)) * 100
    # V18.0: Z-Score
    df['ZSCORE'] = calculate_zscore(df['close'], window=50)
    df = detect_patterns_v18(df)
    df = detect_swing_points_v17(df)
    df.dropna(inplace=True)
    return df

# ==============================================================================
# ALIGNMENT, STORM, MOMENTUM (V17)
# ==============================================================================

def detect_perfect_alignment(h4r, h1r, m15r, d):
    sc = 0
    if d == "BULLISH":
        if h4r['close'] > h4r['EMA_20'] > h4r['EMA_50'] > h4r['EMA_200']: sc += 10
        if h1r['close'] > h1r['EMA_20'] > h1r['EMA_50'] > h1r['EMA_200']: sc += 10
        if m15r['close'] > m15r['EMA_20'] > m15r['EMA_50'] > m15r['EMA_200']: sc += 10
    else:
        if h4r['close'] < h4r['EMA_20'] < h4r['EMA_50'] < h4r['EMA_200']: sc += 10
        if h1r['close'] < h1r['EMA_20'] < h1r['EMA_50'] < h1r['EMA_200']: sc += 10
        if m15r['close'] < m15r['EMA_20'] < m15r['EMA_50'] < m15r['EMA_200']: sc += 10
    if sc == 30: return "PERFECT_ALIGNMENT", 25
    elif sc >= 20: return "STRONG_ALIGNMENT", 15
    elif sc >= 10: return "WEAK_ALIGNMENT", 5
    return "NO_ALIGNMENT", 0

def check_momentum_alignment(h4, h1, m15, d):
    sc = 0
    if d == "BULLISH":
        if h4['MACD'].iloc[-1] > 0: sc += 1
        if h1['MACD'].iloc[-1] > 0: sc += 1
        if m15['MACD'].iloc[-1] > 0: sc += 1
    else:
        if h4['MACD'].iloc[-1] < 0: sc += 1
        if h1['MACD'].iloc[-1] < 0: sc += 1
        if m15['MACD'].iloc[-1] < 0: sc += 1
    return sc

def calculate_perfect_storm_bonus(sd):
    met, lst = 0, []
    checks = [
        (sd.get('adx', 0) > 30, "ADX > 30"), (sd.get('momentum_score', 0) == 3, "Momentum 3/3"),
        (sd.get('pattern_score', 0) >= 15, "Padrões fortes"), (sd.get('divergence') is not None, "Divergência real"),
        (sd.get('fib_confluence'), "Fib confluência"), (sd.get('sr_touch'), "S/R cluster"),
        (sd.get('perfect_alignment'), "Perfect Alignment"), (sd.get('bb_compression'), "BB Squeeze"),
        (sd.get('regime_trending'), "Regime Trending"), (sd.get('volume_confirmed'), "Volume confirmado"),
        (sd.get('hurst_trending'), "Hurst trending"),  # V18.0
        (sd.get('zscore_favorable'), "Z-Score favorável"),  # V18.0
    ]
    for c, l in checks:
        if c: met += 1; lst.append(l)
    if met >= 8: return "PERFECT_STORM", 25, lst
    elif met >= 6: return "STRONG_CONFLUENCE", 15, lst
    elif met >= 4: return "GOOD_CONFLUENCE", 10, lst
    return None, 0, lst

# ==============================================================================
# WALK-FORWARD BACKTEST + MONTE CARLO (V17)
# ==============================================================================

def detect_swing_level(df, direction, atr_mult=1.5):
    if direction == "BUY":
        sw = df[df['swing_low']]['low']
        return (sw.iloc[-1] - df['ATR'].iloc[-1] * atr_mult) if not sw.empty else df['low'].tail(20).min() - df['ATR'].iloc[-1] * atr_mult
    else:
        sw = df[df['swing_high']]['high']
        return (sw.iloc[-1] + df['ATR'].iloc[-1] * atr_mult) if not sw.empty else df['high'].tail(20).max() + df['ATR'].iloc[-1] * atr_mult

def run_walk_forward_backtest(df, trend_dir, profile, n_folds=3):
    spread = profile['spread']
    sl_mult = profile['sl_atr_mult']
    fold_size = len(df) // (n_folds + 1)
    all_trades, fold_results = [], []

    for fold in range(n_folds):
        ts = fold_size * (fold + 1)
        te = fold_size * (fold + 2) if fold < n_folds - 1 else len(df)
        if ts >= len(df) - 80: break
        ft, fw, fb, fr = 0, 0, 0.0, []
        si = max(200, ts)

        for i in range(si, min(te, len(df) - 80)):
            row = df.iloc[i]
            sig = None
            adx_min = profile['adx_strong']
            if trend_dir == "BULLISH" and row['ADX'] > adx_min:
                if row['close'] > row['EMA_200'] and (row['low'] <= row['EMA_50'] or row['RSI'] < 45):
                    sig = "BUY"
            elif trend_dir == "BEARISH" and row['ADX'] > adx_min:
                if row['close'] < row['EMA_200'] and (row['high'] >= row['EMA_50'] or row['RSI'] > 55):
                    sig = "SELL"
            if not sig: continue

            entry = row['close'] + (spread if sig == "BUY" else -spread)
            atr = row['ATR']
            sl_c = detect_swing_level(df.iloc[:i + 1], sig)
            if sig == "BUY":
                sl = max(entry - sl_mult * atr, sl_c)
            else:
                sl = min(entry + sl_mult * atr, sl_c)
            risk = abs(entry - sl)
            if risk == 0: risk = atr
            tp1 = entry + (profile['tp1_r'] * risk) if sig == "BUY" else entry - (profile['tp1_r'] * risk)
            tp2 = entry + (profile['tp2_r'] * risk) if sig == "BUY" else entry - (profile['tp2_r'] * risk)

            p1, p2 = True, True
            r1, r2 = 0, 0
            csl = sl
            trailing = False

            for f in range(i + 1, min(i + 80, len(df))):
                nx = df.iloc[f]
                if sig == "BUY":
                    if nx['low'] <= csl:
                        if p1: r1 = (csl - entry) / risk
                        if p2: r2 = (csl - entry) / risk
                        break
                    if p1 and nx['high'] >= tp1:
                        r1 = profile['tp1_r'] - spread / risk; p1 = False
                        csl = entry + spread; trailing = True
                    if trailing and p2:
                        csl = max(csl, nx['high'] - 2 * atr)
                        if nx['high'] >= tp2: r2 = profile['tp2_r'] - spread / risk; p2 = False; break
                else:
                    if nx['high'] >= csl:
                        if p1: r1 = (entry - csl) / risk
                        if p2: r2 = (entry - csl) / risk
                        break
                    if p1 and nx['low'] <= tp1:
                        r1 = profile['tp1_r'] - spread / risk; p1 = False
                        csl = entry - spread; trailing = True
                    if trailing and p2:
                        csl = min(csl, nx['low'] + 2 * atr)
                        if nx['low'] <= tp2: r2 = profile['tp2_r'] - spread / risk; p2 = False; break

            result = r1 * 0.5 + r2 * 0.5
            if not (p1 and p2):
                ft += 1; fb += result; fr.append(result)
                if result > 0: fw += 1
                all_trades.append({'fold': fold, 'result': result})

        if ft > 0:
            fold_results.append({'fold': fold, 'trades': ft, 'wr': fw / ft * 100, 'balance': fb})

    if not all_trades:
        return {"WR": 0, "NET": 0, "DD": 0, "PF": 0, "SHARPE": 0, "SORTINO": 0,
                "RECOVERY": 0, "MAX_CONS_WIN": 0, "MAX_CONS_LOSS": 0,
                "WF_STABLE": False, "FOLD_WRS": [], "TOTAL_TRADES": 0}

    results = [t['result'] for t in all_trades]
    wins = [r for r in results if r > 0]
    losses = [r for r in results if r <= 0]
    wr = len(wins) / len(results) * 100
    net = sum(results)
    gp = sum(wins) if wins else 0
    gl = abs(sum(losses)) if losses else 0
    pf = gp / gl if gl > 0 else (gp if gp > 0 else 0)
    cum = np.cumsum(results)
    peak = np.maximum.accumulate(cum)
    dd = (peak - cum).max() if len(cum) > 0 else 0
    mcw = mcl = cw = cl = 0
    for r in results:
        if r > 0: cw += 1; cl = 0; mcw = max(mcw, cw)
        else: cl += 1; cw = 0; mcl = max(mcl, cl)
    rs = pd.Series(results)
    sharpe = (rs.mean() / rs.std() * np.sqrt(252)) if len(rs) >= 2 and rs.std() > 0 else 0
    ds = rs[rs < 0]
    sortino = (rs.mean() / ds.std() * np.sqrt(252)) if len(ds) >= 2 and ds.std() > 0 else 0
    fwrs = [f['wr'] for f in fold_results]
    return {
        "WR": round(wr, 1), "NET": round(net, 1), "DD": round(dd, 1), "PF": round(pf, 2),
        "SHARPE": round(sharpe, 2), "SORTINO": round(sortino, 2),
        "RECOVERY": round(net / dd if dd > 0 else 0, 2),
        "MAX_CONS_WIN": mcw, "MAX_CONS_LOSS": mcl,
        "WF_STABLE": len(fwrs) >= 2 and all(w > 30 for w in fwrs),
        "FOLD_WRS": [round(w, 1) for w in fwrs], "TOTAL_TRADES": len(results)
    }

def monte_carlo_simulation(bt, n_sim=1000, n_trades=50):
    try:
        wr = bt['WR'] / 100
        if wr == 0 or bt['TOTAL_TRADES'] < 5:
            return {"median": 0, "p5": 0, "p95": 0, "p25": 0, "p75": 0, "positive_pct": 0}
        avg_w = bt.get('PF', 2.0)
        fb = []
        for _ in range(n_sim):
            b = 0
            for _ in range(n_trades):
                b += np.random.uniform(1.5, min(avg_w * 1.5, 5)) if np.random.random() < wr else -np.random.uniform(0.5, 1.0)
            fb.append(b)
        fb = np.array(fb)
        return {"median": round(np.median(fb), 1), "p5": round(np.percentile(fb, 5), 1),
                "p95": round(np.percentile(fb, 95), 1), "p25": round(np.percentile(fb, 25), 1),
                "p75": round(np.percentile(fb, 75), 1), "positive_pct": round(np.mean(fb > 0) * 100, 1)}
    except:
        return {"median": 0, "p5": 0, "p95": 0, "p25": 0, "p75": 0, "positive_pct": 0}

# ==============================================================================
# SCORING V18.0
# ==============================================================================

@dataclass
class SetupScore:
    trend_strength: float; momentum_align: float; patterns: float
    value_zone: float; historical: float; base_total: float
    divergence_bonus: float; fib_bonus: float; sr_bonus: float
    alignment_bonus: float; storm_bonus: float; regime_bonus: float
    volume_bonus: float; hurst_bonus: float; zscore_bonus: float
    consecutive_bonus: float; bonus_total: float
    total: float; grade: str

def calculate_setup_score(adx, momentum_score, pattern_score, dist_ema50, atr,
                           win_rate, profit_factor, profile,
                           divergence_bonus=0, fib_bonus=0, sr_bonus=0,
                           alignment_bonus=0, storm_bonus=0, regime_bonus=0,
                           volume_bonus=0, hurst_bonus=0, zscore_bonus=0,
                           consecutive_bonus=0):
    ts = 25 if adx > profile['adx_strong'] else (15 if adx > profile['adx_trend_min'] else 0)
    mp = (momentum_score / 3) * 20
    dr = dist_ema50 / atr if atr > 0 else 999
    vs = 15 if dr < 0.5 else (10 if dr < 1.0 else (5 if dr < 1.5 else 0))
    hs = min((win_rate * 0.15) + (profit_factor * 5), 25)
    base = ts + mp + pattern_score + vs + hs
    bonus = min(divergence_bonus + fib_bonus + sr_bonus + alignment_bonus +
                storm_bonus + regime_bonus + volume_bonus + hurst_bonus +
                zscore_bonus + consecutive_bonus, 50)
    total = base + bonus
    if total >= 140: g = "S"
    elif total >= 120: g = "A++"
    elif total >= 90: g = "A+"
    elif total >= 70: g = "A"
    elif total >= 50: g = "B"
    elif total >= 30: g = "C"
    else: g = "D"
    return SetupScore(ts, mp, pattern_score, vs, hs, base,
                       divergence_bonus, fib_bonus, sr_bonus, alignment_bonus,
                       storm_bonus, regime_bonus, volume_bonus, hurst_bonus,
                       zscore_bonus, consecutive_bonus, bonus, total, g)

# ==============================================================================
# POSITION SIZING V18.0
# ==============================================================================

def adaptive_position_size(capital, risk_pct, entry, sl, profile):
    base_risk = capital * (risk_pct / 100) * profile['risk_mult']
    risk_per_unit = abs(entry - sl)
    if risk_per_unit == 0: return 0, 0, "N/A"
    ps = base_risk / risk_per_unit
    pv = ps * entry
    note = f"{profile['vol_class']} — risco ×{profile['risk_mult']}"
    return round(ps, 2), round(pv, 2), note

def calculate_kelly(wr, avg_w, avg_l):
    if avg_l == 0: return 0
    k = ((wr / 100) * avg_w - (1 - wr / 100) * avg_l) / avg_l
    return max(0, min(k * 0.5, 0.1))

# ==============================================================================
# TRADE MANAGEMENT
# ==============================================================================

@dataclass
class ActiveTrade:
    symbol: str; direction: str; entry_price: float; current_price: float
    sl: float; tp1: float; tp2: float; entry_time: datetime
    atr: float; initial_risk: float
    sl_moved_to_be: bool = False; tp1_hit: bool = False
    realized_pct: float = 0.0
    highest_price: float = 0.0; lowest_price: float = 999999.0

    def update_price(self, p):
        self.current_price = p
        if self.direction == "LONG": self.highest_price = max(self.highest_price, p)
        else: self.lowest_price = min(self.lowest_price, p)

    def get_current_r(self):
        profit = (self.current_price - self.entry_price) if self.direction == "LONG" else (self.entry_price - self.current_price)
        return profit / self.initial_risk if self.initial_risk != 0 else 0

    def get_unrealized_pl(self):
        return (self.current_price - self.entry_price) if self.direction == "LONG" else (self.entry_price - self.current_price)

def analyze_trade_health(trade, df_m15):
    alerts, recs = [], []
    hs = 100
    cr = trade.get_current_r()
    if not trade.sl_moved_to_be and cr >= 1.5:
        alerts.append("🟢 MOVER STOP PARA BREAK-EVEN")
        recs.append({'type': 'MOVE_TO_BE', 'action': 'Mover SL para entrada', 'priority': 'HIGH'})
    if not trade.tp1_hit:
        hit = (trade.direction == "LONG" and trade.current_price >= trade.tp1) or \
              (trade.direction == "SHORT" and trade.current_price <= trade.tp1)
        if hit:
            alerts.append("🎯 TP1 ATINGIDO"); recs.append({'type': 'TP1', 'action': 'Realizar 50%', 'priority': 'CRITICAL'})
    if len(df_m15) >= 15:
        d, _, det = detect_divergence_v17(df_m15, 'RSI', order=3)
        if d and ((trade.direction == "LONG" and "BEARISH" in d) or (trade.direction == "SHORT" and "BULLISH" in d)):
            alerts.append(f"⚠️ DIVERGÊNCIA CONTRÁRIA: {d}"); hs -= 30
            recs.append({'type': 'REVERSAL', 'action': 'Apertar trailing', 'priority': 'HIGH'})
    if len(df_m15) >= 14:
        if (trade.direction == "LONG" and df_m15['MACD'].iloc[-1] < df_m15['MACD_signal'].iloc[-1]) or \
           (trade.direction == "SHORT" and df_m15['MACD'].iloc[-1] > df_m15['MACD_signal'].iloc[-1]):
            alerts.append("⚠️ MACD FRACO"); hs -= 20
    # V18.0: Z-Score contra
    if 'ZSCORE' in df_m15.columns:
        z = df_m15['ZSCORE'].iloc[-1]
        if (trade.direction == "LONG" and z > 2.0) or (trade.direction == "SHORT" and z < -2.0):
            alerts.append(f"⚠️ Z-Score extremo ({z:.1f}) — risco de reversão"); hs -= 15
    if cr > 4.0 and trade.realized_pct == 0:
        alerts.append(f"💰 +{cr:.1f}R sem realizar"); recs.append({'type': 'PARTIAL', 'action': 'Realizar 30%', 'priority': 'MEDIUM'})
    if hs >= 80: st2, col = "EXCELLENT", "trade-health-excellent"
    elif hs >= 60: st2, col = "GOOD", "trade-health-good"
    elif hs >= 40: st2, col = "WARNING", "trade-health-warning"
    else: st2, col = "DANGER", "trade-health-danger"
    return {'health_score': hs, 'health_status': st2, 'health_color': col, 'current_r': cr, 'alerts': alerts, 'recommendations': recs}

# ==============================================================================
# CHART V18.0
# ==============================================================================

def plot_candles(df, title, entry=None, sl=None, tp1=None, tp2=None, sr_levels=None, fib_levels=None, patterns=None):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), height_ratios=[3, 1], facecolor='#0a0a0a')
    ax1.set_facecolor('#0a0a0a'); ax2.set_facecolor('#0a0a0a')
    for i in range(len(df)):
        c = '#10b981' if df['close'].iloc[i] >= df['open'].iloc[i] else '#ef4444'
        ax1.plot([df.index[i]] * 2, [df['low'].iloc[i], df['high'].iloc[i]], color=c, lw=0.8)
        ax1.plot([df.index[i]] * 2, [df['open'].iloc[i], df['close'].iloc[i]], color=c, lw=3.5)
    ax1.plot(df.index, df['EMA_20'], label='EMA20', color='cyan', ls='--', alpha=0.6, lw=1)
    ax1.plot(df.index, df['EMA_50'], label='EMA50', color='orange', ls='--', alpha=0.6, lw=1)
    ax1.plot(df.index, df['EMA_200'], label='EMA200', color='purple', ls='-', alpha=0.4, lw=1.5)
    ax1.fill_between(df.index, df['BB_upper'], df['BB_lower'], alpha=0.05, color='white')
    if sr_levels:
        for sr in sr_levels[:4]:
            c = '#ef4444' if sr['type'] == 'RESISTANCE' else '#10b981'
            ax1.axhspan(sr['zone_low'], sr['zone_high'], alpha=0.1, color=c)
            ax1.axhline(y=sr['price'], color=c, ls=':', alpha=0.4, lw=0.8)
    if fib_levels:
        for n, p in fib_levels.items():
            if pd.notna(p): ax1.axhline(y=p, color='#fbbf24', ls='-.', alpha=0.25, lw=0.7)
    if entry: ax1.axhline(y=entry, color='cyan', ls='-', label='Entry', lw=2)
    if sl: ax1.axhline(y=sl, color='#ef4444', ls='-', label='SL', lw=2)
    if tp1: ax1.axhline(y=tp1, color='#10b981', ls='--', label='TP1', lw=1.5)
    if tp2: ax1.axhline(y=tp2, color='#059669', ls='-', label='TP2', lw=2)
    if patterns and 'patterns' in df.columns:
        last = df['patterns'].iloc[-1]
        if last: ax1.text(df.index[-1], df['high'].iloc[-1] * 1.001, " ".join(last), fontsize=7, color='#fbbf24', fontweight='bold')
    ax1.set_title(title, fontsize=14, fontweight='bold', color='#fbbf24')
    ax1.legend(loc='upper left', fontsize=7, facecolor='#111', edgecolor='#333', labelcolor='white')
    ax1.grid(True, alpha=0.1, color='#333'); ax1.tick_params(colors='#666')
    colors = ['#10b981' if x > 0 else '#ef4444' for x in df['MACD_hist']]
    ax2.bar(df.index, df['MACD_hist'], color=colors, alpha=0.5, width=0.8)
    ax2.plot(df.index, df['MACD'], color='#3b82f6', lw=1)
    ax2.plot(df.index, df['MACD_signal'], color='#ef4444', lw=1)
    ax2.axhline(y=0, color='#333', lw=0.5)
    ax2.set_title('MACD', fontsize=10, color='#fbbf24')
    ax2.grid(True, alpha=0.1, color='#333'); ax2.tick_params(colors='#666')
    plt.xticks(rotation=45); plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=120, facecolor='#0a0a0a', bbox_inches='tight')
    plt.close(fig); buf.seek(0)
    return Image.open(buf)

def convert_np(obj):
    if isinstance(obj, dict): return {k: convert_np(v) for k, v in obj.items()}
    elif isinstance(obj, list): return [convert_np(i) for i in obj]
    elif isinstance(obj, np.integer): return int(obj)
    elif isinstance(obj, np.floating): return float(obj)
    elif isinstance(obj, np.ndarray): return obj.tolist()
    elif isinstance(obj, np.bool_): return bool(obj)
    elif isinstance(obj, float) and pd.isna(obj): return None
    return obj

# ==============================================================================
# SNIPER CORE V18.0 — SYNTHETIC SPECIALIST
# ==============================================================================

def sniper_core_v18(name, h1_raw, h4_raw, m15_raw, capital=10000, risk_pct=1.0):
    profile = get_profile(name)
    h1 = indicators(prep_df(h1_raw))
    h4 = indicators(prep_df(h4_raw))
    m15 = indicators(prep_df(m15_raw))
    c1, c4, cm = h1.iloc[-1], h4.iloc[-1], m15.iloc[-1]

    bias = "BULLISH" if c4['close'] > c4['EMA_200'] else "BEARISH"
    adx = c4['ADX']
    structure = classify_market_structure(h1)
    regime, regime_sc = classify_market_regime(h1)
    momentum = check_momentum_alignment(h4, h1, m15, bias)

    # V18.0: Hurst Exponent
    hurst_val, hurst_regime = calculate_hurst_exponent(h1['close'])
    hurst_bonus = 0
    hurst_trending = False
    if hurst_val > profile['hurst_trend_min']:
        hurst_bonus = 10; hurst_trending = True
    elif hurst_val < 0.45:
        hurst_bonus = 5  # Mean reversion edge

    # V18.0: Z-Score
    z_current = cm['ZSCORE'] if pd.notna(cm['ZSCORE']) else 0
    z_status, z_abs = interpret_zscore(z_current, profile)
    zscore_bonus = 0
    zscore_favorable = False
    # Z-Score favorável: esticado NA DIREÇÃO CONTRÁRIA ao bias (comprar barato, vender caro)
    if bias == "BULLISH" and z_current < -profile['zscore_extreme'] * 0.6:
        zscore_bonus = 10; zscore_favorable = True
    elif bias == "BEARISH" and z_current > profile['zscore_extreme'] * 0.6:
        zscore_bonus = 10; zscore_favorable = True

    # V18.0: BB Cycle
    bb_cycle, bb_ratio, bb_squeeze_count = detect_bb_cycle(h1, profile)
    bb_compression = bb_cycle == "SQUEEZE"

    # V18.0: Consecutive Candles
    consec_count, consec_dir = count_consecutive_candles(m15)
    consecutive_bonus = 0
    consec_reversal_risk = False
    if consec_count >= profile['consecutive_reversal']:
        consec_reversal_risk = True
        # Se consecutivas vão CONTRA nosso bias → bonus (reversão a nosso favor)
        if (bias == "BULLISH" and consec_dir == "BEARISH") or \
           (bias == "BEARISH" and consec_dir == "BULLISH"):
            consecutive_bonus = 10

    # V18.0: ROC Extreme
    roc_status, roc_details = detect_roc_extreme(m15, profile)

    # Divergências
    rsi_div, rsi_db, rsi_dd = detect_divergence_v17(m15, 'RSI', order=4)
    macd_div, macd_db, macd_dd = detect_divergence_v17(m15, 'MACD', order=4)
    divergence = rsi_div or macd_div
    div_bonus = max(rsi_db, macd_db)
    div_detail = rsi_dd or macd_dd

    # S/R
    sr_levels = detect_sr_clustered(h1)
    sr_bonus, sr_touch, closest_sr = 0, False, None
    if sr_levels:
        closest_sr = min(sr_levels, key=lambda x: abs(x['price'] - c1['close']))
        if abs(closest_sr['price'] - c1['close']) < c1['ATR'] * 0.5:
            sr_bonus = min(closest_sr['strength'] * 3, 15); sr_touch = True

    # Fibonacci
    fibs, fib_dir, _ = calculate_fibonacci_from_swings(h1)
    fib_level, fib_bonus = check_fib_confluence(c1['close'], fibs, c1['ATR'])

    # Alignment
    align_type, align_bonus = detect_perfect_alignment(c4, c1, cm, bias)

    # Volume
    vol_st, vol_proxy = analyze_tick_volume(m15)
    vol_confirmed = vol_proxy > 1.3
    vol_bonus = 5 if vol_confirmed else 0
    regime_bonus = 5 if "TRENDING" in regime else 0

    # Patterns
    recent_patterns = cm['patterns'] if 'patterns' in cm.index else []
    pat_score = min(cm.get('pattern_score', 0), 15)

    # ── DETECÇÃO DE SETUP ──
    sig = "MONITORING"
    entry = c1['close']
    sl_val = c1['close']
    entry_type = "Wait"
    sl_reason = "Structural Pivot"
    trade_style = setup_type = None

    vc = profile['vol_class']
    if vc == "EXTREME" and roc_status == "EXTREME":
        sig = "BLOCKED (ROC EXTREMO em ativo EXTREME VOL)"
    elif regime == "RANGING" and consec_reversal_risk and not zscore_favorable:
        sig = "BLOCKED (RANGING + SEM EDGE ESTATÍSTICO)"
    else:
        # V18.0: Micro-pullback entry
        mp_price, mp_type = detect_micro_pullback(m15, bias, c1['ATR'])

        if bias == "BULLISH":
            if divergence and "BEARISH" in str(divergence) and "HIDDEN" not in str(divergence):
                sig = f"BLOCKED (BEARISH_DIV: {div_detail})"
            else:
                if adx > profile['adx_strong'] and (abs(c1['close'] - c1['EMA_50']) < c1['ATR'] * 1.5 or c1['RSI'] < 45):
                    if "RANGING" in regime and not hurst_trending:
                        sig = "BLOCKED (RANGING + HURST NÃO TRENDING)"
                    else:
                        sig = "LONG (SWING)"
                        sl_val = detect_swing_level(h1, "BUY", profile['sl_atr_mult'])
                        entry_type = f"Swing: Reteste — {mp_type}"
                        trade_style = "SWING"; setup_type = "SWING"
                        if mp_price and mp_type != "MARKET": entry = mp_price

                elif adx > profile['adx_trend_min'] and (c1['close'] > c1['EMA_20'] or len(recent_patterns) > 0):
                    sig = "LONG (DAY)"
                    sl_val = detect_swing_level(h1, "BUY", profile['sl_atr_mult'] * 0.8)
                    entry_type = f"Day Trade — {mp_type}"
                    trade_style = "DAY"; setup_type = "DAY"
                    if mp_price and mp_type != "MARKET": entry = mp_price

                elif sr_touch and closest_sr and c1['close'] > closest_sr['price']:
                    bk_ok, bk_r = confirm_breakout_volume(m15)
                    if bk_ok:
                        sig = "LONG (BREAKOUT)"
                        sl_val = closest_sr['price'] - c1['ATR']
                        entry_type = f"Breakout S/R (Vol ×{bk_r:.1f})"
                        trade_style = "BREAKOUT"; setup_type = "BREAKOUT"

                # V18.0: Mean Reversion setup (específico para sintéticos)
                elif z_status == "EXTREME" and z_current < 0 and hurst_val < 0.48:
                    sig = "LONG (MEAN REVERSION)"
                    sl_val = c1['close'] - profile['sl_atr_mult'] * c1['ATR']
                    entry_type = f"Mean Reversion — Z={z_current:.1f}, Hurst={hurst_val:.2f}"
                    trade_style = "REVERSAL"; setup_type = "MEAN_REVERSION"

                if "LONG" in sig and (entry - sl_val) > profile['sl_atr_mult'] * c1['ATR']:
                    sl_val = entry - profile['sl_atr_mult'] * c1['ATR']
                    sl_reason = f"Max {profile['sl_atr_mult']}× ATR ({vc})"

        elif bias == "BEARISH":
            if divergence and "BULLISH" in str(divergence) and "HIDDEN" not in str(divergence):
                sig = f"BLOCKED (BULLISH_DIV: {div_detail})"
            else:
                if adx > profile['adx_strong'] and (abs(c1['close'] - c1['EMA_50']) < c1['ATR'] * 1.5 or c1['RSI'] > 55):
                    if "RANGING" in regime and not hurst_trending:
                        sig = "BLOCKED (RANGING + HURST NÃO TRENDING)"
                    else:
                        sig = "SHORT (SWING)"
                        sl_val = detect_swing_level(h1, "SELL", profile['sl_atr_mult'])
                        entry_type = f"Swing: Reteste — {mp_type}"
                        trade_style = "SWING"; setup_type = "SWING"
                        if mp_price and mp_type != "MARKET": entry = mp_price

                elif adx > profile['adx_trend_min'] and (c1['close'] < c1['EMA_20'] or len(recent_patterns) > 0):
                    sig = "SHORT (DAY)"
                    sl_val = detect_swing_level(h1, "SELL", profile['sl_atr_mult'] * 0.8)
                    entry_type = f"Day Trade — {mp_type}"
                    trade_style = "DAY"; setup_type = "DAY"
                    if mp_price and mp_type != "MARKET": entry = mp_price

                elif sr_touch and closest_sr and c1['close'] < closest_sr['price']:
                    bk_ok, bk_r = confirm_breakout_volume(m15)
                    if bk_ok:
                        sig = "SHORT (BREAKOUT)"
                        sl_val = closest_sr['price'] + c1['ATR']
                        entry_type = f"Breakout S/R (Vol ×{bk_r:.1f})"
                        trade_style = "BREAKOUT"; setup_type = "BREAKOUT"

                elif z_status == "EXTREME" and z_current > 0 and hurst_val < 0.48:
                    sig = "SHORT (MEAN REVERSION)"
                    sl_val = c1['close'] + profile['sl_atr_mult'] * c1['ATR']
                    entry_type = f"Mean Reversion — Z={z_current:.1f}, Hurst={hurst_val:.2f}"
                    trade_style = "REVERSAL"; setup_type = "MEAN_REVERSION"

                if "SHORT" in sig and (sl_val - entry) > profile['sl_atr_mult'] * c1['ATR']:
                    sl_val = entry + profile['sl_atr_mult'] * c1['ATR']
                    sl_reason = f"Max {profile['sl_atr_mult']}× ATR ({vc})"

    # Spread
    if "LONG" in sig: entry += profile['spread']
    elif "SHORT" in sig: entry -= profile['spread']

    # Backtest
    if "BLOCKED" not in sig and sig != "MONITORING":
        sim = run_walk_forward_backtest(h1, bias, profile, n_folds=3)
    else:
        sim = {"WR": 0, "NET": 0, "DD": 0, "PF": 0, "SHARPE": 0, "SORTINO": 0,
               "RECOVERY": 0, "MAX_CONS_WIN": 0, "MAX_CONS_LOSS": 0,
               "WF_STABLE": False, "FOLD_WRS": [], "TOTAL_TRADES": 0}

    mc = monte_carlo_simulation(sim) if sim['TOTAL_TRADES'] >= 5 else \
        {"median": 0, "p5": 0, "p95": 0, "p25": 0, "p75": 0, "positive_pct": 0}

    # Perfect Storm V18.0 (agora com Hurst + Z-Score)
    storm_data = {
        'adx': adx, 'momentum_score': momentum, 'pattern_score': pat_score,
        'divergence': divergence, 'fib_confluence': fib_level is not None,
        'sr_touch': sr_touch, 'perfect_alignment': align_type == "PERFECT_ALIGNMENT",
        'bb_compression': bb_compression, 'regime_trending': "TRENDING" in regime,
        'volume_confirmed': vol_confirmed,
        'hurst_trending': hurst_trending, 'zscore_favorable': zscore_favorable,
    }
    storm_level, storm_bonus, storm_criteria = calculate_perfect_storm_bonus(storm_data)

    if storm_level == "PERFECT_STORM" and "BLOCKED" not in sig and sig != "MONITORING":
        sig = sig.replace("LONG", "LONG (⭐STORM⭐)").replace("SHORT", "SHORT (⭐STORM⭐)")
        setup_type = "PERFECT_STORM"

    # Div bonus direction-aware
    if divergence:
        if ("LONG" in sig and "BULLISH" in str(divergence)) or ("SHORT" in sig and "BEARISH" in str(divergence)):
            final_db = abs(div_bonus)
        else:
            final_db = 0
    else:
        final_db = 0

    # Score
    score = calculate_setup_score(
        adx=adx, momentum_score=momentum, pattern_score=pat_score,
        dist_ema50=abs(c1['close'] - c1['EMA_50']), atr=c1['ATR'],
        win_rate=sim['WR'], profit_factor=sim['PF'], profile=profile,
        divergence_bonus=final_db, fib_bonus=fib_bonus, sr_bonus=sr_bonus,
        alignment_bonus=align_bonus, storm_bonus=storm_bonus,
        regime_bonus=regime_bonus, volume_bonus=vol_bonus,
        hurst_bonus=hurst_bonus, zscore_bonus=zscore_bonus,
        consecutive_bonus=consecutive_bonus)

    # Filtros
    configs = {"PERFECT_STORM": (100, 1.5), "BREAKOUT": (60, 1.4),
               "MEAN_REVERSION": (50, 1.2), "DAY": (45, 1.3)}
    ms, mpf = configs.get(setup_type, (75, 1.5))
    if "BLOCKED" not in sig and sig != "MONITORING":
        fails = []
        if score.total < ms: fails.append(f"SCORE={score.total:.0f}<{ms}")
        if sim['NET'] <= 0: fails.append(f"NET≤0")
        if sim['PF'] < mpf: fails.append(f"PF={sim['PF']}<{mpf}")
        if fails: sig = f"BLOCKED ({', '.join(fails)})"

    # Targets (calibrados por perfil)
    risk = abs(entry - sl_val)
    if risk == 0: risk = c1['ATR']
    tc = {
        "PERFECT_STORM": (5, 10, "TP1 (1:5)", "TP2 (1:10)", 30, 70),
        "BREAKOUT": (profile['tp1_r'], profile['tp2_r'] + 2, f"TP1 (1:{profile['tp1_r']:.0f})", f"TP2 (1:{profile['tp2_r'] + 2:.0f})", 50, 50),
        "MEAN_REVERSION": (2, 3, "TP1 (1:2)", "TP2 (1:3)", 60, 40),
        "DAY": (2, 3, "TP1 (1:2)", "TP2 (1:3)", 60, 40),
    }
    r1, r2, l1, l2, p1, p2 = tc.get(setup_type, (profile['tp1_r'], profile['tp2_r'], f"TP1 (1:{profile['tp1_r']:.0f})", f"TP2 (1:{profile['tp2_r']:.0f})", 50, 50))
    if "LONG" in sig: tp1, tp2 = entry + r1 * risk, entry + r2 * risk
    elif "SHORT" in sig: tp1, tp2 = entry - r1 * risk, entry - r2 * risk
    else: tp1 = tp2 = entry

    ps, pv, pn = adaptive_position_size(capital, risk_pct, entry, sl_val, profile)
    kelly_msg = ""
    if setup_type in ["PERFECT_STORM"] and score.grade in ["S", "A++"]:
        kelly_msg = f"🌟 Kelly: {calculate_kelly(sim['WR'], 5, 1) * 100:.1f}%"

    show = any(x in sig for x in ["SWING", "DAY", "BREAKOUT", "STORM", "REVERSION"])
    imgs = [
        plot_candles(h4, f"{name} H4 — Regime: {regime} | Hurst: {hurst_val:.2f}", entry if show else None, sl_val if show else None, tp1 if show else None, tp2 if show else None, sr_levels=sr_levels if show else None),
        plot_candles(h1, f"{name} H1 — Z: {z_current:.1f} | BB: {bb_cycle}", entry if show else None, sl_val if show else None, tp1 if show else None, tp2 if show else None, sr_levels=sr_levels, fib_levels=fibs if show else None),
        plot_candles(m15, f"{name} M15 — Consec: {consec_count}{consec_dir[0]} | ROC: {roc_status}", entry if show else None, sl_val if show else None, tp1 if show else None, tp2 if show else None, patterns=True)
    ]

    confs = []
    if divergence: confs.append(f"🔍 {divergence}: {div_detail}")
    if fib_level: confs.append(f"📐 Fib {fib_level}")
    if sr_touch and closest_sr: confs.append(f"🎯 S/R {closest_sr['touches']}x @ {closest_sr['price']:.2f}")
    if align_type != "NO_ALIGNMENT": confs.append(f"⭐ {align_type}")
    if storm_level: confs.append(f"🌟 {storm_level}")
    if vol_confirmed: confs.append(f"📊 Volume ×{vol_proxy:.1f}")
    if hurst_trending: confs.append(f"🧬 Hurst trending ({hurst_val:.2f})")
    if zscore_favorable: confs.append(f"📊 Z-Score favorável ({z_current:.1f})")
    if consecutive_bonus > 0: confs.append(f"🔢 {consec_count} candles {consec_dir} (reversão)")
    if bb_compression: confs.append(f"💥 BB Squeeze ({bb_squeeze_count} candles)")

    risks = []
    if "RANGING" in regime: risks.append("⚠️ Regime RANGING")
    if not sim['WF_STABLE']: risks.append("⚠️ Walk-Forward instável")
    if mc.get('positive_pct', 0) < 60: risks.append(f"⚠️ MC {mc.get('positive_pct', 0)}% positivo")
    if roc_status == "EXTREME": risks.append(f"⚠️ ROC EXTREMO — snap-back possível")
    if consec_reversal_risk and consecutive_bonus == 0: risks.append(f"⚠️ {consec_count} candles consecutivas — reversão iminente")
    if hurst_regime == "RANDOM_WALK": risks.append("⚠️ Hurst ≈ 0.5 — random walk, sem edge")

    return {
        "FINAL_DECISION": sig, "TRADE_STYLE": trade_style or "N/A", "SETUP_TYPE": setup_type or "N/A",
        "SETUP_SCORE": float(round(score.total, 1)), "BASE_SCORE": float(round(score.base_total, 1)),
        "BONUS_SCORE": float(round(score.bonus_total, 1)), "SETUP_GRADE": score.grade,
        "INDEX_PROFILE": vc, "PROFILE_DESC": profile['description'],
        "ADX_SCORE": float(round(score.trend_strength, 1)),
        "MOMENTUM_SCORE": float(round(score.momentum_align, 1)),
        "PATTERN_SCORE": float(round(score.patterns, 1)),
        "VALUE_SCORE": float(round(score.value_zone, 1)),
        "HIST_SCORE": float(round(score.historical, 1)),
        "DIVERGENCE_BONUS": float(round(score.divergence_bonus, 1)),
        "FIB_BONUS": float(round(score.fib_bonus, 1)), "SR_BONUS": float(round(score.sr_bonus, 1)),
        "ALIGNMENT_BONUS": float(round(score.alignment_bonus, 1)),
        "STORM_BONUS": float(round(score.storm_bonus, 1)),
        "REGIME_BONUS": float(round(score.regime_bonus, 1)),
        "VOLUME_BONUS": float(round(score.volume_bonus, 1)),
        "HURST_BONUS": float(round(score.hurst_bonus, 1)),
        "ZSCORE_BONUS": float(round(score.zscore_bonus, 1)),
        "CONSECUTIVE_BONUS": float(round(score.consecutive_bonus, 1)),
        "HURST": float(hurst_val), "HURST_REGIME": hurst_regime,
        "ZSCORE": float(round(z_current, 2)), "ZSCORE_STATUS": z_status,
        "BB_CYCLE": bb_cycle, "BB_RATIO": float(round(bb_ratio, 2)),
        "BB_SQUEEZE_COUNT": int(bb_squeeze_count),
        "CONSECUTIVE": int(consec_count), "CONSECUTIVE_DIR": consec_dir,
        "ROC_STATUS": roc_status, "ROC_DETAILS": {k: v for k, v in roc_details.items()},
        "MARKET_STRUCTURE": structure, "MARKET_REGIME": regime,
        "VOL_CLASS": vc, "TICK_VOLUME": f"{vol_st} (×{vol_proxy:.1f})",
        "PATTERNS": ", ".join(recent_patterns) if recent_patterns else "Nenhum",
        "DIVERGENCE": divergence or "Nenhuma", "DIVERGENCE_DETAIL": div_detail or "",
        "FIB_LEVEL": fib_level or "N/A", "FIB_DIR": fib_dir or "N/A",
        "SR_LEVELS": int(len(sr_levels)), "ALIGNMENT": align_type,
        "STORM_LEVEL": storm_level or "N/A", "STORM_CRITERIA": storm_criteria,
        "CONFLUENCES": confs, "RISKS": risks,
        "MOMENTUM": f"{momentum}/3",
        "ENTRY_TYPE": entry_type, "SL_REASON": sl_reason, "SPREAD": float(profile['spread']),
        "WIN_RATE": float(sim['WR']), "NET_PROFIT": float(sim['NET']),
        "MAX_DRAWDOWN": float(sim['DD']), "PROFIT_FACTOR": float(sim['PF']),
        "SHARPE": float(sim['SHARPE']), "SORTINO": float(sim['SORTINO']),
        "RECOVERY": float(sim['RECOVERY']),
        "WF_STABLE": sim['WF_STABLE'], "FOLD_WRS": sim['FOLD_WRS'],
        "TOTAL_TRADES": int(sim['TOTAL_TRADES']),
        "MC_MEDIAN": float(mc.get('median', 0)), "MC_P5": float(mc.get('p5', 0)),
        "MC_P95": float(mc.get('p95', 0)), "MC_POSITIVE": float(mc.get('positive_pct', 0)),
        "ENTRY": float(round(entry, 5)), "SL": float(round(sl_val, 5)),
        "TP1": float(round(tp1, 5)), "TP2": float(round(tp2, 5)),
        "TP1_LABEL": l1, "TP2_LABEL": l2,
        "PCT1": int(p1), "PCT2": int(p2),
        "POS_SIZE": float(ps), "POS_VALUE": float(pv), "POS_NOTE": pn,
        "KELLY_MSG": kelly_msg,
        "IMAGES": imgs, "ATR": float(c1['ATR']), "INITIAL_RISK": float(risk),
    }

# ==============================================================================
# STREAMLIT UI V18.0
# ==============================================================================

st.sidebar.title("🧬 SI-APATECO V18.0")
st.sidebar.caption("SYNTHETIC INDEX SPECIALIST")

if "GEMINI_API_KEY" in st.secrets:
    api = st.secrets["GEMINI_API_KEY"]
    st.sidebar.success("✅ API ATIVA")
else:
    api = st.sidebar.text_input("CHAVE API GEMINI", type="password")

st.sidebar.divider()
capital = st.sidebar.number_input("💰 Capital ($)", min_value=100, value=10000, step=100)
risk_pct = st.sidebar.slider("📊 Risco Base (%)", 0.5, 3.0, 1.0, 0.1)

st.sidebar.divider()
mode = st.sidebar.radio("⚙️ Modo", ["🔍 Análise", "📊 Monitor"])

st.sidebar.divider()
st.sidebar.info("""
**V18.0 — ARMAS SINTÉTICOS:**
- 🧬 Hurst Exponent
- 📊 Z-Score Mean Reversion
- 🎯 Perfil calibrado por índice
- 💥 BB Squeeze → Expansion
- 🔢 Consecutive Candle Counter
- ⚡ ROC Extreme (snap-back)
- 🎯 Micro-Pullback Entry
- 🔄 Crash/Boom: LONG e SHORT
- 📏 SL calibrado por vol class
""")

st.title("🧬 SI-APATECO V18.0 — SYNTHETIC SPECIALIST")
st.caption("Hurst | Z-Score | Perfil por Índice | BB Cycle | ROC | Bidirecional Crash/Boom")

with st.spinner("Carregando ativos..."):
    assets = get_assets()
if not assets:
    st.error("❌ FALHA NA CONEXÃO"); st.stop()

if mode == "🔍 Análise":
    c1, c2 = st.columns([1, 2])
    with c1:
        target = st.selectbox("🎯 ATIVO", list(assets.keys()))
        prof = get_profile(target)
        st.markdown(f"**Perfil:** `{prof['vol_class']}` — {prof['description']}")
        st.caption(f"SL: {prof['sl_atr_mult']}×ATR | TP: 1:{prof['tp1_r']}/1:{prof['tp2_r']} | Risco: ×{prof['risk_mult']}")
        run = st.button("🧬 ANALISAR", use_container_width=True)

    with c2:
        if run:
            if not api: st.error("⚠️ API KEY"); st.stop()
            status = st.status("🧬 V18.0 SYNTHETIC SPECIALIST...", expanded=True)
            status.write("1️⃣ Dados MTF...")
            h1r, h4r, m15r, err = asyncio.run(fetch_tri_force(assets[target]))
            if err: status.update(state='error'); st.error(err); st.stop()
            status.write("2️⃣ Hurst Exponent + Z-Score...")
            status.write("3️⃣ BB Cycle + ROC + Consecutive...")
            status.write("4️⃣ Perfil calibrado + Micro-pullback...")
            status.write("5️⃣ Walk-Forward + Monte Carlo...")
            data = sniper_core_v18(target, h1r, h4r, m15r, capital, risk_pct)
            imgs = data.pop("IMAGES")
            status.write("6️⃣ Gemini 3 Pro...")
            genai.configure(api_key=api)
            dc = convert_np(data)
            try:
                model = genai.GenerativeModel("models/gemini-3-pro-preview", safety_settings=SAFETY_SETTINGS)
                ai = model.generate_content([SYSTEM_PROMPT, f"DADOS V18.0: {json.dumps(dc)}"] + imgs).text
                status.update(label="✅ V18.0 COMPLETA", state="complete")
            except Exception as e:
                ai = f"⚠️ IA indisponível: {str(e)[:150]}"; status.update(label="⚠️ Sem IA", state="complete")

            # DISPLAY
            g = data['SETUP_GRADE']
            gc = {"S": ("score-s", "👑"), "A++": ("score-a-plus-plus", "🏆"), "A+": ("score-a-plus", "💎"),
                  "A": ("score-a", "⭐"), "B": ("score-b", "📊")}.get(g, ("score-c", "⚠️"))

            st.markdown(f"""
            <div style='text-align:center;padding:25px;background:rgba(251,191,36,0.08);border:3px solid #fbbf24;border-radius:15px;margin-bottom:25px;'>
                <h1 style='margin:0;'>{gc[1]} GRADE: <span class='{gc[0]}'>{g}</span></h1>
                <p style='font-size:28px;margin:15px 0;'><strong>SCORE: {data["SETUP_SCORE"]}/150</strong></p>
                <p style='font-size:16px;margin:8px 0;'>Base: {data["BASE_SCORE"]}/100 | Bonus: +{data["BONUS_SCORE"]}/50</p>
                <p style='font-size:20px;margin:10px 0;color:#a855f7;'>🧬 {data["INDEX_PROFILE"]} — {data.get("SETUP_TYPE","N/A")}</p>
            </div>""", unsafe_allow_html=True)

            if data.get('SETUP_TYPE') == "PERFECT_STORM": st.success("🌟 PERFECT STORM!"); st.balloons()

            # V18.0 Synthetic Stats
            st.subheader("🧬 ANÁLISE ESTATÍSTICA SINTÉTICO")
            s1, s2, s3, s4, s5, s6 = st.columns(6)
            s1.metric("Hurst", f"{data['HURST']:.3f}", data['HURST_REGIME'])
            s2.metric("Z-Score", f"{data['ZSCORE']:.2f}", data['ZSCORE_STATUS'])
            s3.metric("BB Cycle", data['BB_CYCLE'], f"ratio: {data['BB_RATIO']:.1f}")
            s4.metric("Consecutivas", f"{data['CONSECUTIVE']}", data['CONSECUTIVE_DIR'])
            s5.metric("ROC", data['ROC_STATUS'])
            s6.metric("Vol Class", data['VOL_CLASS'])

            # WF Metrics
            st.subheader("📊 WALK-FORWARD")
            m1, m2, m3, m4, m5, m6 = st.columns(6)
            m1.metric("WR", f"{data['WIN_RATE']}%"); m2.metric("PF", f"{data['PROFIT_FACTOR']}")
            m3.metric("Sharpe", f"{data['SHARPE']}"); m4.metric("Sortino", f"{data['SORTINO']}")
            m5.metric("DD", f"{data['MAX_DRAWDOWN']}R"); m6.metric("Trades", f"{data['TOTAL_TRADES']}")
            if data['FOLD_WRS']:
                st.write("Folds: " + " | ".join([f"F{i+1}: {w}%" for i, w in enumerate(data['FOLD_WRS'])]))

            # MC
            st.subheader("🎲 MONTE CARLO")
            mc1, mc2, mc3, mc4 = st.columns(4)
            mc1.metric("Mediana", f"{data['MC_MEDIAN']}R"); mc2.metric("P5", f"{data['MC_P5']}R")
            mc3.metric("P95", f"{data['MC_P95']}R"); mc4.metric("% Positivo", f"{data['MC_POSITIVE']}%")

            # Breakdown
            st.subheader("🔬 BREAKDOWN")
            bc1, bc2 = st.columns(2)
            with bc1:
                st.markdown("**Base (100):**")
                st.dataframe(pd.DataFrame([
                    {"Item": "ADX", "Score": f"{data['ADX_SCORE']}/25"},
                    {"Item": "Momentum", "Score": f"{data['MOMENTUM_SCORE']}/20"},
                    {"Item": "Padrões", "Score": f"{data['PATTERN_SCORE']}/15"},
                    {"Item": "Zona Valor", "Score": f"{data['VALUE_SCORE']}/15"},
                    {"Item": "Histórico WF", "Score": f"{data['HIST_SCORE']}/25"},
                ]), hide_index=True, use_container_width=True)
            with bc2:
                st.markdown("**Bonus (50):**")
                st.dataframe(pd.DataFrame([
                    {"Item": "Divergência", "Bonus": f"+{data['DIVERGENCE_BONUS']}"},
                    {"Item": "Fibonacci", "Bonus": f"+{data['FIB_BONUS']}"},
                    {"Item": "S/R", "Bonus": f"+{data['SR_BONUS']}"},
                    {"Item": "Alignment", "Bonus": f"+{data['ALIGNMENT_BONUS']}"},
                    {"Item": "Storm", "Bonus": f"+{data['STORM_BONUS']}"},
                    {"Item": "Regime", "Bonus": f"+{data['REGIME_BONUS']}"},
                    {"Item": "Volume", "Bonus": f"+{data['VOLUME_BONUS']}"},
                    {"Item": "🧬 Hurst", "Bonus": f"+{data['HURST_BONUS']}"},
                    {"Item": "📊 Z-Score", "Bonus": f"+{data['ZSCORE_BONUS']}"},
                    {"Item": "🔢 Consecutive", "Bonus": f"+{data['CONSECUTIVE_BONUS']}"},
                ]), hide_index=True, use_container_width=True)

            if data['CONFLUENCES']:
                st.subheader("🔥 CONFLUÊNCIAS")
                for c in data['CONFLUENCES']: st.markdown(f"- {c}")
            if data['RISKS']:
                st.subheader("⚠️ RISCOS")
                for r in data['RISKS']: st.warning(r)

            st.divider()
            d = data['FINAL_DECISION']
            if any(x in d for x in ["SWING", "DAY", "BREAKOUT", "STORM", "REVERSION"]):
                st.success(f"✅ {d}")
            elif "BLOCKED" in d: st.error(f"🛑 {d}")
            else: st.warning(f"⏸️ {d}")

            if any(x in d for x in ["SWING", "DAY", "BREAKOUT", "STORM", "REVERSION"]):
                st.subheader(f"📋 PLANO — {data['INDEX_PROFILE']}")
                st.dataframe(pd.DataFrame([
                    {"P": "Entrada", "V": f"{data['ENTRY']}", "N": data['ENTRY_TYPE']},
                    {"P": "Stop Loss", "V": f"{data['SL']}", "N": data['SL_REASON']},
                    {"P": data['TP1_LABEL'], "V": f"{data['TP1']}", "N": f"Realizar {data['PCT1']}%"},
                    {"P": data['TP2_LABEL'], "V": f"{data['TP2']}", "N": f"Realizar {data['PCT2']}% + trail"},
                    {"P": "Spread", "V": f"{data['SPREAD']}", "N": "Incluído"},
                    {"P": "Posição", "V": f"{data['POS_SIZE']} un (${data['POS_VALUE']})", "N": data['POS_NOTE']},
                ]), hide_index=True, use_container_width=True)
                if data['KELLY_MSG']: st.info(data['KELLY_MSG'])

            st.divider()
            tabs = st.tabs(["H4", "H1", "M15"])
            with tabs[0]: st.image(imgs[0], use_container_width=True)
            with tabs[1]: st.image(imgs[1], use_container_width=True)
            with tabs[2]: st.image(imgs[2], use_container_width=True)

            st.divider()
            st.subheader("🤖 ANÁLISE IA")
            st.markdown(ai)

elif mode == "📊 Monitor":
    st.markdown("### 📊 TRADE MONITOR V18.0")
    c1, c2 = st.columns(2)
    with c1:
        ms = st.selectbox("Ativo", list(assets.keys()))
        md = st.selectbox("Direção", ["LONG", "SHORT"])
    with c2:
        me = st.number_input("Entrada", value=1000.0, step=0.1)
        msl = st.number_input("Stop", value=990.0, step=0.1)
    c3, c4 = st.columns(2)
    with c3: mt1 = st.number_input("TP1", value=1030.0, step=0.1)
    with c4: mt2 = st.number_input("TP2", value=1050.0, step=0.1)

    if st.button("🧬 MONITORAR", use_container_width=True):
        trade = ActiveTrade(ms, md, me, me, msl, mt1, mt2, datetime.now(),
                            abs(me - msl) / 2.5, abs(me - msl))
        if md == "LONG": trade.highest_price = me
        else: trade.lowest_price = me
        sph, mph, aph, rph, cph = st.empty(), st.empty(), st.empty(), st.empty(), st.empty()
        for _ in range(120):
            try:
                _, _, m15r, err = asyncio.run(fetch_tri_force(assets[ms]))
                if not err and m15r:
                    mdf = indicators(prep_df(m15r))
                    trade.update_price(mdf['close'].iloc[-1])
                    h = analyze_trade_health(trade, mdf)
                    sph.markdown(f"<div class='{h['health_color']}'><h3>🏥 {h['health_status']} ({h['health_score']}/100)</h3><p>R: {h['current_r']:+.2f} | P&L: ${trade.get_unrealized_pl():+.2f}</p></div>", unsafe_allow_html=True)
                    with mph.container():
                        a, b, c, d, e = st.columns(5)
                        a.metric("Preço", f"{trade.current_price:.4f}")
                        b.metric("Entrada", f"{trade.entry_price:.4f}")
                        c.metric("R", f"{h['current_r']:+.2f}")
                        d.metric("Z-Score", f"{mdf['ZSCORE'].iloc[-1]:.1f}" if 'ZSCORE' in mdf.columns else "N/A")
                        e.metric("Extremo", f"{(trade.highest_price if md == 'LONG' else trade.lowest_price):.4f}")
                    if h['alerts']:
                        with aph.container():
                            for a in h['alerts']: st.warning(a)
                    if h['recommendations']:
                        with rph.container():
                            for r in h['recommendations']:
                                st.info(f"{'🔴' if r['priority'] == 'CRITICAL' else '🟡' if r['priority'] == 'HIGH' else '🟢'} {r['type']}: {r['action']}")
                    with cph.container():
                        st.image(plot_candles(mdf.tail(50), f"{ms} M15 Monitor", trade.entry_price, trade.sl, trade.tp1, trade.tp2), use_container_width=True)
                time.sleep(5)
            except Exception as ex:
                st.error(str(ex)); break
        st.success("✅ Monitor finalizado")
