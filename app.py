import streamlit as st
import asyncio
import websockets
import json
import time
import pandas as pd
import numpy as np
import google.generativeai as genai
from PIL import Image
import matplotlib.pyplot as plt
import io
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
from scipy.stats import norm, median_abs_deviation, chi2 as chi2_dist
from itertools import permutations as _perms
from math import factorial, log as math_log
import time
import warnings
warnings.filterwarnings('ignore')

# ==============================================================================
# SI-APATECO V24.0-BC — BOOM/CRASH PRECISION SNIPER ENGINE
#
# ⚡ V24: FULL AUDIT IMPLEMENTATION — 14 fixes + 5 HPI + 4 math + 5 arch
# ⚡ SISTEMA EXCLUSIVO BOOM & CRASH — Day Trade + Scalp
# ⚡ BUY e SELL em ambos os ativos
# ⚡ Alta precisão + Agressividade controlada
#
# ATIVOS: Boom 300/500/600/900/1000 | Crash 300/500/600/900/1000
# ESTILOS: Day Trade + Scalp APENAS (sem Swing)
#
# V24 AUDIT FIXES:
#   #1  Walk-Forward testa BC setups (DRIFT/FADE/SPIKE) — CRITICAL
#   #2  Spike timing empírico (não ticks/15) — HIGH
#   #3  Kelly Criterion correto (avg_win/avg_loss) — HIGH
#   #4  Spike probability com desconto correlação + Poisson — HIGH
#   #5  Bias dual scoring para BC — MEDIUM-HIGH
#   #6  Clean ATR mediano (exclui spikes) — MEDIUM
#   #7  Drift magnitude + contagem — MEDIUM
#   #8  Post-spike fade com validação absorção — MEDIUM
#   #9  Supply/Demand zones com decay temporal — MEDIUM
#   #10 Sharpe/Sortino com PPY correto — MEDIUM
#   #11 Score floor após cascata — MEDIUM
#   #12 Stochastic lookback paramétrico — LOW
#   #13 Multi-spike gap tolerance — LOW
#   #14 SampEn otimizado (n=200 + vectorizado) — LOW
#
# V24 HIGH PERFORMANCE IMPROVEMENTS:
#   M1  BC-Aware Backtest (30-50% precisão)
#   M2  Median ATR for BC (25% robustez)
#   M3  Calibrated Spike Probability (20% precisão)
#   M4  Returns Kurtosis Analysis (15% robustez)
#   M5  Regime-Aware SL (20% risk control)
#
# V24 MATHEMATICAL:
#   A1  Kelly com payoff ratio correto
#   A2  Sharpe com PPY auto-detectado
#   A3  Expectância explícita + stress test -20% WR
#   A4  Modelo Poisson/Weibull para spike timing
#
# V24 ARCHITECTURAL:
#   O2  Pipeline BC dedicado em try_setup
#   O3  Resolução de conflitos entre engines
#   O4  Dead code removido (GBM/STEP)
#   O5  Anti-Meltdown Kill-Switch
#
# ==============================================================================# 🟢 PRECISION #2: Trailing Stop por regime/tipo
# 🟢 PRECISION #3: Dynamic TP com S/R awareness
# 🟢 PRECISION #4: Scanner para TODOS gen types
# 🟢 PRECISION #5: Adaptive Kelly Criterion (não if/elif)
# 🟢 PRECISION #6: M5 entry timing
# ==============================================================================

st.set_page_config(
    page_title="APATECO V24-BC",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    /* ── BASE ── */
    .stApp {
        background: #09090b;
        color: #a1a1aa;
        font-family: 'Inter', -apple-system, sans-serif;
    }
    section[data-testid="stSidebar"] {
        background: #09090b;
        border-right: 1px solid #1a1a1f;
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown span {
        color: #71717a;
        font-size: 13px;
    }

    /* ── TYPOGRAPHY ── */
    h1 { font-family:'Inter',sans-serif!important; font-weight:300!important; color:#fafafa!important;
         letter-spacing:-0.5px!important; font-size:28px!important; text-transform:none!important;
         text-shadow:none!important; border:none!important; }
    h2 { font-family:'Inter',sans-serif!important; font-weight:500!important; color:#e4e4e7!important;
         font-size:16px!important; letter-spacing:0.3px!important; text-transform:uppercase!important;
         text-shadow:none!important; border:none!important; margin-top:28px!important; }
    h3 { font-family:'Inter',sans-serif!important; font-weight:500!important; color:#a1a1aa!important;
         font-size:13px!important; letter-spacing:0.5px!important; text-transform:uppercase!important;
         text-shadow:none!important; border:none!important; }
    p, li, span { font-family:'Inter',sans-serif; }

    /* ── METRICS ── */
    div[data-testid="stMetric"] {
        background: #111113;
        border: 1px solid #1e1e23;
        border-radius: 10px;
        padding: 16px 18px;
        border-right: 1px solid #1e1e23;
    }
    div[data-testid="stMetric"] label {
        color: #52525b !important;
        font-size: 11px !important;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        font-weight: 500 !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #fafafa !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 20px !important;
        font-weight: 500 !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 11px !important;
    }

    /* ── BUTTONS ── */
    .stButton > button {
        background: #fafafa;
        color: #09090b;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 13px;
        letter-spacing: 0.5px;
        padding: 12px 24px;
        border-radius: 8px;
        border: none;
        width: 100%;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background: #e4e4e7;
        box-shadow: 0 4px 20px rgba(255,255,255,0.06);
        transform: translateY(-1px);
    }

    /* ── CARDS ── */
    .card {
        background: #111113;
        border: 1px solid #1e1e23;
        border-radius: 12px;
        padding: 24px;
        margin: 8px 0;
    }
    .card-accent {
        background: linear-gradient(135deg, #111113 0%, #13131a 100%);
        border: 1px solid #27272a;
        border-radius: 14px;
        padding: 28px;
        margin: 12px 0;
    }

    /* ── GRADE BADGES ── */
    .grade-s {
        background: linear-gradient(135deg, #7c3aed20, #a855f710);
        border: 1px solid #7c3aed40;
        color: #c4b5fd;
        border-radius: 12px; padding: 24px; text-align: center;
    }
    .grade-s .grade-letter { font-size: 48px; font-weight: 700; color: #a78bfa; }
    .grade-app {
        background: linear-gradient(135deg, #05966920, #10b98110);
        border: 1px solid #10b98140;
        color: #6ee7b7;
        border-radius: 12px; padding: 24px; text-align: center;
    }
    .grade-app .grade-letter { font-size: 48px; font-weight: 700; color: #34d399; }
    .grade-ap {
        background: linear-gradient(135deg, #2563eb20, #3b82f610);
        border: 1px solid #3b82f640;
        color: #93c5fd;
        border-radius: 12px; padding: 24px; text-align: center;
    }
    .grade-ap .grade-letter { font-size: 48px; font-weight: 700; color: #60a5fa; }
    .grade-a {
        background: linear-gradient(135deg, #06b6d420, #22d3ee10);
        border: 1px solid #22d3ee30;
        color: #a5f3fc;
        border-radius: 12px; padding: 24px; text-align: center;
    }
    .grade-a .grade-letter { font-size: 48px; font-weight: 700; color: #67e8f9; }
    .grade-low {
        background: #111113;
        border: 1px solid #27272a;
        color: #71717a;
        border-radius: 12px; padding: 24px; text-align: center;
    }
    .grade-low .grade-letter { font-size: 48px; font-weight: 700; color: #52525b; }

    /* ── SCORE BAR ── */
    .score-bar-outer {
        background: #1a1a1f;
        border-radius: 6px;
        height: 8px;
        margin: 8px 0 4px;
        overflow: hidden;
    }
    .score-bar-inner {
        height: 100%;
        border-radius: 6px;
        transition: width 1s ease;
    }

    /* ── SIGNAL TAGS ── */
    .tag-long {
        display: inline-block;
        background: #05966915;
        color: #34d399;
        border: 1px solid #10b98130;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: 0.5px;
    }
    .tag-short {
        display: inline-block;
        background: #ef444415;
        color: #f87171;
        border: 1px solid #ef444430;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: 0.5px;
    }
    .tag-blocked {
        display: inline-block;
        background: #71717a10;
        color: #71717a;
        border: 1px solid #52525b30;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 500;
    }
    .tag-monitoring {
        display: inline-block;
        background: #f59e0b10;
        color: #fbbf24;
        border: 1px solid #f59e0b30;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 500;
    }

    /* ── CONFLUENCE PILLS ── */
    .pill {
        display: inline-block;
        background: #18181b;
        border: 1px solid #27272a;
        color: #a1a1aa;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 12px;
        margin: 3px 3px;
        font-weight: 400;
    }
    .pill-green { border-color: #10b98130; color: #6ee7b7; background: #10b98108; }
    .pill-red { border-color: #ef444430; color: #fca5a5; background: #ef444408; }
    .pill-purple { border-color: #7c3aed30; color: #c4b5fd; background: #7c3aed08; }
    .pill-blue { border-color: #3b82f630; color: #93c5fd; background: #3b82f608; }

    /* ── SCANNER ROWS ── */
    .scan-row {
        background: #111113;
        border: 1px solid #1e1e23;
        border-radius: 10px;
        padding: 14px 18px;
        margin: 6px 0;
        display: flex;
        align-items: center;
        justify-content: space-between;
        transition: border-color 0.2s;
    }
    .scan-row:hover { border-color: #3b82f640; }
    .scan-rank {
        color: #52525b;
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        width: 28px;
    }
    .scan-name {
        color: #fafafa;
        font-weight: 600;
        font-size: 14px;
        flex: 1;
        margin-left: 8px;
    }
    .scan-score {
        font-family: 'JetBrains Mono', monospace;
        font-size: 18px;
        font-weight: 600;
        margin: 0 16px;
    }
    .scan-meta {
        color: #52525b;
        font-size: 11px;
        font-family: 'JetBrains Mono', monospace;
    }

    /* ── TRADE PLAN TABLE ── */
    .plan-row {
        display: flex;
        align-items: center;
        padding: 12px 16px;
        border-bottom: 1px solid #1e1e23;
    }
    .plan-row:last-child { border-bottom: none; }
    .plan-label {
        color: #52525b;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        width: 80px;
        font-weight: 500;
    }
    .plan-value {
        color: #fafafa;
        font-family: 'JetBrains Mono', monospace;
        font-size: 15px;
        font-weight: 500;
        flex: 1;
    }
    .plan-note {
        color: #52525b;
        font-size: 12px;
    }

    /* ── MISC ── */
    .divider {
        height: 1px;
        background: #1e1e23;
        margin: 20px 0;
        border: none;
    }
    .mono { font-family: 'JetBrains Mono', monospace; }
    .muted { color: #52525b; }
    .text-sm { font-size: 12px; }
    .text-xs { font-size: 11px; }

    /* ── TABS ── */
    .stTabs [data-baseweb="tab-list"] { gap: 0; border-bottom: 1px solid #1e1e23; }
    .stTabs [data-baseweb="tab"] {
        background: transparent; color: #52525b; font-family:'Inter',sans-serif;
        font-weight: 500; font-size: 13px; padding: 10px 20px;
        border-bottom: 2px solid transparent;
    }
    .stTabs [aria-selected="true"] { color: #fafafa; border-bottom-color: #fafafa; background: transparent; }

    /* ── STATUS ── */
    div[data-testid="stStatusWidget"] {
        background: #111113; border: 1px solid #1e1e23; border-radius: 10px;
    }

    /* ── HIDE EXTRA ── */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
</style>
""", unsafe_allow_html=True)

SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# ==============================================================================
# PERFIS — sigma_annual será CALIBRADO dos dados reais (MATH FIX #1)
# Os valores aqui são SEEDS iniciais, substituídos pela calibração
# ==============================================================================

SYNTHETIC_PROFILES = {
    # ═══════════════════════════════════════════════════════════════════
    # BOOM INDICES — Drift DOWN, Spike UP
    # ═══════════════════════════════════════════════════════════════════
    "BOOM 300 INDEX": {
        "gen_type": "BOOM", "vol_class": "BOOM", "sigma_seed": 0.50,
        "spike_lambda": 1/300, "spike_direction": "UP", "drift_direction": "DOWN",
        "spike_avg_ticks": 300, "spike_freq": "HIGH",
        "spread": 0.10, "adx_trend_min": 12, "adx_strong": 20,
        # Agressivo — Day Trade + Scalp
        "sl_atr_mult": 1.5, "tp1_r": 2.0, "tp2_r": 3.5,
        "sl_scalp_mult": 1.0, "tp1_scalp": 1.5, "tp2_scalp": 2.5,
        "bb_squeeze_threshold": 0.5, "zscore_extreme": 1.8,
        "hurst_trend_min": 0.50, "consecutive_reversal": 4,
        "roc_extreme_pct": 2.0, "mean_reversion_bias": 0.3, "risk_mult": 1.2,
        # BC-specific
        "rsi_spike_buy": 30, "rsi_spike_sell": 70,
        "rsi_extreme_buy": 20, "rsi_extreme_sell": 80,
        "drift_ema_fast": 5, "drift_ema_slow": 15,
        "spike_size_min_atr": 2.0,  # Spike mínimo = 2× ATR
        "post_spike_fade_pct": 0.4, # Fade 40% do spike
        "max_hold_scalp": 15,  # max candles M15
        "max_hold_day": 60,    # max candles M15 (~15h)
    },
    "BOOM 500 INDEX": {
        "gen_type": "BOOM", "vol_class": "BOOM", "sigma_seed": 0.50,
        "spike_lambda": 1/500, "spike_direction": "UP", "drift_direction": "DOWN",
        "spike_avg_ticks": 500, "spike_freq": "MEDIUM",
        "spread": 0.10, "adx_trend_min": 12, "adx_strong": 22,
        "sl_atr_mult": 1.8, "tp1_r": 2.5, "tp2_r": 4.0,
        "sl_scalp_mult": 1.0, "tp1_scalp": 1.5, "tp2_scalp": 2.5,
        "bb_squeeze_threshold": 0.55, "zscore_extreme": 1.8,
        "hurst_trend_min": 0.50, "consecutive_reversal": 5,
        "roc_extreme_pct": 2.0, "mean_reversion_bias": 0.3, "risk_mult": 1.1,
        "rsi_spike_buy": 30, "rsi_spike_sell": 70,
        "rsi_extreme_buy": 20, "rsi_extreme_sell": 80,
        "drift_ema_fast": 5, "drift_ema_slow": 15,
        "spike_size_min_atr": 2.0,
        "post_spike_fade_pct": 0.38,
        "max_hold_scalp": 15, "max_hold_day": 60,
    },
    "BOOM 600 INDEX": {
        "gen_type": "BOOM", "vol_class": "BOOM", "sigma_seed": 0.50,
        "spike_lambda": 1/600, "spike_direction": "UP", "drift_direction": "DOWN",
        "spike_avg_ticks": 600, "spike_freq": "MEDIUM",
        "spread": 0.10, "adx_trend_min": 14, "adx_strong": 22,
        "sl_atr_mult": 1.8, "tp1_r": 2.5, "tp2_r": 4.5,
        "sl_scalp_mult": 1.0, "tp1_scalp": 1.5, "tp2_scalp": 3.0,
        "bb_squeeze_threshold": 0.55, "zscore_extreme": 1.8,
        "hurst_trend_min": 0.50, "consecutive_reversal": 5,
        "roc_extreme_pct": 2.0, "mean_reversion_bias": 0.3, "risk_mult": 1.0,
        "rsi_spike_buy": 30, "rsi_spike_sell": 70,
        "rsi_extreme_buy": 20, "rsi_extreme_sell": 80,
        "drift_ema_fast": 5, "drift_ema_slow": 15,
        "spike_size_min_atr": 2.2,
        "post_spike_fade_pct": 0.35,
        "max_hold_scalp": 15, "max_hold_day": 60,
    },
    "BOOM 900 INDEX": {
        "gen_type": "BOOM", "vol_class": "BOOM", "sigma_seed": 0.50,
        "spike_lambda": 1/900, "spike_direction": "UP", "drift_direction": "DOWN",
        "spike_avg_ticks": 900, "spike_freq": "LOW",
        "spread": 0.10, "adx_trend_min": 14, "adx_strong": 24,
        "sl_atr_mult": 2.0, "tp1_r": 3.0, "tp2_r": 5.0,
        "sl_scalp_mult": 1.2, "tp1_scalp": 2.0, "tp2_scalp": 3.0,
        "bb_squeeze_threshold": 0.6, "zscore_extreme": 2.0,
        "hurst_trend_min": 0.50, "consecutive_reversal": 5,
        "roc_extreme_pct": 2.0, "mean_reversion_bias": 0.3, "risk_mult": 1.0,
        "rsi_spike_buy": 30, "rsi_spike_sell": 70,
        "rsi_extreme_buy": 20, "rsi_extreme_sell": 80,
        "drift_ema_fast": 8, "drift_ema_slow": 21,
        "spike_size_min_atr": 2.5,
        "post_spike_fade_pct": 0.35,
        "max_hold_scalp": 20, "max_hold_day": 80,
    },
    "BOOM 1000 INDEX": {
        "gen_type": "BOOM", "vol_class": "BOOM", "sigma_seed": 0.50,
        "spike_lambda": 1/1000, "spike_direction": "UP", "drift_direction": "DOWN",
        "spike_avg_ticks": 1000, "spike_freq": "LOW",
        "spread": 0.10, "adx_trend_min": 15, "adx_strong": 25,
        "sl_atr_mult": 2.0, "tp1_r": 3.0, "tp2_r": 5.5,
        "sl_scalp_mult": 1.2, "tp1_scalp": 2.0, "tp2_scalp": 3.5,
        "bb_squeeze_threshold": 0.6, "zscore_extreme": 2.0,
        "hurst_trend_min": 0.50, "consecutive_reversal": 6,
        "roc_extreme_pct": 2.5, "mean_reversion_bias": 0.3, "risk_mult": 1.0,
        "rsi_spike_buy": 30, "rsi_spike_sell": 70,
        "rsi_extreme_buy": 20, "rsi_extreme_sell": 80,
        "drift_ema_fast": 8, "drift_ema_slow": 21,
        "spike_size_min_atr": 2.5,
        "post_spike_fade_pct": 0.30,
        "max_hold_scalp": 20, "max_hold_day": 80,
    },
    # ═══════════════════════════════════════════════════════════════════
    # CRASH INDICES — Drift UP, Spike DOWN
    # ═══════════════════════════════════════════════════════════════════
    "CRASH 300 INDEX": {
        "gen_type": "CRASH", "vol_class": "CRASH", "sigma_seed": 0.50,
        "spike_lambda": 1/300, "spike_direction": "DOWN", "drift_direction": "UP",
        "spike_avg_ticks": 300, "spike_freq": "HIGH",
        "spread": 0.10, "adx_trend_min": 12, "adx_strong": 20,
        "sl_atr_mult": 1.5, "tp1_r": 2.0, "tp2_r": 3.5,
        "sl_scalp_mult": 1.0, "tp1_scalp": 1.5, "tp2_scalp": 2.5,
        "bb_squeeze_threshold": 0.5, "zscore_extreme": 1.8,
        "hurst_trend_min": 0.50, "consecutive_reversal": 4,
        "roc_extreme_pct": 2.0, "mean_reversion_bias": 0.3, "risk_mult": 1.2,
        "rsi_spike_buy": 30, "rsi_spike_sell": 70,
        "rsi_extreme_buy": 20, "rsi_extreme_sell": 80,
        "drift_ema_fast": 5, "drift_ema_slow": 15,
        "spike_size_min_atr": 2.0,
        "post_spike_fade_pct": 0.4,
        "max_hold_scalp": 15, "max_hold_day": 60,
    },
    "CRASH 500 INDEX": {
        "gen_type": "CRASH", "vol_class": "CRASH", "sigma_seed": 0.50,
        "spike_lambda": 1/500, "spike_direction": "DOWN", "drift_direction": "UP",
        "spike_avg_ticks": 500, "spike_freq": "MEDIUM",
        "spread": 0.10, "adx_trend_min": 12, "adx_strong": 22,
        "sl_atr_mult": 1.8, "tp1_r": 2.5, "tp2_r": 4.0,
        "sl_scalp_mult": 1.0, "tp1_scalp": 1.5, "tp2_scalp": 2.5,
        "bb_squeeze_threshold": 0.55, "zscore_extreme": 1.8,
        "hurst_trend_min": 0.50, "consecutive_reversal": 5,
        "roc_extreme_pct": 2.0, "mean_reversion_bias": 0.3, "risk_mult": 1.1,
        "rsi_spike_buy": 30, "rsi_spike_sell": 70,
        "rsi_extreme_buy": 20, "rsi_extreme_sell": 80,
        "drift_ema_fast": 5, "drift_ema_slow": 15,
        "spike_size_min_atr": 2.0,
        "post_spike_fade_pct": 0.38,
        "max_hold_scalp": 15, "max_hold_day": 60,
    },
    "CRASH 600 INDEX": {
        "gen_type": "CRASH", "vol_class": "CRASH", "sigma_seed": 0.50,
        "spike_lambda": 1/600, "spike_direction": "DOWN", "drift_direction": "UP",
        "spike_avg_ticks": 600, "spike_freq": "MEDIUM",
        "spread": 0.10, "adx_trend_min": 14, "adx_strong": 22,
        "sl_atr_mult": 1.8, "tp1_r": 2.5, "tp2_r": 4.5,
        "sl_scalp_mult": 1.0, "tp1_scalp": 1.5, "tp2_scalp": 3.0,
        "bb_squeeze_threshold": 0.55, "zscore_extreme": 1.8,
        "hurst_trend_min": 0.50, "consecutive_reversal": 5,
        "roc_extreme_pct": 2.0, "mean_reversion_bias": 0.3, "risk_mult": 1.0,
        "rsi_spike_buy": 30, "rsi_spike_sell": 70,
        "rsi_extreme_buy": 20, "rsi_extreme_sell": 80,
        "drift_ema_fast": 5, "drift_ema_slow": 15,
        "spike_size_min_atr": 2.2,
        "post_spike_fade_pct": 0.35,
        "max_hold_scalp": 15, "max_hold_day": 60,
    },
    "CRASH 900 INDEX": {
        "gen_type": "CRASH", "vol_class": "CRASH", "sigma_seed": 0.50,
        "spike_lambda": 1/900, "spike_direction": "DOWN", "drift_direction": "UP",
        "spike_avg_ticks": 900, "spike_freq": "LOW",
        "spread": 0.10, "adx_trend_min": 14, "adx_strong": 24,
        "sl_atr_mult": 2.0, "tp1_r": 3.0, "tp2_r": 5.0,
        "sl_scalp_mult": 1.2, "tp1_scalp": 2.0, "tp2_scalp": 3.0,
        "bb_squeeze_threshold": 0.6, "zscore_extreme": 2.0,
        "hurst_trend_min": 0.50, "consecutive_reversal": 5,
        "roc_extreme_pct": 2.0, "mean_reversion_bias": 0.3, "risk_mult": 1.0,
        "rsi_spike_buy": 30, "rsi_spike_sell": 70,
        "rsi_extreme_buy": 20, "rsi_extreme_sell": 80,
        "drift_ema_fast": 8, "drift_ema_slow": 21,
        "spike_size_min_atr": 2.5,
        "post_spike_fade_pct": 0.35,
        "max_hold_scalp": 20, "max_hold_day": 80,
    },
    "CRASH 1000 INDEX": {
        "gen_type": "CRASH", "vol_class": "CRASH", "sigma_seed": 0.50,
        "spike_lambda": 1/1000, "spike_direction": "DOWN", "drift_direction": "UP",
        "spike_avg_ticks": 1000, "spike_freq": "LOW",
        "spread": 0.10, "adx_trend_min": 15, "adx_strong": 25,
        "sl_atr_mult": 2.0, "tp1_r": 3.0, "tp2_r": 5.5,
        "sl_scalp_mult": 1.2, "tp1_scalp": 2.0, "tp2_scalp": 3.5,
        "bb_squeeze_threshold": 0.6, "zscore_extreme": 2.0,
        "hurst_trend_min": 0.50, "consecutive_reversal": 6,
        "roc_extreme_pct": 2.5, "mean_reversion_bias": 0.3, "risk_mult": 1.0,
        "rsi_spike_buy": 30, "rsi_spike_sell": 70,
        "rsi_extreme_buy": 20, "rsi_extreme_sell": 80,
        "drift_ema_fast": 8, "drift_ema_slow": 21,
        "spike_size_min_atr": 2.5,
        "post_spike_fade_pct": 0.30,
        "max_hold_scalp": 20, "max_hold_day": 80,
    },
}

DEFAULT_PROFILE = {
    "gen_type": "BOOM", "vol_class": "BOOM", "sigma_seed": 0.50,
    "spike_lambda": 1/500, "spike_direction": "UP", "drift_direction": "DOWN",
    "spike_avg_ticks": 500, "spike_freq": "MEDIUM",
    "spread": 0.10, "adx_trend_min": 14, "adx_strong": 22,
    "sl_atr_mult": 1.8, "tp1_r": 2.5, "tp2_r": 4.0,
    "sl_scalp_mult": 1.0, "tp1_scalp": 1.5, "tp2_scalp": 2.5,
    "bb_squeeze_threshold": 0.55, "zscore_extreme": 1.8,
    "hurst_trend_min": 0.50, "consecutive_reversal": 5,
    "roc_extreme_pct": 2.0, "mean_reversion_bias": 0.3, "risk_mult": 1.0,
    "rsi_spike_buy": 30, "rsi_spike_sell": 70,
    "rsi_extreme_buy": 20, "rsi_extreme_sell": 80,
    "drift_ema_fast": 5, "drift_ema_slow": 15,
    "spike_size_min_atr": 2.0,
    "post_spike_fade_pct": 0.35,
    "max_hold_scalp": 15, "max_hold_day": 60,
}

def get_profile(name: str) -> dict:
    for key, profile in SYNTHETIC_PROFILES.items():
        if key in name.upper():
            return profile.copy()
    return DEFAULT_PROFILE.copy()

# ==============================================================================
# 🔴 BUG FIX #1: AUTO-DETECT TIMEFRAME
# ==============================================================================

def detect_periods_per_year(df):
    """Detecta timeframe automaticamente e retorna períodos/ano corretos.
    Sintéticos operam 24/7/365, não 252 dias."""
    try:
        if len(df) < 3:
            return 365 * 24  # default H1
        deltas = (df.index[1:] - df.index[:-1]).total_seconds()
        avg_delta = np.median(deltas)
        if avg_delta < 120:       return 365 * 24 * 60   # M1
        elif avg_delta < 600:     return 365 * 24 * 12   # M5
        elif avg_delta < 1200:    return 365 * 24 * 4    # M15
        elif avg_delta < 5000:    return 365 * 24         # H1
        elif avg_delta < 20000:   return 365 * 6          # H4
        else:                     return 365              # Daily
    except:
        return 365 * 24

# ==============================================================================
# 🟠 MATH FIX #1: CALIBRAR SIGMA REAL DO HISTÓRICO
# ==============================================================================

def calibrate_sigma(df, periods_per_year):
    """Calcula sigma REAL do ativo a partir de todo o histórico disponível.
    Usa toda a série como referência — NÃO assume que Vol10 = 0.10."""
    try:
        log_ret = np.log(df['close'] / df['close'].shift(1)).dropna()
        if len(log_ret) < 50:
            return None
        return float(log_ret.std() * np.sqrt(periods_per_year))
    except:
        return None

# ==============================================================================
# GENERATOR MODELS V20 — TODOS OS BUGS CORRIGIDOS
# ==============================================================================

class GeneratorModelV20:
    """V20: Modela o gerador com sigma calibrado, direction-aware, multi-window"""

    @staticmethod
    def analyze_gbm(df, profile, sigma_calibrated, ppy):
        """
        🔴 FIX #2: VOL_COMPRESS agora sabe a DIREÇÃO (contra movimento recente)
        🟠 FIX #1: Usa sigma calibrado, não inventado
        🔴 FIX #1: periods_per_year auto-detectado
        🟢 PRECISION #1: Multi-window (30, 100, 300)
        🟡 EDGE #6: Preço teórico vs real
        """
        try:
            log_returns = np.log(df['close'] / df['close'].shift(1)).dropna()
            sigma_ref = sigma_calibrated if sigma_calibrated else profile.get('sigma_seed', 0.5)
            results = {}

            # 🟢 MULTI-WINDOW ANALYSIS
            for label, window in [("SHORT", 30), ("MEDIUM", 100), ("LONG", min(300, len(log_returns)-1))]:
                if len(log_returns) < window:
                    results[label] = {"vol_ratio": 1.0, "signal": "NEUTRAL", "confidence": 0}
                    continue
                recent = log_returns.tail(window)
                vol_realized = float(recent.std() * np.sqrt(ppy))
                ratio = vol_realized / sigma_ref if sigma_ref > 0 else 1.0

                # Chi² test correto
                expected_var = (sigma_ref / np.sqrt(ppy)) ** 2
                observed_var = float(recent.var())
                chi2 = (window - 1) * observed_var / expected_var if expected_var > 0 else window
                z_chi = (chi2 - (window - 1)) / np.sqrt(2 * (window - 1))
                p_value = 2 * (1 - norm.cdf(abs(z_chi)))

                if ratio > 1.3:
                    signal = "VOL_OVEREXTENDED"
                    confidence = min((ratio - 1.0) / 0.5, 1.0) * 100
                elif ratio < 1.0 / 1.3:
                    signal = "VOL_COMPRESSED"
                    confidence = min((1.0 / ratio - 1.0) / 0.5, 1.0) * 100
                else:
                    signal = "VOL_NORMAL"
                    confidence = 0

                results[label] = {
                    "vol_ratio": round(ratio, 3), "vol_realized": round(vol_realized, 4),
                    "signal": signal, "confidence": round(confidence, 1),
                    "p_value": round(p_value, 4), "z_chi": round(z_chi, 2),
                }

            # CONSENSUS: multi-window agreement
            signals = [r['signal'] for r in results.values()]
            if all(s == "VOL_OVEREXTENDED" for s in signals):
                consensus = "VOL_OVEREXTENDED"
                consensus_confidence = min(sum(r['confidence'] for r in results.values()) / 3 * 1.5, 100)
            elif all(s == "VOL_COMPRESSED" for s in signals):
                consensus = "VOL_COMPRESSED"
                consensus_confidence = min(sum(r['confidence'] for r in results.values()) / 3 * 1.5, 100)
            elif signals.count("VOL_OVEREXTENDED") >= 2:
                consensus = "VOL_OVEREXTENDED"
                consensus_confidence = min(sum(r['confidence'] for r in results.values() if r['signal']=="VOL_OVEREXTENDED") / 2, 100)
            elif signals.count("VOL_COMPRESSED") >= 2:
                consensus = "VOL_COMPRESSED"
                consensus_confidence = min(sum(r['confidence'] for r in results.values() if r['signal']=="VOL_COMPRESSED") / 2, 100)
            else:
                consensus = "VOL_NORMAL"
                consensus_confidence = 0

            # 🔴 BUG FIX #2: DIREÇÃO CONTRA O MOVIMENTO RECENTE
            lookback = min(100, len(df) - 1)
            recent_move = float(df['close'].iloc[-1] - df['close'].iloc[-lookback])
            if consensus == "VOL_OVEREXTENDED":
                compress_direction = "BEARISH" if recent_move > 0 else "BULLISH"
            else:
                compress_direction = "NEUTRAL"

            # 🟡 EDGE #6: PREÇO TEÓRICO VS REAL
            lookback_price = min(200, len(df) - 1)
            start_price = float(df['close'].iloc[-lookback_price])
            current_price = float(df['close'].iloc[-1])
            t_years = lookback_price / ppy
            expected_var_price = sigma_ref**2 * t_years
            actual_log_dev = np.log(current_price / start_price) if start_price > 0 else 0
            z_price = actual_log_dev / np.sqrt(expected_var_price) if expected_var_price > 0 else 0

            return {
                "windows": results,
                "consensus": consensus,
                "consensus_confidence": round(consensus_confidence, 1),
                "compress_direction": compress_direction,
                "recent_move": round(recent_move, 4),
                "sigma_calibrated": round(sigma_ref, 4),
                "z_price": round(z_price, 2),
                "price_deviation_signal": "OVERBOUGHT" if z_price > 2 else "OVERSOLD" if z_price < -2 else "NORMAL",
                "vol_ratio": results.get("MEDIUM", {}).get("vol_ratio", 1.0),
                "signal": consensus,
                "confidence": consensus_confidence,
            }
        except:
            return {"windows": {}, "consensus": "NEUTRAL", "consensus_confidence": 0,
                    "compress_direction": "NEUTRAL", "sigma_calibrated": 0,
                    "z_price": 0, "signal": "NEUTRAL", "confidence": 0, "vol_ratio": 1.0}

    @staticmethod
    def analyze_crash_boom(df, profile, ppy):
        """
        🟠 FIX #4: MAD-based spike detection (não std circular)
        🟠 FIX #5: Drift por REGRESSÃO LINEAR (não média)
        🟡 EDGE #5: Spike Decay Model
        🔴 FIX #3: Drift direction calculada, não hardcoded
        """
        try:
            window = min(300, len(df) - 1)
            if window < 50:
                return {"signal": "NEUTRAL", "spikes_found": 0, "drift_direction": "UNKNOWN",
                        "drift_slope": 0, "last_spike_bars": 999, "spike_phase": "UNKNOWN", "decay_strength": 0}

            recent = df.tail(window)
            returns = recent['close'].pct_change().dropna()
            is_boom = profile.get('gen_type') == 'BOOM'

            # 🟠 FIX #4: MAD-BASED SPIKE DETECTION
            mad = float(median_abs_deviation(returns.values, scale='normal'))
            spike_threshold = mad * 4.5 if mad > 0 else returns.std() * 3.5

            spike_indices = []
            for i in range(len(returns)):
                r = returns.iloc[i]
                if is_boom and r > spike_threshold:
                    spike_indices.append(i)
                elif not is_boom and r < -spike_threshold:
                    spike_indices.append(i)

            last_spike_bars = (len(returns) - spike_indices[-1]) if spike_indices else 999

            # 🟠 FIX #5: DRIFT POR REGRESSÃO LINEAR
            slopes = []
            if len(spike_indices) >= 2:
                for si in range(len(spike_indices) - 1):
                    start_idx = spike_indices[si] + 3  # após absorção
                    end_idx = spike_indices[si + 1]
                    if end_idx - start_idx > 5:
                        segment = recent['close'].iloc[start_idx:end_idx].values
                        x = np.arange(len(segment))
                        try:
                            slope = np.polyfit(x, segment, 1)[0]
                            norm_slope = slope / recent['close'].iloc[start_idx] if recent['close'].iloc[start_idx] > 0 else 0
                            slopes.append(norm_slope)
                        except:
                            pass

            # Também calcular drift do segmento ATUAL (após último spike)
            if spike_indices:
                current_start = spike_indices[-1] + 3
                if current_start < len(recent) - 5:
                    current_segment = recent['close'].iloc[current_start:].values
                    x = np.arange(len(current_segment))
                    try:
                        current_slope = np.polyfit(x, current_segment, 1)[0]
                        current_norm_slope = current_slope / recent['close'].iloc[current_start]
                        slopes.append(current_norm_slope)
                    except:
                        pass

            drift_slope = float(np.median(slopes)) if slopes else 0
            drift_direction = "UP" if drift_slope > 0 else "DOWN" if drift_slope < 0 else "FLAT"
            drift_strength = abs(drift_slope) * 10000  # Normalizar para legibilidade

            avg_between = window / max(len(spike_indices), 1)

            # 🟡 EDGE #5: SPIKE DECAY MODEL
            progress = last_spike_bars / avg_between if avg_between > 0 else 0
            if progress < 0.05:
                spike_phase = "ABSORBING"
                decay_strength = 0
            elif progress < 0.15:
                spike_phase = "DRIFT_STRONG"
                decay_strength = drift_strength * 1.5
            elif progress < 0.5:
                spike_phase = "DRIFT_NORMAL"
                decay_strength = drift_strength * 1.0
            elif progress < 0.8:
                spike_phase = "DRIFT_WEAKENING"
                decay_strength = drift_strength * 0.5
            else:
                spike_phase = "SPIKE_IMMINENT"
                decay_strength = 0

            # Signal
            if spike_phase in ["DRIFT_STRONG", "DRIFT_NORMAL"] and drift_strength > 0.5:
                signal = f"DRIFT_{drift_direction}"
            elif spike_phase == "ABSORBING":
                signal = "SPIKE_RECOVERY"
            elif spike_phase == "SPIKE_IMMINENT":
                signal = "SPIKE_WARNING"
            else:
                signal = "NEUTRAL"

            return {
                "signal": signal,
                "spikes_found": len(spike_indices),
                "drift_direction": drift_direction,
                "drift_slope": round(drift_slope * 10000, 4),
                "drift_strength": round(drift_strength, 3),
                "last_spike_bars": last_spike_bars,
                "avg_bars_between": round(avg_between, 0),
                "spike_phase": spike_phase,
                "progress": round(progress, 2),
                "decay_strength": round(decay_strength, 3),
                "confidence": min(drift_strength * 30, 100) if signal != "NEUTRAL" else 0,
            }
        except:
            return {"signal": "NEUTRAL", "spikes_found": 0, "drift_direction": "UNKNOWN",
                    "drift_slope": 0, "last_spike_bars": 999, "spike_phase": "UNKNOWN",
                    "decay_strength": 0, "confidence": 0}

    @staticmethod
    def analyze_step(df, profile, ppy):
        """
        🟠 FIX #3: Escala correta (log-returns, não step_size em candles)
        """
        try:
            window = min(300, len(df) - 1)
            if window < 50:
                return {"signal": "NEUTRAL", "deviation_sigma": 0, "runs_test": "NORMAL", "runs_z": 0}

            recent = df.tail(window)
            log_ret = np.log(recent['close'] / recent['close'].shift(1)).dropna()

            # Deviation: vol realizada recente vs toda a série
            full_log_ret = np.log(df['close'] / df['close'].shift(1)).dropna()
            full_std = float(full_log_ret.std())
            recent_std = float(log_ret.std()) if len(log_ret) > 10 else full_std

            # Preço: quanto desviou em termos de std acumulado
            price_change = float(recent['close'].iloc[-1] - recent['close'].iloc[0])
            expected_std_price = full_std * np.sqrt(window) * float(recent['close'].iloc[0])
            deviation_sigma = price_change / expected_std_price if expected_std_price > 0 else 0

            # Runs test
            directions = (recent['close'].diff().dropna() > 0).astype(int)
            runs = 1
            for i in range(1, len(directions)):
                if directions.iloc[i] != directions.iloc[i-1]:
                    runs += 1
            n1 = int(directions.sum())
            n0 = len(directions) - n1
            if n0 > 0 and n1 > 0:
                expected_runs = (2 * n0 * n1) / (n0 + n1) + 1
                denom = (n0 + n1)**2 * (n0 + n1 - 1)
                std_runs = np.sqrt(2*n0*n1*(2*n0*n1-n0-n1) / denom) if denom > 0 else 1
                z_runs = (runs - expected_runs) / std_runs if std_runs > 0 else 0
            else:
                z_runs = 0

            runs_test = "CLUSTERING" if z_runs < -2 else "ALTERNATING" if z_runs > 2 else "NORMAL"

            # Vol ratio
            vol_ratio = recent_std / full_std if full_std > 0 else 1.0

            # Signal
            if abs(deviation_sigma) > 2.5:
                signal = "EXTREME_DEVIATION"
            elif abs(deviation_sigma) > 1.5:
                signal = "HIGH_DEVIATION"
            elif runs_test == "CLUSTERING":
                signal = "TREND_CLUSTER"
            elif runs_test == "ALTERNATING":
                signal = "MEAN_REVERT_PATTERN"
            elif vol_ratio > 1.4:
                signal = "VOL_EXPANDING"
            elif vol_ratio < 0.6:
                signal = "VOL_COMPRESSING"
            else:
                signal = "NEUTRAL"

            return {
                "signal": signal,
                "deviation_sigma": round(deviation_sigma, 2),
                "runs_test": runs_test,
                "runs_z": round(z_runs, 2),
                "vol_ratio": round(vol_ratio, 3),
                "price_change": round(price_change, 4),
                "confidence": min(abs(deviation_sigma) * 25, 100) if signal != "NEUTRAL" else 0,
            }
        except:
            return {"signal": "NEUTRAL", "deviation_sigma": 0, "runs_test": "NORMAL",
                    "runs_z": 0, "confidence": 0}

# ==============================================================================
# 🟡 EDGE #1: VARIANCE RATIO TEST — Detecta se há edge real
# ==============================================================================

def variance_ratio_test(series, periods=[2, 5, 10, 20]):
    """Se VR ≠ 1 → NÃO é random walk → há edge explorável.
    VR < 1 = mean-reverting. VR > 1 = trending."""
    try:
        log_ret = np.log(series / series.shift(1)).dropna()
        if len(log_ret) < 50:
            return {"has_edge": False, "dominant_type": "RANDOM_WALK", "results": {}}
        var1 = float(log_ret.var())
        if var1 == 0:
            return {"has_edge": False, "dominant_type": "RANDOM_WALK", "results": {}}
        results = {}
        for q in periods:
            q_ret = np.log(series / series.shift(q)).dropna()
            if len(q_ret) < 20:
                continue
            var_q = float(q_ret.var())
            vr = var_q / (q * var1)
            n = len(log_ret)
            z = (vr - 1) / np.sqrt(2*(2*q-1)*(q-1) / (3*q*n)) if n > 0 else 0
            results[q] = {"vr": round(vr, 4), "z": round(z, 2), "significant": abs(z) > 1.96,
                          "type": "MEAN_REVERT" if vr < 1 and abs(z)>1.96 else "TRENDING" if vr > 1 and abs(z)>1.96 else "RANDOM"}
        sig_results = [r for r in results.values() if r['significant']]
        if not sig_results:
            return {"has_edge": False, "dominant_type": "RANDOM_WALK", "results": results,
                    "best_vr": min((r['vr'] for r in results.values()), default=1.0)}
        types = [r['type'] for r in sig_results]
        dominant = max(set(types), key=types.count)
        return {"has_edge": True, "dominant_type": dominant, "results": results,
                "n_significant": len(sig_results),
                "best_vr": min((r['vr'] for r in results.values()), default=1.0)}
    except:
        return {"has_edge": False, "dominant_type": "RANDOM_WALK", "results": {}}

# ==============================================================================
# 🟡 EDGE #2: AUTOCORRELAÇÃO DE RETORNOS
# ==============================================================================

def autocorrelation_analysis(series, max_lag=5):
    """Autocorrelação significativa → padrão explorável"""
    try:
        log_ret = np.log(series / series.shift(1)).dropna()
        if len(log_ret) < 50:
            return {"significant_lags": [], "dominant_type": "NOISE", "acf_1": 0}
        sig_threshold = 2 / np.sqrt(len(log_ret))
        results = {}
        for lag in range(1, max_lag + 1):
            acf = float(log_ret.autocorr(lag=lag))
            sig = abs(acf) > sig_threshold
            rtype = "MEAN_REVERT" if acf < -sig_threshold else "MOMENTUM" if acf > sig_threshold else "NOISE"
            results[lag] = {"acf": round(acf, 4), "significant": sig, "type": rtype}
        sig_lags = [lag for lag, r in results.items() if r['significant']]
        types = [results[l]['type'] for l in sig_lags]
        dominant = max(set(types), key=types.count) if types else "NOISE"
        return {"results": results, "significant_lags": sig_lags, "dominant_type": dominant,
                "acf_1": results.get(1, {}).get('acf', 0), "has_pattern": len(sig_lags) > 0}
    except:
        return {"significant_lags": [], "dominant_type": "NOISE", "acf_1": 0, "has_pattern": False}

# ==============================================================================
# 🟡 EDGE #3: VOLATILITY CLUSTERING (GARCH EFFECT)
# ==============================================================================

def volatility_clustering_test(series, window=20):
    """Autocorrelação de retornos absolutos → vol clusters → edge"""
    try:
        log_ret = np.log(series / series.shift(1)).dropna()
        if len(log_ret) < 50:
            return {"has_clustering": False, "vol_regime": "NORMAL", "acf_abs": 0}
        abs_ret = log_ret.abs()
        acf_abs = float(abs_ret.autocorr(lag=1))
        sig = 2 / np.sqrt(len(abs_ret))
        has_clustering = acf_abs > sig

        current_vol = float(abs_ret.tail(window).mean())
        historical_vol = float(abs_ret.mean())
        vol_ratio = current_vol / historical_vol if historical_vol > 0 else 1.0

        if has_clustering:
            if vol_ratio > 1.5:
                regime = "HIGH_VOL_CLUSTER"
            elif vol_ratio < 0.6:
                regime = "LOW_VOL_CLUSTER"
            else:
                regime = "NORMAL_CLUSTER"
        else:
            regime = "NO_CLUSTER"

        return {"has_clustering": has_clustering, "vol_regime": regime,
                "acf_abs": round(acf_abs, 4), "vol_ratio": round(vol_ratio, 3),
                "current_vol": round(current_vol, 6), "historical_vol": round(historical_vol, 6)}
    except:
        return {"has_clustering": False, "vol_regime": "NORMAL", "acf_abs": 0}

# ==============================================================================
# V21+ ENGINE: ADX SLOPE DETECTION — Early Trend Capture
# ==============================================================================

def adx_slope_analysis(df, lookback=14):
    """Detects ADX acceleration BEFORE it crosses thresholds.
    Rising ADX slope = trend forming. Falling = trend dying."""
    try:
        if len(df) < lookback + 5 or 'ADX' not in df.columns:
            return {"slope": 0, "acceleration": 0, "phase": "UNKNOWN", "confidence": 0}
        adx_series = df['ADX'].tail(lookback).dropna()
        if len(adx_series) < 8:
            return {"slope": 0, "acceleration": 0, "phase": "UNKNOWN", "confidence": 0}
        x = np.arange(len(adx_series))
        slope = np.polyfit(x, adx_series.values, 1)[0]
        # Acceleration: slope of last half vs first half
        mid = len(adx_series) // 2
        slope_1 = np.polyfit(np.arange(mid), adx_series.values[:mid], 1)[0]
        slope_2 = np.polyfit(np.arange(len(adx_series) - mid), adx_series.values[mid:], 1)[0]
        acceleration = slope_2 - slope_1
        adx_now = float(adx_series.iloc[-1])
        if slope > 0.5 and acceleration > 0:
            phase = "TREND_FORMING"
            confidence = min(slope * 20 + acceleration * 30, 100)
        elif slope > 0.3 and adx_now > 20:
            phase = "TREND_ESTABLISHED"
            confidence = min(adx_now * 1.5 + slope * 10, 100)
        elif slope > 0.5 and acceleration < 0:
            phase = "TREND_MATURING"
            confidence = min(slope * 15, 80)
        elif slope < -0.3:
            phase = "TREND_DYING"
            confidence = min(abs(slope) * 20, 80)
        elif abs(slope) < 0.15 and adx_now < 20:
            phase = "RANGE_FLAT"
            confidence = 0
        else:
            phase = "TRANSITIONING"
            confidence = min(abs(slope) * 15, 50)
        return {
            "slope": round(float(slope), 3),
            "acceleration": round(float(acceleration), 3),
            "phase": phase,
            "adx_now": round(adx_now, 1),
            "confidence": round(float(confidence), 1)
        }
    except:
        return {"slope": 0, "acceleration": 0, "phase": "UNKNOWN", "confidence": 0}

# ==============================================================================
# V21+ ENGINE: EMA RIBBON SPREAD — Trend Strength Measurement
# ==============================================================================

def ema_ribbon_analysis(df):
    """Measures EMA ribbon spread and ordering for trend quality.
    Expanding ribbon = strong trend. Contracting = weakening."""
    try:
        if len(df) < 5 or not all(c in df.columns for c in ['EMA_20', 'EMA_50', 'EMA_200']):
            return {"spread": 0, "expanding": False, "quality": "NONE", "direction": "NEUTRAL"}
        c = df.iloc[-1]
        e20, e50, e200 = float(c['EMA_20']), float(c['EMA_50']), float(c['EMA_200'])
        atr = float(c['ATR']) if c['ATR'] > 0 else 1
        # Normalized spreads
        spread_20_50 = (e20 - e50) / atr
        spread_50_200 = (e50 - e200) / atr
        total_spread = abs(spread_20_50) + abs(spread_50_200)
        # Check ordering
        bull_order = e20 > e50 > e200
        bear_order = e20 < e50 < e200
        # Expansion check (compare with 5 bars ago)
        if len(df) >= 6:
            p = df.iloc[-6]
            prev_spread = abs(float(p['EMA_20']) - float(p['EMA_50'])) / atr + abs(float(p['EMA_50']) - float(p['EMA_200'])) / atr
            expanding = total_spread > prev_spread * 1.05
            contracting = total_spread < prev_spread * 0.95
        else:
            expanding = False
            contracting = False
        # Quality
        if (bull_order or bear_order) and expanding and total_spread > 3:
            quality = "EXCELLENT"
        elif (bull_order or bear_order) and total_spread > 2:
            quality = "GOOD"
        elif (bull_order or bear_order):
            quality = "MODERATE"
        elif abs(spread_20_50) < 0.5 and abs(spread_50_200) < 1:
            quality = "COMPRESSED"
        else:
            quality = "MIXED"
        direction = "BULLISH" if spread_20_50 > 0 and spread_50_200 > 0 else \
                    "BEARISH" if spread_20_50 < 0 and spread_50_200 < 0 else "MIXED"
        return {
            "spread_20_50": round(spread_20_50, 2),
            "spread_50_200": round(spread_50_200, 2),
            "total_spread": round(total_spread, 2),
            "expanding": expanding, "contracting": contracting,
            "quality": quality, "direction": direction,
            "bull_order": bull_order, "bear_order": bear_order,
        }
    except:
        return {"spread": 0, "expanding": False, "quality": "NONE", "direction": "NEUTRAL"}

# ==============================================================================
# V21+ ENGINE: MULTI-TF TREND COHERENCE SCORING
# ==============================================================================

def multi_tf_trend_coherence(h4, h1, m15, m5=None):
    """Scores how coherent the trend is across all timeframes.
    Perfect coherence = highest confidence entries."""
    try:
        score = 0.0; details = []
        for tf, name, weight in [(h4, "H4", 3.0), (h1, "H1", 2.0), (m15, "M15", 1.5), (m5, "M5", 1.0)]:
            if tf is None or len(tf) < 20:
                continue
            c = tf.iloc[-1]
            # EMA alignment direction
            if c['EMA_20'] > c['EMA_50'] > c['EMA_200']:
                tf_dir = "BULL"
            elif c['EMA_20'] < c['EMA_50'] < c['EMA_200']:
                tf_dir = "BEAR"
            else:
                tf_dir = "MIXED"
            # MACD confirmation
            macd_bull = c['MACD_hist'] > 0
            # RSI zone
            rsi = c.get('RSI', 50)
            rsi_ok = (40 < rsi < 70) if tf_dir == "BULL" else (30 < rsi < 60) if tf_dir == "BEAR" else True
            # ADX trending
            adx = c.get('ADX', 0)
            trending = adx > 20
            # Score this TF
            tf_score = 0
            if tf_dir in ["BULL", "BEAR"]:
                tf_score += 1.0
                if (tf_dir == "BULL" and macd_bull) or (tf_dir == "BEAR" and not macd_bull):
                    tf_score += 0.5
                if rsi_ok:
                    tf_score += 0.3
                if trending:
                    tf_score += 0.2
            score += tf_score * weight
            details.append({"tf": name, "dir": tf_dir, "score": round(tf_score * weight, 1)})
        max_score = 3.0 * 2.0 + 2.0 * 2.0 + 1.5 * 2.0 + (1.0 * 2.0 if m5 is not None else 0)
        normalized = score / max_score * 100 if max_score > 0 else 0
        # Coherence: check if all TFs agree on direction
        dirs = [d['dir'] for d in details if d['dir'] != "MIXED"]
        if dirs and all(d == dirs[0] for d in dirs):
            coherence = "PERFECT"
            coherent_dir = "BULLISH" if dirs[0] == "BULL" else "BEARISH"
        elif dirs and dirs.count(dirs[0]) >= len(dirs) * 0.7:
            coherence = "STRONG"
            coherent_dir = "BULLISH" if dirs.count("BULL") > dirs.count("BEAR") else "BEARISH"
        else:
            coherence = "WEAK"
            coherent_dir = "MIXED"
        return {
            "score": round(normalized, 1),
            "coherence": coherence,
            "coherent_direction": coherent_dir,
            "details": details,
            "n_timeframes": len(details),
        }
    except:
        return {"score": 0, "coherence": "WEAK", "coherent_direction": "MIXED", "details": []}

# ==============================================================================
# V21+ ENGINE: VWAP PROXY — Institutional Entry Zones
# ==============================================================================

def vwap_proxy_analysis(df, lookback=50):
    """VWAP proxy using typical price × range as volume proxy.
    Identifies institutional accumulation/distribution zones."""
    try:
        if len(df) < lookback:
            return {"vwap": 0, "deviation": 0, "zone": "UNKNOWN"}
        recent = df.tail(lookback)
        typical_price = (recent['high'] + recent['low'] + recent['close']) / 3
        vol_proxy = recent['high'] - recent['low']  # range as volume proxy
        cumulative_tpv = (typical_price * vol_proxy).cumsum()
        cumulative_vol = vol_proxy.cumsum()
        vwap = cumulative_tpv / cumulative_vol.replace(0, np.nan)
        vwap_current = float(vwap.iloc[-1]) if pd.notna(vwap.iloc[-1]) else float(typical_price.iloc[-1])
        current_price = float(df['close'].iloc[-1])
        atr = float(df['ATR'].iloc[-1]) if df['ATR'].iloc[-1] > 0 else 1
        deviation = (current_price - vwap_current) / atr
        if deviation > 2.0:
            zone = "FAR_ABOVE_VWAP"
        elif deviation > 0.5:
            zone = "ABOVE_VWAP"
        elif deviation > -0.5:
            zone = "AT_VWAP"
        elif deviation > -2.0:
            zone = "BELOW_VWAP"
        else:
            zone = "FAR_BELOW_VWAP"
        # Entry quality: best entries are near VWAP in trend direction
        return {
            "vwap": round(vwap_current, 5),
            "deviation": round(float(deviation), 2),
            "zone": zone,
            "entry_quality": "EXCELLENT" if abs(deviation) < 0.5 else "GOOD" if abs(deviation) < 1.5 else "POOR",
        }
    except:
        return {"vwap": 0, "deviation": 0, "zone": "UNKNOWN", "entry_quality": "UNKNOWN"}

# ==============================================================================
# V21+ ENGINE: CANDLE STRUCTURE SCORING — Entry Quality
# ==============================================================================

def candle_structure_score(df, direction, n_candles=5):
    """Scores the last N candles' structure quality for entry.
    Strong bodies, proper wicks, momentum sequence = better entry."""
    try:
        if len(df) < n_candles + 1:
            return {"score": 0, "quality": "UNKNOWN", "pattern_type": "NONE"}
        recent = df.tail(n_candles)
        is_long = "BULL" in str(direction) or "LONG" in str(direction)
        score = 0.0
        # 1. Body-to-range ratio (strong moves have large bodies)
        bodies = abs(recent['close'] - recent['open'])
        ranges = (recent['high'] - recent['low']).replace(0, np.nan)
        body_ratios = (bodies / ranges).dropna()
        avg_body_ratio = float(body_ratios.mean()) if len(body_ratios) > 0 else 0.5
        if avg_body_ratio > 0.6:
            score += 25  # Strong directional candles
        elif avg_body_ratio > 0.4:
            score += 15
        # 2. Directional consistency
        if is_long:
            bullish_candles = sum(recent['close'] > recent['open'])
        else:
            bullish_candles = sum(recent['close'] < recent['open'])
        consistency = bullish_candles / n_candles
        score += consistency * 25
        # 3. Wick analysis (favorable wicks)
        last = df.iloc[-1]
        body = abs(last['close'] - last['open'])
        rng = last['high'] - last['low']
        if rng > 0:
            if is_long:
                lower_wick = min(last['open'], last['close']) - last['low']
                upper_wick = last['high'] - max(last['open'], last['close'])
                # Long entries: small upper wick (no rejection), lower wick ok
                if upper_wick / rng < 0.2:
                    score += 15
                if lower_wick / rng > 0.3 and last['close'] > last['open']:
                    score += 10  # Demand wick
            else:
                upper_wick = last['high'] - max(last['open'], last['close'])
                lower_wick = min(last['open'], last['close']) - last['low']
                if lower_wick / rng < 0.2:
                    score += 15
                if upper_wick / rng > 0.3 and last['close'] < last['open']:
                    score += 10  # Supply wick
        # 4. Closing position (close near high for longs, near low for shorts)
        if rng > 0:
            close_pos = (last['close'] - last['low']) / rng
            if is_long and close_pos > 0.7:
                score += 15
            elif not is_long and close_pos < 0.3:
                score += 15
        # 5. Range expansion (last candle bigger than recent average)
        if len(df) > n_candles + 5:
            prev_avg_range = float((df['high'] - df['low']).iloc[-(n_candles+5):-n_candles].mean())
            if prev_avg_range > 0 and rng > prev_avg_range * 1.3:
                score += 10
        quality = "EXCELLENT" if score >= 75 else "GOOD" if score >= 55 else "MODERATE" if score >= 35 else "WEAK"
        # Pattern type
        if consistency > 0.8 and avg_body_ratio > 0.5:
            pattern_type = "IMPULSE"
        elif consistency < 0.4:
            pattern_type = "CONFLICTED"
        elif avg_body_ratio < 0.3:
            pattern_type = "INDECISION"
        else:
            pattern_type = "BUILDING"
        return {"score": round(min(score, 100), 1), "quality": quality, "pattern_type": pattern_type,
                "body_ratio": round(avg_body_ratio, 2) if len(body_ratios) > 0 else 0,
                "consistency": round(consistency, 2)}
    except:
        return {"score": 0, "quality": "UNKNOWN", "pattern_type": "NONE"}

# ==============================================================================
# V21+ ENGINE: MOMENTUM ACCELERATION — Optimal Timing
# ==============================================================================

def momentum_acceleration(df, periods=[3, 7, 14]):
    """Measures rate of change of momentum itself.
    Accelerating momentum = ideal entry point.
    Decelerating = wait or take profit."""
    try:
        if len(df) < max(periods) + 5 or 'MACD_hist' not in df.columns:
            return {"acceleration": 0, "phase": "UNKNOWN", "confidence": 0}
        hist = df['MACD_hist'].tail(max(periods) + 2).dropna()
        if len(hist) < max(periods):
            return {"acceleration": 0, "phase": "UNKNOWN", "confidence": 0}
        # Rate of change measurements at different scales
        rocs = {}
        for p in periods:
            if len(hist) > p:
                roc = float(hist.iloc[-1] - hist.iloc[-p]) / abs(float(hist.iloc[-p])) * 100 if hist.iloc[-p] != 0 else 0
                rocs[p] = roc
        if not rocs:
            return {"acceleration": 0, "phase": "UNKNOWN", "confidence": 0}
        short_roc = rocs.get(3, 0)
        med_roc = rocs.get(7, 0)
        long_roc = rocs.get(14, 0)
        # Phase detection
        current_hist = float(hist.iloc[-1])
        prev_hist = float(hist.iloc[-2])
        if current_hist > 0 and current_hist > prev_hist and short_roc > 0:
            phase = "BULL_ACCELERATING"
            confidence = min(abs(short_roc) * 0.5 + abs(med_roc) * 0.3, 100)
        elif current_hist > 0 and current_hist < prev_hist:
            phase = "BULL_DECELERATING"
            confidence = min(abs(short_roc) * 0.3, 60)
        elif current_hist < 0 and current_hist < prev_hist and short_roc < 0:
            phase = "BEAR_ACCELERATING"
            confidence = min(abs(short_roc) * 0.5 + abs(med_roc) * 0.3, 100)
        elif current_hist < 0 and current_hist > prev_hist:
            phase = "BEAR_DECELERATING"
            confidence = min(abs(short_roc) * 0.3, 60)
        elif abs(current_hist) < abs(prev_hist) * 0.3:
            phase = "ZERO_CROSS_IMMINENT"
            confidence = 70
        else:
            phase = "NEUTRAL"
            confidence = 0
        # Consecutive accelerating bars
        accel_bars = 0
        for i in range(1, min(8, len(hist))):
            if abs(float(hist.iloc[-i])) > abs(float(hist.iloc[-i-1])) if i < len(hist) - 1 else False:
                accel_bars += 1
            else:
                break
        return {
            "acceleration": round(float(short_roc), 2),
            "phase": phase,
            "confidence": round(float(confidence), 1),
            "short_roc": round(float(short_roc), 2),
            "med_roc": round(float(med_roc), 2),
            "long_roc": round(float(long_roc), 2),
            "accel_bars": accel_bars,
            "current_hist": round(float(current_hist), 6),
        }
    except:
        return {"acceleration": 0, "phase": "UNKNOWN", "confidence": 0}

# ==============================================================================
# V21+ ENGINE: DYNAMIC ATR CHANNEL — Volatility-Adjusted Entries
# ==============================================================================

def atr_channel_entry(df, direction, lookback=20):
    """Calculates optimal entry using ATR channels.
    Entries near lower channel in uptrend = high probability."""
    try:
        if len(df) < lookback + 5 or 'ATR' not in df.columns:
            return {"channel_entry": None, "channel_position": 0.5, "quality": "UNKNOWN"}
        recent = df.tail(lookback)
        ema = recent['EMA_20']
        atr = recent['ATR']
        upper_channel = ema + atr * 2
        lower_channel = ema - atr * 2
        current_price = float(df['close'].iloc[-1])
        ema_now = float(ema.iloc[-1])
        atr_now = float(atr.iloc[-1])
        channel_range = float(upper_channel.iloc[-1]) - float(lower_channel.iloc[-1])
        if channel_range > 0:
            channel_position = (current_price - float(lower_channel.iloc[-1])) / channel_range
        else:
            channel_position = 0.5
        is_long = "BULL" in str(direction) or "LONG" in str(direction)
        # Optimal entry zones
        if is_long:
            if channel_position < 0.3:
                quality = "OPTIMAL"  # Near lower channel in uptrend
                channel_entry = float(lower_channel.iloc[-1]) + atr_now * 0.3
            elif channel_position < 0.5:
                quality = "GOOD"
                channel_entry = ema_now - atr_now * 0.2
            elif channel_position < 0.7:
                quality = "FAIR"
                channel_entry = current_price
            else:
                quality = "OVEREXTENDED"
                channel_entry = ema_now  # Wait for pullback to EMA
        else:
            if channel_position > 0.7:
                quality = "OPTIMAL"
                channel_entry = float(upper_channel.iloc[-1]) - atr_now * 0.3
            elif channel_position > 0.5:
                quality = "GOOD"
                channel_entry = ema_now + atr_now * 0.2
            elif channel_position > 0.3:
                quality = "FAIR"
                channel_entry = current_price
            else:
                quality = "OVEREXTENDED"
                channel_entry = ema_now
        return {
            "channel_entry": round(float(channel_entry), 5),
            "channel_position": round(float(channel_position), 3),
            "quality": quality,
            "upper": round(float(upper_channel.iloc[-1]), 5),
            "lower": round(float(lower_channel.iloc[-1]), 5),
            "ema": round(float(ema_now), 5),
        }
    except:
        return {"channel_entry": None, "channel_position": 0.5, "quality": "UNKNOWN"}


# ==============================================================================
# V23 ENGINE #1: MARKET STRUCTURE — HH/HL, BOS, CHoCH
# ==============================================================================

def detect_market_structure(df, lookback=50):
    """Detecta Higher Highs/Lower Lows, Break of Structure, Change of Character."""
    try:
        if len(df) < lookback:
            return {"trend": "UNKNOWN", "strength": 0, "bos": False, "choch": False,
                    "hh_count": 0, "ll_count": 0, "last_event": "NONE"}
        d = df.tail(lookback)
        swing_h = d[d['swing_high']]['high'].values if 'swing_high' in d.columns else np.array([])
        swing_l = d[d['swing_low']]['low'].values if 'swing_low' in d.columns else np.array([])
        if len(swing_h) < 3 or len(swing_l) < 3:
            return {"trend": "UNCLEAR", "strength": 0, "bos": False, "choch": False,
                    "hh_count": 0, "ll_count": 0, "last_event": "NONE"}
        # Count HH/HL and LL/LH
        hh, hl, ll, lh = 0, 0, 0, 0
        for i in range(1, min(len(swing_h), 5)):
            if swing_h[-(i)] > swing_h[-(i+1)]: hh += 1
            else: lh += 1
        for i in range(1, min(len(swing_l), 5)):
            if swing_l[-(i)] > swing_l[-(i+1)]: hl += 1
            else: ll += 1
        # Determine structure
        bullish_struct = hh >= 2 and hl >= 2
        bearish_struct = ll >= 2 and lh >= 2
        # BOS = Break of Structure (continuation)
        bos = False
        last_event = "NONE"
        if len(swing_h) >= 2 and len(swing_l) >= 2:
            price_now = float(d['close'].iloc[-1])
            if bullish_struct and price_now > swing_h[-2]:
                bos = True; last_event = "BOS_BULL"
            elif bearish_struct and price_now < swing_l[-2]:
                bos = True; last_event = "BOS_BEAR"
        # CHoCH = Change of Character (reversal signal)
        choch = False
        if len(swing_h) >= 3 and len(swing_l) >= 3:
            # Bullish CHoCH: was making LL but now broke above last LH
            if ll >= 2 and swing_h[-1] > swing_h[-2]:
                choch = True; last_event = "CHOCH_BULL"
            # Bearish CHoCH: was making HH but now broke below last HL
            elif hh >= 2 and swing_l[-1] < swing_l[-2]:
                choch = True; last_event = "CHOCH_BEAR"
        strength = min(100, (hh + hl) * 15) if bullish_struct else min(100, (ll + lh) * 15) if bearish_struct else 0
        trend = "BULLISH" if bullish_struct else "BEARISH" if bearish_struct else "RANGING"
        return {"trend": trend, "strength": strength, "bos": bos, "choch": choch,
                "hh_count": hh, "hl_count": hl, "ll_count": ll, "lh_count": lh,
                "last_event": last_event}
    except:
        return {"trend": "UNKNOWN", "strength": 0, "bos": False, "choch": False,
                "hh_count": 0, "ll_count": 0, "last_event": "NONE"}

# ==============================================================================
# V23 ENGINE #2: MULTI-SPEED BIAS (Fast + Medium + Slow)
# ==============================================================================

def calculate_multi_speed_bias(h4, h1, m15, m5=None):
    """Bias com 3 velocidades: Fast(M15) 30%, Medium(H1) 40%, Slow(H4) 30%.
    Detecta reversões ANTES do H4 virar."""
    try:
        # FAST BIAS (M15 + M5) — reage em 15-30 min
        fast_sc = 0.0
        cm = m15.iloc[-1]
        if cm['EMA_20'] > cm['EMA_50']: fast_sc += 15
        elif cm['EMA_20'] < cm['EMA_50']: fast_sc -= 15
        if cm['MACD_hist'] > 0: fast_sc += 10
        elif cm['MACD_hist'] < 0: fast_sc -= 10
        if len(m15) >= 3:
            macd_acc = m15['MACD_hist'].iloc[-1] - m15['MACD_hist'].iloc[-2]
            fast_sc += max(-10, min(10, macd_acc * 100))
        if m5 is not None and len(m5) > 5:
            c5 = m5.iloc[-1]
            if c5['close'] > c5['EMA_20']: fast_sc += 5
            elif c5['close'] < c5['EMA_20']: fast_sc -= 5

        # MEDIUM BIAS (H1) — confirma em 1-2h
        med_sc = 0.0
        c1 = h1.iloc[-1]
        if c1['ATR'] > 0:
            dist_ema = (c1['close'] - c1['EMA_200']) / c1['ATR']
            med_sc += max(-20, min(20, dist_ema * 5))
        if c1['EMA_20'] > c1['EMA_50'] > c1['EMA_200']: med_sc += 20
        elif c1['EMA_20'] < c1['EMA_50'] < c1['EMA_200']: med_sc -= 20
        elif c1['EMA_20'] > c1['EMA_50']: med_sc += 8
        elif c1['EMA_20'] < c1['EMA_50']: med_sc -= 8
        rsi1 = c1.get('RSI', 50)
        if pd.notna(rsi1):
            if rsi1 > 60: med_sc += 5
            elif rsi1 < 40: med_sc -= 5

        # SLOW BIAS (H4) — fundo
        slow_sc = 0.0
        c4 = h4.iloc[-1]
        if c4['EMA_20'] > c4['EMA_50'] > c4['EMA_200']: slow_sc += 25
        elif c4['EMA_20'] < c4['EMA_50'] < c4['EMA_200']: slow_sc -= 25
        elif c4['EMA_20'] > c4['EMA_50']: slow_sc += 10
        elif c4['EMA_20'] < c4['EMA_50']: slow_sc -= 10
        if len(h4) >= 3:
            hn = h4['MACD_hist'].iloc[-1]; hp = h4['MACD_hist'].iloc[-2]
            if hn > hp: slow_sc += 8
            elif hn < hp: slow_sc -= 8

        # WEIGHTED COMBINATION
        total = fast_sc * 0.30 + med_sc * 0.40 + slow_sc * 0.30
        if total > 12: bias = "BULLISH"
        elif total < -12: bias = "BEARISH"
        else: bias = "NEUTRAL"
        conf = min(abs(total), 60) / 60 * 100

        # EARLY REVERSAL detection
        early_reversal = False
        reversal_dir = None
        fast_dir = "BULL" if fast_sc > 10 else "BEAR" if fast_sc < -10 else "NEUTRAL"
        med_dir = "BULL" if med_sc > 10 else "BEAR" if med_sc < -10 else "NEUTRAL"
        slow_dir = "BULL" if slow_sc > 10 else "BEAR" if slow_sc < -10 else "NEUTRAL"
        if fast_dir == med_dir and fast_dir != slow_dir and fast_dir != "NEUTRAL":
            early_reversal = True
            reversal_dir = "BULLISH" if fast_dir == "BULL" else "BEARISH"

        return bias, round(float(conf), 1), round(float(total), 1), early_reversal, reversal_dir
    except:
        return "NEUTRAL", 0.0, 0.0, False, None

# ==============================================================================
# V23 ENGINE #3: CANDLE MOMENTUM ENGINE
# ==============================================================================

def candle_momentum_engine(df, direction, lookback=10):
    """Analisa qualidade dos candles para confirmação de momentum."""
    try:
        if len(df) < lookback + 5:
            return {"score": 0, "conviction": "NONE", "avg_body_ratio": 0}
        d = df.tail(lookback)
        bodies = abs(d['close'] - d['open'])
        ranges = d['high'] - d['low']
        ranges = ranges.replace(0, np.nan)
        body_ratios = (bodies / ranges).dropna()
        is_bull = direction == "BULLISH"
        # 1. Body ratio (conviction candles)
        avg_br = float(body_ratios.mean()) if len(body_ratios) > 0 else 0.3
        br_score = min(30, avg_br * 40)
        # 2. Directional candles (% of candles in our direction)
        if is_bull:
            dir_count = (d['close'] > d['open']).sum()
        else:
            dir_count = (d['close'] < d['open']).sum()
        dir_pct = dir_count / len(d)
        dir_score = min(30, dir_pct * 40)
        # 3. Candle size trend (increasing = momentum building)
        if len(bodies) >= 5:
            recent = bodies.iloc[-3:].mean()
            older = bodies.iloc[:3].mean()
            size_ratio = recent / older if older > 0 else 1
            size_score = min(20, max(0, (size_ratio - 0.8) * 40))
        else:
            size_score = 0
        # 4. Rejection wicks (wicks against direction = confirmation)
        wick_score = 0
        for i in range(-3, 0):
            row = d.iloc[i]
            rng = row['high'] - row['low']
            if rng == 0: continue
            if is_bull:
                lower_wick = min(row['open'], row['close']) - row['low']
                if lower_wick / rng > 0.5: wick_score += 7
            else:
                upper_wick = row['high'] - max(row['open'], row['close'])
                if upper_wick / rng > 0.5: wick_score += 7
        wick_score = min(20, wick_score)
        total = br_score + dir_score + size_score + wick_score
        conviction = "STRONG" if total > 65 else "MODERATE" if total > 40 else "WEAK" if total > 20 else "NONE"
        return {"score": round(total, 1), "conviction": conviction, "avg_body_ratio": round(avg_br, 3),
                "directional_pct": round(dir_pct, 2), "size_trend": round(size_score, 1)}
    except:
        return {"score": 0, "conviction": "NONE", "avg_body_ratio": 0}

# ==============================================================================
# V23 ENGINE #4: PULLBACK QUALITY SCORE
# ==============================================================================

def pullback_quality_score(df, direction, atr):
    """Avalia qualidade do pullback: depth, tempo, volume, rejection."""
    try:
        if len(df) < 20 or atr == 0:
            return {"score": 0, "quality": "NONE", "depth_pct": 0}
        is_bull = direction == "BULLISH"
        d = df.tail(30)
        # Find last impulse (biggest move in direction)
        if is_bull:
            impulse_high = d['high'].max()
            impulse_low = d['low'].iloc[:15].min()
            impulse_size = impulse_high - impulse_low
            current = float(d['close'].iloc[-1])
            retracement = impulse_high - current
        else:
            impulse_low = d['low'].min()
            impulse_high = d['high'].iloc[:15].max()
            impulse_size = impulse_high - impulse_low
            current = float(d['close'].iloc[-1])
            retracement = current - impulse_low
        if impulse_size == 0: return {"score": 0, "quality": "NONE", "depth_pct": 0}
        depth_pct = retracement / impulse_size
        # 1. Depth score (30-62% = excellent, fibonacci zone)
        if 0.30 <= depth_pct <= 0.62:
            depth_sc = 30
        elif 0.20 <= depth_pct <= 0.75:
            depth_sc = 15
        elif depth_pct < 0.15:
            depth_sc = 5   # Too shallow
        else:
            depth_sc = 0   # Too deep, trend may be broken
        # 2. Time (3-8 candles = ideal)
        # Count candles since the impulse extreme
        if is_bull:
            peak_idx = d['high'].idxmax()
        else:
            peak_idx = d['low'].idxmin()
        if peak_idx in d.index:
            pb_candles = len(d.loc[peak_idx:]) - 1
        else:
            pb_candles = 5
        if 3 <= pb_candles <= 8:
            time_sc = 25
        elif 2 <= pb_candles <= 12:
            time_sc = 15
        else:
            time_sc = 5
        # 3. Candle size decreasing in pullback (volume proxy)
        last_5 = d.tail(5)
        ranges = (last_5['high'] - last_5['low']).values
        if len(ranges) >= 3:
            decreasing = all(ranges[i] >= ranges[i+1] * 0.8 for i in range(len(ranges)-2, len(ranges)-1))
            vol_sc = 20 if decreasing else 8
        else:
            vol_sc = 10
        # 4. Rejection candle at end (pin bar, engulfing)
        last = d.iloc[-1]
        prev = d.iloc[-2] if len(d) > 1 else last
        rng = last['high'] - last['low']
        reject_sc = 0
        if rng > 0:
            if is_bull:
                lower_wick = min(last['open'], last['close']) - last['low']
                if lower_wick / rng > 0.6 and last['close'] > last['open']:
                    reject_sc = 25  # Pin bar rejection
                elif last['close'] > last['open'] and abs(last['close'] - last['open']) > abs(prev['close'] - prev['open']) * 1.3:
                    reject_sc = 20  # Bullish engulfing
                elif last['close'] > last['open']:
                    reject_sc = 10  # Normal bullish
            else:
                upper_wick = last['high'] - max(last['open'], last['close'])
                if upper_wick / rng > 0.6 and last['close'] < last['open']:
                    reject_sc = 25
                elif last['close'] < last['open'] and abs(last['close'] - last['open']) > abs(prev['close'] - prev['open']) * 1.3:
                    reject_sc = 20
                elif last['close'] < last['open']:
                    reject_sc = 10
        total = depth_sc + time_sc + vol_sc + reject_sc
        quality = "EXCELLENT" if total >= 70 else "GOOD" if total >= 50 else "MODERATE" if total >= 30 else "WEAK"
        return {"score": round(total, 1), "quality": quality, "depth_pct": round(depth_pct, 3),
                "pb_candles": pb_candles, "rejection": reject_sc > 15}
    except:
        return {"score": 0, "quality": "NONE", "depth_pct": 0}

# ==============================================================================
# V23 ENGINE #5: LIQUIDITY SWEEP DETECTOR
# ==============================================================================

def detect_liquidity_sweep(df, atr):
    """Detecta sweeps de liquidez em swing points."""
    try:
        if len(df) < 30 or atr == 0:
            return {"sweep": False, "type": "NONE", "level": 0}
        d = df.tail(40)
        sh = d[d['swing_high']]['high'] if 'swing_high' in d.columns else pd.Series(dtype=float)
        sl = d[d['swing_low']]['low'] if 'swing_low' in d.columns else pd.Series(dtype=float)
        last = d.iloc[-1]
        threshold = atr * 0.4  # Sweep = ultrapassa por menos de 0.4× ATR
        # Check bull sweep (price dipped below swing low then closed above)
        if len(sl) >= 2:
            recent_low = sl.iloc[-1]
            if last['low'] < recent_low - 0.01 and last['close'] > recent_low and (recent_low - last['low']) < threshold:
                return {"sweep": True, "type": "BULL_SWEEP", "level": round(float(recent_low), 5),
                        "overshoot": round(float(recent_low - last['low']), 5)}
        # Check bear sweep (price spiked above swing high then closed below)
        if len(sh) >= 2:
            recent_high = sh.iloc[-1]
            if last['high'] > recent_high + 0.01 and last['close'] < recent_high and (last['high'] - recent_high) < threshold:
                return {"sweep": True, "type": "BEAR_SWEEP", "level": round(float(recent_high), 5),
                        "overshoot": round(float(last['high'] - recent_high), 5)}
        return {"sweep": False, "type": "NONE", "level": 0}
    except:
        return {"sweep": False, "type": "NONE", "level": 0}

# ==============================================================================
# V23 ENGINE #6: ENTRY SYNC SCORE (Multi-TF alignment at entry moment)
# ==============================================================================

def entry_sync_score(h4, h1, m15, m5, direction):
    """Verifica se TODOS os timeframes estão alinhados NO MOMENTO da entrada."""
    try:
        is_bull = direction == "BULLISH"
        total = 0
        # H4 bias aligned (30 points)
        c4 = h4.iloc[-1]
        if is_bull:
            if c4['close'] > c4['EMA_200'] and c4['MACD_hist'] > 0: total += 30
            elif c4['close'] > c4['EMA_200']: total += 15
        else:
            if c4['close'] < c4['EMA_200'] and c4['MACD_hist'] < 0: total += 30
            elif c4['close'] < c4['EMA_200']: total += 15
        # H1 momentum aligned (25 points)
        c1 = h1.iloc[-1]
        if is_bull:
            if c1['MACD_hist'] > 0 and c1['close'] > c1['EMA_20']: total += 25
            elif c1['MACD_hist'] > 0 or c1['close'] > c1['EMA_20']: total += 12
        else:
            if c1['MACD_hist'] < 0 and c1['close'] < c1['EMA_20']: total += 25
            elif c1['MACD_hist'] < 0 or c1['close'] < c1['EMA_20']: total += 12
        # M15 candle confirming (25 points)
        cm = m15.iloc[-1]
        if is_bull:
            if cm['close'] > cm['open'] and cm['close'] > cm['EMA_20']: total += 25
            elif cm['close'] > cm['open']: total += 12
        else:
            if cm['close'] < cm['open'] and cm['close'] < cm['EMA_20']: total += 25
            elif cm['close'] < cm['open']: total += 12
        # M5 trigger (20 points)
        if m5 is not None and len(m5) > 3:
            c5 = m5.iloc[-1]
            if is_bull:
                if c5['close'] > c5['open'] and c5['close'] > c5['EMA_20']: total += 20
                elif c5['close'] > c5['open']: total += 10
            else:
                if c5['close'] < c5['open'] and c5['close'] < c5['EMA_20']: total += 20
                elif c5['close'] < c5['open']: total += 10
        ready = "READY" if total >= 60 else "ALMOST" if total >= 40 else "WAIT"
        return {"score": total, "ready": ready}
    except:
        return {"score": 0, "ready": "WAIT"}

# ==============================================================================
# V23 ENGINE #7: BREAKOUT RETEST DETECTOR
# ==============================================================================

def detect_breakout_retest(df, sr_levels, direction, atr):
    """Detecta quando preço retesta um nível S/R quebrado."""
    try:
        if not sr_levels or len(df) < 10 or atr == 0:
            return {"retest": False, "level": None, "quality": "NONE"}
        is_bull = direction == "BULLISH"
        price = float(df['close'].iloc[-1])
        for sr in sr_levels[:5]:
            lvl = sr['price']
            dist = abs(price - lvl) / atr
            # Price is near the level (within 0.5 ATR)
            if dist < 0.5:
                # Check if it was broken recently (price was on other side 5-15 bars ago)
                lookback_prices = df['close'].iloc[-15:-3]
                if is_bull:
                    # For bull retest: price should have been BELOW level, now ABOVE
                    was_below = (lookback_prices < lvl).any()
                    now_above = price > lvl
                    if was_below and now_above:
                        return {"retest": True, "level": lvl, "quality": "GOOD",
                                "type": "SUPPORT_RETEST", "distance_atr": round(dist, 2)}
                else:
                    was_above = (lookback_prices > lvl).any()
                    now_below = price < lvl
                    if was_above and now_below:
                        return {"retest": True, "level": lvl, "quality": "GOOD",
                                "type": "RESISTANCE_RETEST", "distance_atr": round(dist, 2)}
        return {"retest": False, "level": None, "quality": "NONE"}
    except:
        return {"retest": False, "level": None, "quality": "NONE"}

# ==============================================================================
# V23 ENGINE #8: CONTINUATION PATTERNS (Flag, Pennant)
# ==============================================================================

def detect_continuation_pattern(df, direction, atr):
    """Detecta flags e pennants — padrões de continuação de alta probabilidade."""
    try:
        if len(df) < 20 or atr == 0:
            return {"pattern": "NONE", "confidence": 0}
        is_bull = direction == "BULLISH"
        d = df.tail(25)
        # Look for impulse followed by consolidation
        # Impulse: large move in direction (>2 ATR in 3-5 candles)
        for start in range(0, min(10, len(d)-10)):
            segment = d.iloc[start:start+5]
            move = float(segment['close'].iloc[-1] - segment['open'].iloc[0])
            if is_bull and move > atr * 2:
                # Found bullish impulse, check for flag after
                flag = d.iloc[start+5:]
                if len(flag) >= 3:
                    flag_range = float(flag['high'].max() - flag['low'].min())
                    flag_drift = float(flag['close'].iloc[-1] - flag['open'].iloc[0])
                    # Flag: tight range, slight counter-trend drift
                    if flag_range < atr * 2 and flag_drift < 0:
                        return {"pattern": "BULL_FLAG", "confidence": min(80, 50 + int(move/atr * 10)),
                                "impulse_size": round(move, 5), "flag_range": round(flag_range, 5)}
                    # Pennant: decreasing range
                    elif flag_range < atr * 1.5:
                        return {"pattern": "BULL_PENNANT", "confidence": min(70, 40 + int(move/atr * 10)),
                                "impulse_size": round(move, 5)}
            elif not is_bull and move < -atr * 2:
                flag = d.iloc[start+5:]
                if len(flag) >= 3:
                    flag_range = float(flag['high'].max() - flag['low'].min())
                    flag_drift = float(flag['close'].iloc[-1] - flag['open'].iloc[0])
                    if flag_range < atr * 2 and flag_drift > 0:
                        return {"pattern": "BEAR_FLAG", "confidence": min(80, 50 + int(abs(move)/atr * 10)),
                                "impulse_size": round(abs(move), 5), "flag_range": round(flag_range, 5)}
                    elif flag_range < atr * 1.5:
                        return {"pattern": "BEAR_PENNANT", "confidence": min(70, 40 + int(abs(move)/atr * 10)),
                                "impulse_size": round(abs(move), 5)}
        return {"pattern": "NONE", "confidence": 0}
    except:
        return {"pattern": "NONE", "confidence": 0}

# ==============================================================================
# BC ENGINE #1: SPIKE DETECTION — Detecta spikes iminentes
# ==============================================================================

# ==============================================================================
# V24-BC FIX #6 + M2: CLEAN ATR — Median ATR excluding spikes
# ==============================================================================

def bc_clean_atr(df, profile, lookback=50):
    """Calcula ATR limpo (mediano) excluindo candles de spike.
    Em Boom/Crash o ATR padrão é distorcido pelos spikes —
    um único spike de 500pts infla o ATR e torna thresholds frouxos."""
    try:
        if len(df) < lookback + 5:
            return float(df['ATR'].iloc[-1]) if 'ATR' in df.columns else 1.0
        d = df.tail(lookback)
        ranges = (d['high'] - d['low']).values
        if len(ranges) < 10:
            return float(d['ATR'].iloc[-1])
        # Median range = robust to spike outliers
        median_range = float(np.median(ranges))
        # Also filter out spikes: keep only candles where range < 2× median
        clean_mask = ranges < (2.0 * median_range)
        if clean_mask.sum() < 10:
            return median_range  # Too few clean candles, use median
        clean_atr = float(np.mean(ranges[clean_mask]))
        return max(clean_atr, median_range * 0.5)  # Floor at 50% median
    except:
        return float(df['ATR'].iloc[-1]) if 'ATR' in df.columns and len(df) > 0 else 1.0

# ==============================================================================
# V24-BC M4: SPIKE DETECTION VIA RETURNS DISTRIBUTION (Kurtosis)
# ==============================================================================

def bc_returns_kurtosis(df, lookback=50):
    """Analisa curtose dos retornos recentes para detectar regime de spike.
    Kurtosis alta (>5) = distribuição fat-tailed = spikes frequentes."""
    try:
        if len(df) < lookback + 5:
            return {"kurtosis": 3.0, "regime": "NORMAL", "spike_prone": False}
        rets = df['close'].pct_change().dropna().tail(lookback)
        if len(rets) < 20:
            return {"kurtosis": 3.0, "regime": "NORMAL", "spike_prone": False}
        kurt = float(rets.kurtosis())
        skew = float(rets.skew())
        if kurt > 8:
            regime = "EXTREME_SPIKE"
        elif kurt > 5:
            regime = "SPIKE_PRONE"
        elif kurt > 3.5:
            regime = "MODERATE"
        else:
            regime = "NORMAL"
        return {"kurtosis": round(kurt, 2), "skewness": round(skew, 2),
                "regime": regime, "spike_prone": kurt > 5}
    except:
        return {"kurtosis": 3.0, "regime": "NORMAL", "spike_prone": False}

# ==============================================================================
# V24-BC M5: BC REGIME CLASSIFIER
# ==============================================================================

def bc_regime_classifier(df, profile, bc_spike_data, bc_drift_data, bc_freq_data, lookback=30):
    """Classifica regime BC: DRIFT_SMOOTH, CHOPPY, PRE_SPIKE, POST_SPIKE, SPIKE_CLUSTER.
    Usado para adaptar SL, TP, e scoring."""
    try:
        regime = "DRIFT_SMOOTH"  # default
        # Post-spike: last spike very recent (0-3 candles)
        if bc_freq_data.get('last_spike_ago', 999) <= 3:
            regime = "POST_SPIKE"
        # Pre-spike: overdue + extreme RSI + long drift
        elif (bc_spike_data.get('probability', 0) >= 55 and
              bc_freq_data.get('overdue', False)):
            regime = "PRE_SPIKE"
        # Spike cluster: multiple spikes recently
        elif bc_freq_data.get('spike_count', 0) >= 3 and bc_freq_data.get('avg_interval', 999) < 8:
            regime = "SPIKE_CLUSTER"
        # Choppy: drift weak + quality poor
        elif bc_drift_data.get('quality') == "CHOPPY" or bc_drift_data.get('strength', 0) < 30:
            regime = "CHOPPY"
        # Drift smooth: default when drift active + quality good
        elif bc_drift_data.get('safe_to_ride') and bc_drift_data.get('quality') in ["SMOOTH", "MODERATE"]:
            regime = "DRIFT_SMOOTH"

        # SL multipliers by regime (M5: Regime-Aware SL)
        sl_mults = {
            "DRIFT_SMOOTH": 0.8,   # Tight SL — predictable
            "CHOPPY": 1.0,         # Normal SL
            "PRE_SPIKE": 1.3,      # Wider SL — spike imminent, noise
            "POST_SPIKE": 1.5,     # Widest SL — high vol after spike
            "SPIKE_CLUSTER": 1.6,  # Very wide — unpredictable clusters
        }
        return {"regime": regime, "sl_mult": sl_mults.get(regime, 1.0)}
    except:
        return {"regime": "UNKNOWN", "sl_mult": 1.0}

# ==============================================================================
# V24-BC O3: ENGINE CONFLICT RESOLUTION
# ==============================================================================

def bc_resolve_engine_conflicts(bc_spike, bc_drift, bc_fade, bc_multi, bc_absorb):
    """Resolve conflitos entre engines BC ANTES do scoring.
    Ex: spike diz 'spike iminente UP' mas drift diz 'drift DOWN safe'
    → conflito → desabilitar drift ride."""
    conflicts = []
    resolved_actions = {"allow_spike_catch": True, "allow_drift_ride": True,
                        "allow_fade": True, "conflict_penalty": 0}
    try:
        # Conflito 1: Spike iminente + Drift ativo = não fazer drift ride
        if bc_spike.get('spike_imminent') and bc_drift.get('safe_to_ride'):
            conflicts.append("SPIKE_vs_DRIFT")
            resolved_actions["allow_drift_ride"] = False
            resolved_actions["conflict_penalty"] += 5  # Score penalty

        # Conflito 2: Fade ativo + Multi-spike cluster = não fazer fade (pode continuar)
        if bc_fade.get('post_spike') and bc_multi.get('cluster'):
            conflicts.append("FADE_vs_CLUSTER")
            resolved_actions["allow_fade"] = False
            resolved_actions["conflict_penalty"] += 8

        # Conflito 3: Spike catch + Absorption detector diz absorção contrária
        if bc_spike.get('spike_imminent') and bc_absorb.get('absorption'):
            spike_type = bc_spike.get('type', '')
            absorb_type = bc_absorb.get('type', '')
            if ('UP' in spike_type and 'BEAR' in absorb_type) or \
               ('DOWN' in spike_type and 'BULL' in absorb_type):
                conflicts.append("SPIKE_vs_ABSORPTION")
                resolved_actions["allow_spike_catch"] = False
                resolved_actions["conflict_penalty"] += 10

        resolved_actions["conflicts"] = conflicts
        resolved_actions["has_conflict"] = len(conflicts) > 0
        return resolved_actions
    except:
        return resolved_actions

# ==============================================================================
# V24-BC O5: ANTI-MELTDOWN KILL-SWITCH
# ==============================================================================

def bc_meltdown_check(session_state_key='bc_loss_streak'):
    """Kill-switch: se 3+ losses consecutivos, aumenta score mínimo.
    Se 5+ losses, bloqueia sinais até reset manual."""
    try:
        streak = st.session_state.get(session_state_key, 0)
        if streak >= 5:
            return {"blocked": True, "reason": f"KILL-SWITCH: {streak} consecutive losses — manual reset required",
                    "score_boost": 0, "streak": streak}
        elif streak >= 3:
            return {"blocked": False, "reason": f"CAUTION: {streak} consecutive losses — score +50%",
                    "score_boost": 50, "streak": streak}  # +50% score requirement
        return {"blocked": False, "reason": None, "score_boost": 0, "streak": streak}
    except:
        return {"blocked": False, "reason": None, "score_boost": 0, "streak": 0}

# ==============================================================================
# V24-BC A3: EXPLICIT EXPECTANCY + STRESS TEST
# ==============================================================================

def calculate_expectancy(wr, avg_win, avg_loss, stress_wr_reduction=0.20):
    """Calcula expectância real e estressada (-20% WR).
    Se expectancy_stressed < 0, setup é alto risco."""
    try:
        p = wr / 100.0
        q = 1 - p
        expectancy = p * avg_win - q * avg_loss
        # Stress test: reduz WR em 20%
        p_stressed = max(0.05, p - stress_wr_reduction)
        q_stressed = 1 - p_stressed
        expectancy_stressed = p_stressed * avg_win - q_stressed * avg_loss
        return {
            "expectancy": round(expectancy, 4),
            "expectancy_stressed": round(expectancy_stressed, 4),
            "high_risk": expectancy_stressed < 0,
            "expectancy_per_trade_R": round(expectancy / avg_loss, 2) if avg_loss > 0 else 0
        }
    except:
        return {"expectancy": 0, "expectancy_stressed": -1, "high_risk": True, "expectancy_per_trade_R": 0}

# ==============================================================================
# V24-BC A4: POISSON SPIKE TIMING MODEL
# ==============================================================================

def bc_poisson_spike_probability(candles_since_last, avg_interval, spike_count=0):
    """Modela tempo entre spikes como processo Poisson (distribuição exponencial).
    Mais preciso que soma aditiva para probabilidade de spike."""
    try:
        if avg_interval <= 0:
            return 0.0
        # Taxa (lambda) = 1/avg_interval
        rate = 1.0 / avg_interval
        # P(spike nos próximos k candles | já esperou t candles)
        # Para exponencial: P(T<=t+k|T>t) = 1-exp(-lambda*k) (memoryless)
        # Mas empiricamente spikes NÃO são perfeitamente memoryless,
        # então usamos renewal process: hazard rate increases with time
        # Weibull com shape > 1 (increasing hazard)
        shape = 1.3  # > 1 = hazard increases over time (spikes more likely when overdue)
        # P(spike no próximo candle | esperou t candles)
        hazard = shape * rate * (candles_since_last * rate) ** (shape - 1)
        prob = 1 - np.exp(-hazard)
        return round(min(0.95, max(0.0, float(prob))), 3)
    except:
        return 0.0

def bc_spike_detector(df, profile, lookback=30):
    """V24: Detecta condições de spike iminente em Boom/Crash.
    FIX #2: Usa intervalo empírico M15 (não ticks/15)
    FIX #4: Probabilidade com desconto por correlação + modelo Poisson
    FIX #6: Usa clean ATR em vez de ATR padrão
    Boom: RSI extremo baixo + drift prolongado = spike UP iminente
    Crash: RSI extremo alto + drift prolongado = crash DOWN iminente"""
    try:
        if len(df) < lookback + 5:
            return {"spike_imminent": False, "probability": 0, "type": "NONE",
                    "candles_since_last": 999, "rsi_zone": "NEUTRAL"}
        is_boom = profile.get('gen_type') == 'BOOM'
        d = df.tail(lookback)
        rsi = d['RSI'].iloc[-1] if pd.notna(d['RSI'].iloc[-1]) else 50
        atr = d['ATR'].iloc[-1]
        # Spike history: count candles since last spike
        spike_min = profile.get('spike_size_min_atr', 2.0)
        candles_since = 0
        for i in range(len(d)-1, 0, -1):
            move = abs(d['close'].iloc[i] - d['close'].iloc[i-1])
            if atr > 0 and move > spike_min * atr:
                break
            candles_since += 1
        # RSI zone analysis
        rsi_buy = profile.get('rsi_spike_buy', 30)
        rsi_sell = profile.get('rsi_spike_sell', 70)
        rsi_ext_buy = profile.get('rsi_extreme_buy', 20)
        rsi_ext_sell = profile.get('rsi_extreme_sell', 80)
        if rsi <= rsi_ext_buy: rsi_zone = "EXTREME_LOW"
        elif rsi <= rsi_buy: rsi_zone = "LOW"
        elif rsi >= rsi_ext_sell: rsi_zone = "EXTREME_HIGH"
        elif rsi >= rsi_sell: rsi_zone = "HIGH"
        else: rsi_zone = "NEUTRAL"
        # Drift measurement (how many consecutive candles in drift direction)
        drift_count = 0
        if is_boom:  # Boom drifts DOWN
            for i in range(len(d)-1, max(0, len(d)-20), -1):
                if d['close'].iloc[i] < d['open'].iloc[i]: drift_count += 1
                else: break
        else:  # Crash drifts UP
            for i in range(len(d)-1, max(0, len(d)-20), -1):
                if d['close'].iloc[i] > d['open'].iloc[i]: drift_count += 1
                else: break
        # Probability calculation — V24: with correlation discount + Poisson timing
        prob = 0
        rsi_active = False
        drift_active = False
        if is_boom:
            if rsi_zone == "EXTREME_LOW": prob += 35; rsi_active = True
            elif rsi_zone == "LOW": prob += 20; rsi_active = True
            if drift_count >= 8: prob += 25; drift_active = True
            elif drift_count >= 5: prob += 15; drift_active = True
            elif drift_count >= 3: prob += 8; drift_active = True
        else:
            if rsi_zone == "EXTREME_HIGH": prob += 35; rsi_active = True
            elif rsi_zone == "HIGH": prob += 20; rsi_active = True
            if drift_count >= 8: prob += 25; drift_active = True
            elif drift_count >= 5: prob += 15; drift_active = True
            elif drift_count >= 3: prob += 8; drift_active = True

        # V24 FIX #4: Correlation discount — RSI + drift are correlated
        # (prolonged drift → extreme RSI), so additive sum inflates probability
        if rsi_active and drift_active:
            prob = int(prob * 0.70)  # 30% discount for correlation

        # V24 FIX #2: Empirical spike timing (NOT ticks/15)
        # Instead of converting spike_avg_ticks by dividing by 15,
        # use empirical average interval from actual spike positions in M15 data
        empirical_intervals = []
        spike_positions = []
        for i in range(1, len(d)):
            move = d['close'].iloc[i] - d['close'].iloc[i-1]
            if is_boom and move > spike_min * atr and atr > 0:
                spike_positions.append(i)
            elif not is_boom and move < -spike_min * atr and atr > 0:
                spike_positions.append(i)
        if len(spike_positions) >= 2:
            empirical_intervals = [spike_positions[j+1] - spike_positions[j]
                                   for j in range(len(spike_positions)-1)]
            avg_m15_interval = np.mean(empirical_intervals)
        else:
            # Fallback: estimate from spike_freq profile (but NOT /15)
            # Boom 300 = ~2-5 M15 candles empirically, Boom 1000 = ~10-20 M15
            freq_map = {"HIGH": 4, "MEDIUM": 8, "LOW": 15}
            avg_m15_interval = freq_map.get(profile.get('spike_freq', 'MEDIUM'), 8)

        # V24 A4: Poisson timing model instead of additive
        poisson_prob = bc_poisson_spike_probability(candles_since, avg_m15_interval)
        # Scale Poisson to 0-25 range (same as old time factor max)
        time_bonus = int(poisson_prob * 25)
        prob += time_bonus
        # BB squeeze = compression before spike
        if 'BB_width' in d.columns and pd.notna(d['BB_width'].iloc[-1]):
            if d['BB_width'].iloc[-1] < d['BB_width'].rolling(20).mean().iloc[-1] * 0.7:
                prob += 10
        spike_type = "SPIKE_UP" if is_boom else "CRASH_DOWN"
        return {"spike_imminent": prob >= 45, "probability": min(95, prob),
                "type": spike_type, "candles_since_last": candles_since,
                "rsi_zone": rsi_zone, "drift_count": drift_count,
                "rsi_value": round(float(rsi), 1)}
    except:
        return {"spike_imminent": False, "probability": 0, "type": "NONE",
                "candles_since_last": 999, "rsi_zone": "NEUTRAL"}

# ==============================================================================
# BC ENGINE #2: DRIFT TRADING — Lucra com o drift natural
# ==============================================================================

def bc_drift_analyzer(df, profile, lookback=20):
    """Analisa força do drift para trading com o fluxo natural.
    Boom: drift DOWN = SELL | Crash: drift UP = BUY"""
    try:
        if len(df) < lookback + 5:
            return {"drift_active": False, "strength": 0, "direction": "NONE",
                    "quality": "NONE", "safe_to_ride": False}
        is_boom = profile.get('gen_type') == 'BOOM'
        d = df.tail(lookback)
        ema_f = d['close'].ewm(span=profile.get('drift_ema_fast', 5)).mean()
        ema_s = d['close'].ewm(span=profile.get('drift_ema_slow', 15)).mean()
        # Drift direction
        if is_boom:
            drift_active = ema_f.iloc[-1] < ema_s.iloc[-1]  # Fast below slow = drift DOWN
            drift_dir = "DOWN"
            # V24 FIX #7: Combine count + magnitude for strength
            bearish_candles = (d['close'] < d['open']).sum()
            count_score = min(100, int(bearish_candles / len(d) * 130))
            # Magnitude: total directional move vs average candle body
            directional_move = abs(float(d['close'].iloc[-1] - d['close'].iloc[0]))
            avg_candle_body = abs(d['close'] - d['open']).mean()
            if avg_candle_body > 0 and len(d) > 0:
                magnitude_score = min(100, int(directional_move / (avg_candle_body * len(d)) * 100))
            else:
                magnitude_score = 0
            strength = int(count_score * 0.4 + magnitude_score * 0.6)
        else:
            drift_active = ema_f.iloc[-1] > ema_s.iloc[-1]  # Fast above slow = drift UP
            drift_dir = "UP"
            bullish_candles = (d['close'] > d['open']).sum()
            count_score = min(100, int(bullish_candles / len(d) * 130))
            directional_move = abs(float(d['close'].iloc[-1] - d['close'].iloc[0]))
            avg_candle_body = abs(d['close'] - d['open']).mean()
            if avg_candle_body > 0 and len(d) > 0:
                magnitude_score = min(100, int(directional_move / (avg_candle_body * len(d)) * 100))
            else:
                magnitude_score = 0
            strength = int(count_score * 0.4 + magnitude_score * 0.6)
        # Quality: smooth drift vs choppy
        bodies = abs(d['close'] - d['open'])
        ranges = d['high'] - d['low']
        ranges = ranges.replace(0, np.nan)
        body_ratio = (bodies / ranges).dropna().mean() if len(ranges.dropna()) > 0 else 0.3
        quality = "SMOOTH" if body_ratio > 0.55 else "MODERATE" if body_ratio > 0.35 else "CHOPPY"
        # Safe to ride: no spike imminent (RSI not extreme)
        rsi = d['RSI'].iloc[-1] if pd.notna(d['RSI'].iloc[-1]) else 50
        if is_boom:
            safe = rsi > 35  # If RSI still above 35, safe to sell (drift)
        else:
            safe = rsi < 65  # If RSI still below 65, safe to buy (drift)
        return {"drift_active": drift_active, "strength": strength,
                "direction": drift_dir, "quality": quality,
                "safe_to_ride": safe and drift_active,
                "body_ratio": round(float(body_ratio), 3),
                "rsi": round(float(rsi), 1)}
    except:
        return {"drift_active": False, "strength": 0, "direction": "NONE",
                "quality": "NONE", "safe_to_ride": False}

# ==============================================================================
# BC ENGINE #3: POST-SPIKE FADE — Trade após spike/crash
# ==============================================================================

def bc_post_spike_fade(df, profile, lookback=10, absorption_data=None):
    """V24: Detecta se um spike acabou de acontecer e calcula fade entry.
    FIX #8: Verifica absorção antes de confirmar fade (spike continuando = não fazer fade).
    Após spike UP em Boom → SELL (fade parcial)
    Após crash DOWN em Crash → BUY (fade parcial)"""
    try:
        if len(df) < lookback + 3:
            return {"post_spike": False, "fade_direction": "NONE",
                    "spike_size": 0, "fade_target": 0, "candles_ago": 999}
        d = df.tail(lookback)
        atr = d['ATR'].iloc[-1]
        # V24: Use clean ATR if available
        clean_atr = bc_clean_atr(df, profile, lookback=50)
        spike_min = profile.get('spike_size_min_atr', 2.0)
        is_boom = profile.get('gen_type') == 'BOOM'
        # Find most recent spike
        for i in range(len(d)-1, 0, -1):
            move = d['close'].iloc[i] - d['close'].iloc[i-1]
            abs_move = abs(move)
            if clean_atr > 0 and abs_move > spike_min * clean_atr:
                candles_ago = len(d) - 1 - i
                if candles_ago > 5: break  # Too old, not tradeable
                spike_size = abs_move

                # V24 FIX #8: Check absorption before confirming fade
                # If market is CONTINUING (not absorbing), don't fade
                if absorption_data and absorption_data.get('absorption'):
                    absorb_type = absorption_data.get('type', '')
                    if is_boom and move > 0:
                        # Spike UP — need BEAR_ABSORPTION to confirm fade
                        if absorb_type != 'BEAR_ABSORPTION':
                            # No absorption = spike may continue = skip fade
                            break
                    elif not is_boom and move < 0:
                        # Crash DOWN — need BULL_ABSORPTION to confirm fade
                        if absorb_type != 'BULL_ABSORPTION':
                            break
                else:
                    # V24: Even without absorption data, check post-spike candles
                    # If 2+ candles continue in spike direction, skip fade
                    continuation_count = 0
                    for j in range(i+1, min(i+4, len(d))):
                        post_move = d['close'].iloc[j] - d['close'].iloc[j-1] if j < len(d) else 0
                        if (is_boom and move > 0 and post_move > 0) or \
                           (not is_boom and move < 0 and post_move < 0):
                            continuation_count += 1
                    if continuation_count >= 2:
                        break  # Momentum continuation, not fade territory

                fade_pct = profile.get('post_spike_fade_pct', 0.35)
                if is_boom and move > 0:
                    # Spike UP just happened → SELL fade
                    fade_target = d['close'].iloc[i] - spike_size * fade_pct
                    return {"post_spike": True, "fade_direction": "SELL",
                            "spike_size": round(float(spike_size), 5),
                            "fade_target": round(float(fade_target), 5),
                            "candles_ago": candles_ago, "spike_candle_idx": i,
                            "absorption_confirmed": bool(absorption_data and absorption_data.get('absorption'))}
                elif not is_boom and move < 0:
                    # Crash DOWN just happened → BUY fade
                    fade_target = d['close'].iloc[i] + spike_size * fade_pct
                    return {"post_spike": True, "fade_direction": "BUY",
                            "spike_size": round(float(spike_size), 5),
                            "fade_target": round(float(fade_target), 5),
                            "candles_ago": candles_ago, "spike_candle_idx": i,
                            "absorption_confirmed": bool(absorption_data and absorption_data.get('absorption'))}
                break
        return {"post_spike": False, "fade_direction": "NONE",
                "spike_size": 0, "fade_target": 0, "candles_ago": 999}
    except:
        return {"post_spike": False, "fade_direction": "NONE",
                "spike_size": 0, "fade_target": 0, "candles_ago": 999}

# ==============================================================================
# BC ENGINE #4: SUPPLY/DEMAND ZONE DETECTION
# ==============================================================================

def bc_supply_demand_zones(df, atr, lookback=50):
    """Detecta zonas de Supply e Demand para Boom/Crash."""
    try:
        if len(df) < lookback or atr == 0:
            return {"zones": [], "nearest_demand": None, "nearest_supply": None}
        d = df.tail(lookback)
        price = float(d['close'].iloc[-1])
        zones = []
        # Find demand zones (strong rallies from a level)
        for i in range(2, len(d)-2):
            candles_ago = len(d) - 1 - i  # V24 FIX #9: track age
            # Demand: price dropped to low, then rallied sharply
            if d['low'].iloc[i] < d['low'].iloc[i-1] and d['low'].iloc[i] < d['low'].iloc[i+1]:
                rally = d['high'].iloc[i+1] - d['low'].iloc[i]
                if rally > atr * 1.5:
                    raw_strength = float(rally / atr)
                    # V24 FIX #9: Temporal decay — recent zones stronger
                    recency_factor = 1.0 - (candles_ago / lookback) * 0.7  # 1.0 → 0.3
                    zones.append({"type": "DEMAND", "price": round(float(d['low'].iloc[i]), 5),
                                  "strength": round(raw_strength * recency_factor, 1),
                                  "raw_strength": round(raw_strength, 1),
                                  "age": candles_ago})
            # Supply: price spiked to high, then dropped
            if d['high'].iloc[i] > d['high'].iloc[i-1] and d['high'].iloc[i] > d['high'].iloc[i+1]:
                drop = d['high'].iloc[i] - d['low'].iloc[i+1]
                if drop > atr * 1.5:
                    raw_strength = float(drop / atr)
                    recency_factor = 1.0 - (candles_ago / lookback) * 0.7
                    zones.append({"type": "SUPPLY", "price": round(float(d['high'].iloc[i]), 5),
                                  "strength": round(raw_strength * recency_factor, 1),
                                  "raw_strength": round(raw_strength, 1),
                                  "age": candles_ago})
        # Sort by strength
        zones.sort(key=lambda x: x['strength'], reverse=True)
        zones = zones[:8]
        # Find nearest
        demands = [z for z in zones if z['type'] == 'DEMAND' and z['price'] < price]
        supplies = [z for z in zones if z['type'] == 'SUPPLY' and z['price'] > price]
        nearest_d = min(demands, key=lambda x: price - x['price']) if demands else None
        nearest_s = min(supplies, key=lambda x: x['price'] - price) if supplies else None
        return {"zones": zones, "nearest_demand": nearest_d, "nearest_supply": nearest_s}
    except:
        return {"zones": [], "nearest_demand": None, "nearest_supply": None}

# ==============================================================================
# BC ENGINE #5: SPIKE FREQUENCY ANALYZER
# ==============================================================================

def bc_spike_frequency(df, profile, lookback=100):
    """Analisa frequência de spikes para timing."""
    try:
        if len(df) < lookback:
            return {"avg_interval": 0, "last_spike_ago": 999, "overdue": False,
                    "spike_count": 0, "next_spike_window": "UNKNOWN"}
        d = df.tail(lookback)
        atr = d['ATR'].mean()
        if atr == 0: return {"avg_interval": 0, "last_spike_ago": 999, "overdue": False}
        spike_min = profile.get('spike_size_min_atr', 2.0)
        is_boom = profile.get('gen_type') == 'BOOM'
        # Find all spikes
        spike_positions = []
        for i in range(1, len(d)):
            move = d['close'].iloc[i] - d['close'].iloc[i-1]
            if is_boom and move > spike_min * atr:
                spike_positions.append(i)
            elif not is_boom and move < -spike_min * atr:
                spike_positions.append(i)
        if len(spike_positions) < 2:
            return {"avg_interval": 0, "last_spike_ago": len(d) - spike_positions[-1] if spike_positions else 999,
                    "overdue": True, "spike_count": len(spike_positions),
                    "next_spike_window": "SOON" if spike_positions else "UNKNOWN"}
        # Calculate intervals
        intervals = [spike_positions[i+1] - spike_positions[i] for i in range(len(spike_positions)-1)]
        avg_int = np.mean(intervals)
        last_ago = len(d) - 1 - spike_positions[-1]
        overdue = last_ago > avg_int * 1.3
        if last_ago > avg_int * 1.5: window = "IMMINENT"
        elif last_ago > avg_int: window = "SOON"
        elif last_ago > avg_int * 0.5: window = "NORMAL"
        else: window = "RECENTLY_SPIKED"
        return {"avg_interval": round(float(avg_int), 1), "last_spike_ago": int(last_ago),
                "overdue": overdue, "spike_count": len(spike_positions),
                "next_spike_window": window, "intervals": [int(x) for x in intervals[-5:]]}
    except:
        return {"avg_interval": 0, "last_spike_ago": 999, "overdue": False,
                "spike_count": 0, "next_spike_window": "UNKNOWN"}

# ==============================================================================
# BC ENGINE #6: CANDLE ABSORPTION — Pressão institucional
# ==============================================================================

def bc_absorption_detector(df, direction, lookback=10):
    """Detecta absorção: grande volume/range mas preço não move = reversão iminente."""
    try:
        if len(df) < lookback + 3:
            return {"absorption": False, "type": "NONE", "strength": 0}
        d = df.tail(lookback)
        is_bull = direction == "BUY"
        # Look for absorption candle: large range but small body at extreme
        for i in range(-3, 0):
            row = d.iloc[i]
            rng = row['high'] - row['low']
            body = abs(row['close'] - row['open'])
            if rng == 0: continue
            body_pct = body / rng
            # Absorption: big range, tiny body (< 30% body)
            if body_pct < 0.30 and rng > d['ATR'].iloc[-1] * 0.8:
                if is_bull:
                    lower_wick = min(row['open'], row['close']) - row['low']
                    if lower_wick / rng > 0.5:
                        return {"absorption": True, "type": "BULL_ABSORPTION",
                                "strength": round(float(lower_wick / rng * 100), 1)}
                else:
                    upper_wick = row['high'] - max(row['open'], row['close'])
                    if upper_wick / rng > 0.5:
                        return {"absorption": True, "type": "BEAR_ABSORPTION",
                                "strength": round(float(upper_wick / rng * 100), 1)}
        return {"absorption": False, "type": "NONE", "strength": 0}
    except:
        return {"absorption": False, "type": "NONE", "strength": 0}

# ==============================================================================
# BC ENGINE #7: MULTI-SPIKE PATTERN — Spikes consecutivos
# ==============================================================================

def bc_multi_spike_pattern(df, profile, lookback=30):
    """Detecta padrões de spikes múltiplos — spikes tendem a vir em clusters."""
    try:
        if len(df) < lookback:
            return {"cluster": False, "consecutive_spikes": 0, "pattern": "NONE"}
        d = df.tail(lookback)
        atr = d['ATR'].mean()
        if atr == 0: return {"cluster": False, "consecutive_spikes": 0, "pattern": "NONE"}
        spike_min = profile.get('spike_size_min_atr', 2.0) * 0.8  # Slightly lower threshold
        is_boom = profile.get('gen_type') == 'BOOM'
        consecutive = 0
        last_was_spike = False
        gap_count = 0
        gap_tolerance = 2  # V24 FIX #13: Allow up to 2 non-spike candles between spikes
        for i in range(len(d)-1, max(0, len(d)-15), -1):
            move = d['close'].iloc[i] - d['close'].iloc[i-1]
            if is_boom and move > spike_min * atr:
                if last_was_spike or consecutive == 0: consecutive += 1
                last_was_spike = True
                gap_count = 0  # Reset gap counter
            elif not is_boom and move < -spike_min * atr:
                if last_was_spike or consecutive == 0: consecutive += 1
                last_was_spike = True
                gap_count = 0
            else:
                if consecutive > 0:
                    gap_count += 1
                    if gap_count > gap_tolerance:
                        break  # Too many non-spike candles, end of cluster
                last_was_spike = False
        pattern = "SPIKE_CLUSTER" if consecutive >= 3 else "DOUBLE_SPIKE" if consecutive == 2 else "SINGLE" if consecutive == 1 else "NONE"
        return {"cluster": consecutive >= 2, "consecutive_spikes": consecutive,
                "pattern": pattern}
    except:
        return {"cluster": False, "consecutive_spikes": 0, "pattern": "NONE"}

# ==============================================================================
# BC ENGINE #8: STOCHASTIC SPIKE TIMER
# ==============================================================================

def bc_stochastic_timer(df, profile):
    """Usa Stochastic + RSI combinados para timing de spike."""
    try:
        if len(df) < 20:
            return {"ready": False, "signal": "WAIT", "stoch_k": 50, "stoch_d": 50}
        d = df.tail(20)
        # V24 FIX #12: Parametric stochastic period based on spike frequency
        stoch_period = profile.get('stoch_period', None)
        if stoch_period is None:
            # Auto-calibrate: fast spike = shorter period, slow spike = longer
            freq = profile.get('spike_freq', 'MEDIUM')
            stoch_period = {"HIGH": 10, "MEDIUM": 14, "LOW": 20}.get(freq, 14)
        low_n = d['low'].rolling(stoch_period).min()
        high_n = d['high'].rolling(stoch_period).max()
        denom = high_n - low_n
        denom = denom.replace(0, np.nan)
        stoch_k = ((d['close'] - low_n) / denom * 100).iloc[-1]
        stoch_d = ((d['close'] - low_n) / denom * 100).rolling(3).mean().iloc[-1]
        if pd.isna(stoch_k): stoch_k = 50
        if pd.isna(stoch_d): stoch_d = 50
        rsi = d['RSI'].iloc[-1] if pd.notna(d['RSI'].iloc[-1]) else 50
        is_boom = profile.get('gen_type') == 'BOOM'
        if is_boom:
            # Boom spike UP: Stoch oversold + RSI oversold
            if stoch_k < 20 and rsi < 30:
                return {"ready": True, "signal": "SPIKE_BUY", "stoch_k": round(float(stoch_k),1),
                        "stoch_d": round(float(stoch_d),1), "rsi": round(float(rsi),1)}
            elif stoch_k > 80 and rsi > 70:
                return {"ready": True, "signal": "DRIFT_SELL", "stoch_k": round(float(stoch_k),1),
                        "stoch_d": round(float(stoch_d),1), "rsi": round(float(rsi),1)}
        else:
            # Crash spike DOWN: Stoch overbought + RSI overbought
            if stoch_k > 80 and rsi > 70:
                return {"ready": True, "signal": "SPIKE_SELL", "stoch_k": round(float(stoch_k),1),
                        "stoch_d": round(float(stoch_d),1), "rsi": round(float(rsi),1)}
            elif stoch_k < 20 and rsi < 30:
                return {"ready": True, "signal": "DRIFT_BUY", "stoch_k": round(float(stoch_k),1),
                        "stoch_d": round(float(stoch_d),1), "rsi": round(float(rsi),1)}
        return {"ready": False, "signal": "WAIT", "stoch_k": round(float(stoch_k),1),
                "stoch_d": round(float(stoch_d),1), "rsi": round(float(rsi),1)}
    except:
        return {"ready": False, "signal": "WAIT", "stoch_k": 50, "stoch_d": 50}


# ==============================================================================
# V21 ENGINE #1: SAMPLE ENTROPY — Previsibilidade do gerador
# ==============================================================================

def sample_entropy_v21(series, m=2, r_mult=0.2, max_n=200):
    """V24: SampEn < 0.5 = altamente previsivel. SampEn > 2.0 = caotico.
    FIX #14: max_n=200 (was 400) to reduce O(n²) from 160K to 40K iterations."""
    try:
        data = np.array(series.dropna().values[-max_n:], dtype=float)
        n = len(data)
        if n < 50: return 2.0, "CHAOTIC"
        r = r_mult * np.std(data)
        if r == 0: return 0.0, "CONSTANT"
        # V24: Vectorized distance computation for speed
        def _count(tl):
            cnt = 0
            templates = np.array([data[i:i+tl] for i in range(n - tl)])
            for i in range(len(templates)):
                # Vectorized: compute max abs diff against all subsequent templates
                diffs = np.max(np.abs(templates[i+1:] - templates[i]), axis=1)
                cnt += np.sum(diffs < r)
            return cnt
        B = _count(m)
        A = _count(m + 1)
        if B == 0 or A == 0: se = 2.5
        else: se = -np.log(A / B)
        if se < 0.4: regime = "HIGHLY_PREDICTABLE"
        elif se < 0.8: regime = "PREDICTABLE"
        elif se < 1.5: regime = "MODERATE"
        else: regime = "CHAOTIC"
        return round(float(se), 3), regime
    except: return 2.0, "ERROR"

# ==============================================================================
# V21 ENGINE #2: PERMUTATION ENTROPY — Determinismo na ordem
# ==============================================================================

def permutation_entropy_v21(series, order=3, delay=1, max_n=400):
    """PE=0 deterministic, PE=1 random. PE < 0.85 = padrao detectavel."""
    try:
        data = np.array(series.dropna().values[-max_n:], dtype=float)
        n = len(data)
        if n < order * delay + 10: return 1.0, "RANDOM"
        counts = {}
        total = 0
        for i in range(n - (order - 1) * delay):
            pat = tuple(int(x) for x in np.argsort(data[i:i + order * delay:delay]))
            counts[pat] = counts.get(pat, 0) + 1
            total += 1
        if total == 0: return 1.0, "RANDOM"
        max_e = math_log(factorial(order))
        if max_e == 0: return 1.0, "RANDOM"
        entropy = 0.0
        for c in counts.values():
            p = c / total
            if p > 0: entropy -= p * math_log(p)
        pe = entropy / max_e
        if pe < 0.75: regime = "DETERMINISTIC"
        elif pe < 0.85: regime = "STRUCTURED"
        elif pe < 0.95: regime = "WEAKLY_STRUCTURED"
        else: regime = "RANDOM"
        return round(float(pe), 4), regime
    except: return 1.0, "ERROR"

# ==============================================================================
# V21 ENGINE #3: SPECTRAL ANALYSIS (FFT) — Ciclos ocultos no CSPRNG
# ==============================================================================

def spectral_analysis_v21(series, top_n=3, min_period=5, max_period=200):
    """Encontra ciclos dominantes na serie de precos via FFT."""
    try:
        vals = np.array(series.dropna().values, dtype=float)
        log_ret = np.diff(np.log(vals))
        n = len(log_ret)
        if n < 100: return {"has_cycle": False, "cycles": [], "spectral_edge": 0}
        log_ret = log_ret - np.mean(log_ret)
        fft_v = np.fft.rfft(log_ret)
        power = np.abs(fft_v) ** 2
        freqs = np.fft.rfftfreq(n, d=1)
        valid = []
        for i in range(1, len(freqs)):
            if freqs[i] > 0:
                period = 1.0 / freqs[i]
                if min_period <= period <= max_period:
                    valid.append((period, power[i]))
        if not valid: return {"has_cycle": False, "cycles": [], "spectral_edge": 0}
        valid.sort(key=lambda x: x[1], reverse=True)
        mean_p = np.mean(power[1:])
        cycles = []
        for period, pwr in valid[:top_n]:
            sig = pwr / mean_p if mean_p > 0 else 0
            if sig > 3.0:
                cycles.append({"period": round(period, 1), "significance": round(float(sig), 2)})
        se = max((c['significance'] for c in cycles), default=0)
        return {"has_cycle": len(cycles) > 0, "cycles": cycles,
                "dominant_period": cycles[0]['period'] if cycles else 0,
                "spectral_edge": round(float(se), 2)}
    except: return {"has_cycle": False, "cycles": [], "spectral_edge": 0}

# ==============================================================================
# V21 ENGINE #4: TRANSITION MATRIX (Markov Chain)
# ==============================================================================

def transition_matrix_v21(series, n_states=3, max_n=500):
    """Detecta dependencias Markovianas nos retornos."""
    try:
        vals = np.array(series.dropna().values[-max_n:], dtype=float)
        log_ret = np.diff(np.log(vals))
        n = len(log_ret)
        if n < 80: return {"has_dependence": False, "transition_edge": 0, "matrix": {},
                           "p_reversal_up": 0.33, "p_reversal_down": 0.33,
                           "p_momentum_up": 0.33, "p_momentum_down": 0.33}
        thr = np.percentile(log_ret, [33.3, 66.7])
        states = np.digitize(log_ret, thr)
        mat = np.zeros((n_states, n_states))
        for i in range(len(states) - 1):
            mat[states[i], states[i + 1]] += 1
        row_s = mat.sum(axis=1, keepdims=True); row_s[row_s == 0] = 1
        prob = mat / row_s
        exp = np.outer(mat.sum(axis=1), mat.sum(axis=0)) / max(mat.sum(), 1)
        exp[exp == 0] = 1e-10
        chi2_val = float(np.sum((mat - exp) ** 2 / exp))
        df = (n_states - 1) ** 2
        p_val = 1 - chi2_dist.cdf(chi2_val, df)
        has_dep = p_val < 0.05
        labels = ["DOWN", "NEUTRAL", "UP"]
        max_dev = 0; best_t = ""
        for i in range(n_states):
            for j in range(n_states):
                d = abs(prob[i, j] - 1.0 / n_states)
                if d > max_dev: max_dev = d; best_t = f"{labels[i]}->{labels[j]}: {prob[i,j]:.2f}"
        return {"has_dependence": has_dep, "chi2": round(chi2_val, 2),
                "p_value": round(float(p_val), 4), "transition_edge": round(float(max_dev * 100), 1),
                "best_transition": best_t,
                "p_reversal_up": round(float(prob[0, 2]), 3) if n_states > 2 else 0.33,
                "p_reversal_down": round(float(prob[2, 0]), 3) if n_states > 2 else 0.33,
                "p_momentum_up": round(float(prob[2, 2]), 3) if n_states > 2 else 0.33,
                "p_momentum_down": round(float(prob[0, 0]), 3) if n_states > 2 else 0.33,
                "matrix": {labels[i]: {labels[j]: round(float(prob[i,j]),3) for j in range(n_states)} for i in range(n_states)}}
    except: return {"has_dependence": False, "transition_edge": 0, "matrix": {},
                    "p_reversal_up": 0.33, "p_reversal_down": 0.33,
                    "p_momentum_up": 0.33, "p_momentum_down": 0.33}

# ==============================================================================
# V21 ENGINE #5: COMPOUND PREDICTABILITY INDEX (CPI)
# ==============================================================================

def compound_predictability_index(series, vr_r=None, acf_r=None):
    """CPI 0-100. >60=FORTE, 35-60=MODERADO, <35=FRACO (nao operar)."""
    try:
        se_val, _ = sample_entropy_v21(series)
        se_sc = max(0, 25 - se_val * 12.5)
        pe_val, _ = permutation_entropy_v21(series)
        pe_sc = max(0, 25 - pe_val * 25)
        if vr_r is None: vr_r = variance_ratio_test(series)
        vr_sc = min(25, vr_r.get('n_significant', 0) * 6.25) if vr_r.get('has_edge') else 0
        if acf_r is None: acf_r = autocorrelation_analysis(series)
        acf_sc = min(25, len(acf_r.get('significant_lags', [])) * 6.25)
        cpi = se_sc + pe_sc + vr_sc + acf_sc
        if cpi >= 60: regime = "HIGHLY_PREDICTABLE"
        elif cpi >= 45: regime = "PREDICTABLE"
        elif cpi >= 35: regime = "MODERATE"
        else: regime = "UNPREDICTABLE"
        return {"cpi": round(float(cpi), 1), "regime": regime,
                "components": {"se": round(float(se_sc),1), "pe": round(float(pe_sc),1),
                               "vr": round(float(vr_sc),1), "acf": round(float(acf_sc),1)},
                "se_raw": se_val, "pe_raw": pe_val}
    except: return {"cpi": 0, "regime": "ERROR", "components": {}, "se_raw": 2.0, "pe_raw": 1.0}

# ==============================================================================
# V21 ENGINE #6: REGIME TRANSITION DETECTION
# ==============================================================================

def detect_regime_transition(df, lb_cur=30, lb_past=80):
    """Detecta MUDANCAS de regime (mais lucrativo que regime estatico)."""
    try:
        if len(df) < lb_past + 20: return "STABLE", 1.0, ""
        cur_r, cur_sc = classify_regime(df, lookback=lb_cur)
        past_r, past_sc = classify_regime(df.iloc[:-lb_cur], lookback=min(lb_past, len(df) - lb_cur - 1))
        adx_now = df['ADX'].iloc[-1]; adx_past = df['ADX'].iloc[-lb_cur] if len(df) > lb_cur else adx_now
        adx_acc = adx_now - adx_past
        bb_now = df['BB_width'].iloc[-1]; bb_past = df['BB_width'].iloc[-lb_cur] if len(df) > lb_cur else bb_now
        bb_ch = (bb_now - bb_past) / bb_past if bb_past > 0 else 0
        if "RANGING" in past_r and "TRENDING" in cur_r:
            return "BREAKOUT_TRANSITION", 1.4, f"Range->Trend (ADX +{adx_acc:.1f})"
        elif "TRENDING" in past_r and "RANGING" in cur_r:
            return "EXHAUSTION", 0.5, f"Trend->Range (ADX {adx_acc:.1f})"
        elif "RANGING" in past_r and "RANGING" in cur_r and bb_ch < -0.3:
            return "COMPRESSION_BUILDING", 1.2, f"Squeeze (BB {bb_ch:.0%})"
        elif "TRENDING" in past_r and "TRENDING" in cur_r and adx_acc > 5:
            return "TREND_ACCEL", 1.3, f"Accel (ADX +{adx_acc:.1f})"
        elif "TRENDING" in past_r and "TRENDING" in cur_r and adx_acc < -5:
            return "TREND_DECEL", 0.7, f"Decel (ADX {adx_acc:.1f})"
        return "STABLE", 1.0, ""
    except: return "STABLE", 1.0, ""

# ==============================================================================
# V21 FIX-B: DYNAMIC BIAS com Score de Confianca
# ==============================================================================

def calculate_dynamic_bias(h4, h1):
    """Bias com score -80 a +80. Substitui comparacao binaria."""
    try:
        c4 = h4.iloc[-1]; c1 = h1.iloc[-1]
        sc = 0.0
        if c4['ATR'] > 0:
            dist_a = (c4['close'] - c4['EMA_200']) / c4['ATR']
            sc += max(-20, min(20, dist_a * 4))
        if len(h4) > 20 and c4['ATR'] > 0:
            sl = (h4['EMA_200'].iloc[-1] - h4['EMA_200'].iloc[-20]) / (c4['ATR'] * 20)
            sc += max(-15, min(15, sl * 50))
        if c4['EMA_20'] > c4['EMA_50'] > c4['EMA_200']: sc += 20
        elif c4['EMA_20'] < c4['EMA_50'] < c4['EMA_200']: sc -= 20
        elif c4['EMA_20'] > c4['EMA_50']: sc += 8
        elif c4['EMA_20'] < c4['EMA_50']: sc -= 8
        h1_bull = c1['close'] > c1['EMA_200']; h4_bull = c4['close'] > c4['EMA_200']
        if h1_bull == h4_bull: sc += 15 if h1_bull else -15
        if len(h4) >= 3:
            hn = h4['MACD_hist'].iloc[-1]; hp = h4['MACD_hist'].iloc[-2]
            if hn > hp and hn > 0: sc += 10
            elif hn < hp and hn < 0: sc -= 10
            elif hn > hp: sc += 5
            elif hn < hp: sc -= 5
        if sc > 15: bias = "BULLISH"
        elif sc < -15: bias = "BEARISH"
        else: bias = "NEUTRAL"
        conf = min(abs(sc), 80) / 80 * 100
        return bias, round(float(conf), 1), round(float(sc), 1)
    except: return "NEUTRAL", 0.0, 0.0

# ==============================================================================
# V21 PREC #1: ENHANCED MOMENTUM (0-100)
# ==============================================================================

def enhanced_momentum_v21(h4, h1, m15, direction):
    """Multi-dimensional momentum: MACD hist + RSI zone + DI."""
    try:
        sc = 0.0; is_b = direction == "BULLISH"
        for tf, w in [(h4, 15), (h1, 12), (m15, 8)]:
            if len(tf) >= 3:
                h = tf['MACD_hist']
                acc = h.iloc[-1] - h.iloc[-2]
                if is_b:
                    if h.iloc[-1] > 0 and acc > 0: sc += w
                    elif h.iloc[-1] > 0: sc += w * 0.5
                    elif acc > 0: sc += w * 0.3
                else:
                    if h.iloc[-1] < 0 and acc < 0: sc += w
                    elif h.iloc[-1] < 0: sc += w * 0.5
                    elif acc < 0: sc += w * 0.3
        rsi = h1['RSI'].iloc[-1] if pd.notna(h1['RSI'].iloc[-1]) else 50
        if is_b:
            if 45 < rsi < 65: sc += 25
            elif 35 < rsi < 45: sc += 15
            elif rsi > 70: sc += 5
        else:
            if 35 < rsi < 55: sc += 25
            elif 55 < rsi < 65: sc += 15
            elif rsi < 30: sc += 5
        c1 = h1.iloc[-1]
        dip = c1.get('+DI', 0) if pd.notna(c1.get('+DI', np.nan)) else 0
        dim = c1.get('-DI', 0) if pd.notna(c1.get('-DI', np.nan)) else 0
        if dip + dim > 0:
            ds = abs(dip - dim) / (dip + dim)
            if is_b and dip > dim: sc += min(20, ds * 40)
            elif not is_b and dim > dip: sc += min(20, ds * 40)
        return round(min(100, sc), 1)
    except: return 0.0

# ==============================================================================
# V21 PREC #2: EDGE CORRELATION MATRIX
# ==============================================================================

def calculate_independent_edges(vr, acf, hurst_val, gen_bonus, dist, zscore,
                                 divergence, fib_level, sr_touch, align_type, vol_confirmed):
    """Conta confluencias INDEPENDENTES (nao correlacionadas)."""
    try:
        groups = {}
        g1 = 0
        if vr.get('has_edge') and vr.get('dominant_type') == 'MEAN_REVERT': g1 += 1
        if acf.get('has_pattern') and acf.get('dominant_type') == 'MEAN_REVERT': g1 += 0.5
        if hurst_val < 0.48: g1 += 0.5
        groups['STAT_MR'] = min(1.0, g1)
        g2 = 0
        if vr.get('has_edge') and vr.get('dominant_type') == 'TRENDING': g2 += 1
        if acf.get('has_pattern') and acf.get('dominant_type') == 'MOMENTUM': g2 += 0.5
        if hurst_val > 0.53: g2 += 0.5
        groups['STAT_TREND'] = min(1.0, g2)
        groups['GENERATOR'] = 1.0 if gen_bonus > 0 else 0.0
        g4 = 0
        if abs(zscore) > 1.5: g4 += 0.5
        if dist.get('percentile', 50) < 15 or dist.get('percentile', 50) > 85: g4 += 0.5
        groups['DISTRIBUTION'] = min(1.0, g4)
        groups['PATTERNS'] = min(1.0, 0.7 if divergence else 0.0)
        g6 = 0
        if fib_level: g6 += 0.4
        if sr_touch: g6 += 0.3
        if align_type not in ["NONE", None]: g6 += 0.3
        groups['STRUCTURE'] = min(1.0, g6)
        groups['VOLUME'] = 1.0 if vol_confirmed else 0.0
        n_act = sum(1 for v in groups.values() if v >= 0.5)
        tot = sum(groups.values())
        ql = "ELITE" if n_act >= 5 else "STRONG" if n_act >= 4 else "MODERATE" if n_act >= 3 else "WEAK"
        return {"n_independent": n_act, "total_strength": round(tot, 1), "groups": groups, "quality": ql}
    except: return {"n_independent": 0, "total_strength": 0, "groups": {}, "quality": "WEAK"}

# ==============================================================================
# V21 PREC #3: OPTIMAL HOLDING PERIOD
# ==============================================================================

def optimal_holding_period(acf_result, setup_type):
    """Calcula tempo otimo de trade baseado no edge decay."""
    try:
        base = {"SWING": 40, "DAY": 20, "MEAN_REVERSION": 15,
                "GEN_VOL_COMPRESS": 25, "GEN_SPIKE_DRIFT": 30,
                "GEN_STEP_REVERT": 12, "GEN_PRICE_DEV": 20,
                "BREAKOUT": 35, "PERFECT_STORM": 60}
        mc = base.get(setup_type, 30)
        sig_l = acf_result.get('significant_lags', [])
        if sig_l:
            ml = max(sig_l); hl = ml * 3
            mc = min(mc, max(10, hl * 2))
        return {"max_candles": int(mc), "time_stop": int(mc * 1.5), "edge_halflife": int(mc // 2)}
    except: return {"max_candles": 30, "time_stop": 45, "edge_halflife": 15}

# ==============================================================================
# V21 PREC #4: CONDITIONAL ENTRY ENGINE
# ==============================================================================

def conditional_entry_v21(setup_type, direction, price, ema20, ema50, atr, bb_lo, bb_hi):
    """Calcula preco de entrada ideal em vez de entrar no close."""
    try:
        is_l = "LONG" in str(direction) or "BULLISH" in str(direction)
        if setup_type == "SWING":
            if is_l:
                ideal = max(ema20 - atr * 0.2, (ema20 + ema50) / 2)
                return (price, "MARKET_IN_ZONE") if price < ideal + atr * 0.3 else (ideal, "LIMIT_VALUE_ZONE")
            else:
                ideal = min(ema20 + atr * 0.2, (ema20 + ema50) / 2)
                return (price, "MARKET_IN_ZONE") if price > ideal - atr * 0.3 else (ideal, "LIMIT_VALUE_ZONE")
        elif setup_type == "MEAN_REVERSION":
            if is_l:
                ideal = bb_lo + atr * 0.3
                return (price, "MARKET_BB_ZONE") if price < ideal + atr * 0.5 else (ideal, "LIMIT_BB_REENTRY")
            else:
                ideal = bb_hi - atr * 0.3
                return (price, "MARKET_BB_ZONE") if price > ideal - atr * 0.5 else (ideal, "LIMIT_BB_REENTRY")
        elif "BREAKOUT" in str(setup_type):
            return (price - atr * 0.3, "LIMIT_PULLBACK") if is_l else (price + atr * 0.3, "LIMIT_PULLBACK")
        return price, "MARKET"
    except: return price, "MARKET"


# DISTRIBUIÇÃO V20 (mantido do V19, corrigido)
# ==============================================================================

class DistributionAnalyzer:
    @staticmethod
    def analyze(df, window=150):
        try:
            log_returns = np.log(df['close'] / df['close'].shift(1)).dropna()
            if len(log_returns) < window:
                return {"skewness": 0, "kurtosis": 3, "tail_risk": "NORMAL",
                        "percentile": 50, "is_normal": True, "signal": "NEUTRAL"}
            recent = log_returns.tail(window)
            skewness = float(recent.skew())
            kurtosis = float(recent.kurtosis()) + 3
            jb = (window / 6) * (skewness**2 + (1/4)*(kurtosis - 3)**2)
            is_normal = jb < 5.99
            if kurtosis > 5: tail_risk = "FAT_TAILS"
            elif kurtosis > 4: tail_risk = "HEAVY_TAILS"
            elif kurtosis < 2.5: tail_risk = "THIN_TAILS"
            else: tail_risk = "NORMAL"
            z_return = float((recent.iloc[-1] - recent.mean()) / recent.std()) if recent.std() > 0 else 0
            recent_cum = float(recent.tail(10).sum())
            all_windows = [float(log_returns.iloc[i:i+10].sum()) for i in range(0, len(log_returns)-10, 5)]
            percentile = sum(1 for w in all_windows if w < recent_cum) / len(all_windows) * 100 if all_windows else 50
            signal = "NEUTRAL"
            if abs(skewness) > 0.5:
                signal = "POSITIVE_SKEW" if skewness > 0 else "NEGATIVE_SKEW"
            if tail_risk == "FAT_TAILS" and abs(z_return) > 2:
                signal = "EXTREME_TAIL_EVENT"
            return {"skewness": round(skewness, 3), "kurtosis": round(kurtosis, 3),
                    "jarque_bera": round(jb, 2), "is_normal": is_normal, "tail_risk": tail_risk,
                    "z_return": round(z_return, 2), "percentile": round(percentile, 1), "signal": signal}
        except:
            return {"skewness": 0, "kurtosis": 3, "tail_risk": "NORMAL", "percentile": 50,
                    "is_normal": True, "signal": "NEUTRAL"}

# ==============================================================================
# 🟢 PRECISION #5: ADAPTIVE KELLY CRITERION (não if/elif primitivo)
# ==============================================================================

class AdaptiveLearnerV20:
    @staticmethod
    def adjust_profile(profile, bt_results, dist_analysis):
        adjusted = profile.copy()
        if not bt_results or bt_results.get('TOTAL_TRADES', 0) < 5:
            return adjusted
        wr = bt_results.get('WR', 50)
        pf = bt_results.get('PF', 1.0)
        dd = bt_results.get('DD', 0)

        # V24 FIX #3 + A1: Kelly Criterion CORRETO
        # Fórmula: f* = (p×b - q) / b onde b = avg_win/avg_loss (NÃO PF)
        # PF já incorpora WR, usar como 'b' causa double-counting
        p = wr / 100
        q = 1 - p
        # Extract avg_win and avg_loss from backtest results
        results = bt_results.get('RESULTS', [])
        wins = [r for r in results if r > 0]
        losses = [abs(r) for r in results if r <= 0]
        avg_win = np.mean(wins) if wins else 1.0
        avg_loss = np.mean(losses) if losses else 1.0
        b = avg_win / avg_loss if avg_loss > 0 else 1.0  # Correct odds ratio
        kelly = (p * b - q) / b if b > 0 else 0
        kelly = max(0.0, min(kelly, 0.25))
        # DD penalty contínuo
        dd_penalty = max(0.3, 1.0 - dd / 20)
        # Risk multiplier
        adjusted['risk_mult'] = round(profile['risk_mult'] * (0.5 + kelly * 2) * dd_penalty, 3)
        adjusted['risk_mult'] = max(0.2, min(adjusted['risk_mult'], 2.5))
        # SL contínuo
        sl_adj = 1.0 + max(0, dd - 5) * 0.03 - max(0, wr - 60) * 0.005
        adjusted['sl_atr_mult'] = round(profile['sl_atr_mult'] * max(0.8, min(sl_adj, 1.3)), 2)
        # TP baseado em kurtosis
        kurt = dist_analysis.get('kurtosis', 3)
        tp_mult = 1.0 + max(0, kurt - 3) * 0.1
        adjusted['tp2_r'] = round(min(profile['tp2_r'] * tp_mult, 10.0), 1)
        return adjusted

# ==============================================================================
# SCALING ENGINE V20 (mantido, funcional)
# ==============================================================================

class ScalingEngine:
    @staticmethod
    def calculate_pyramid(grade, score, capital, risk_pct, entry, sl, atr, profile):
        risk_per_unit = abs(entry - sl)
        if risk_per_unit == 0:
            return {"levels": [{"entry": entry, "risk_pct": risk_pct, "size": 0, "trigger": "BASE"}],
                    "total_risk_pct": risk_pct, "total_size": 0, "n_levels": 1}
        levels = []
        rm = profile.get('risk_mult', 1.0)
        if grade == "S" and score >= 140:
            for mult, rp, off, trig in [(1.5, risk_pct*1.5, 0, "STORM ENTRY"),
                                         (1.0, risk_pct, 0.5, "+0.5 ATR → add (SL→BE)"),
                                         (0.5, risk_pct*0.5, 1.5, "+1.5 ATR → add")]:
                e = entry + atr*off*(1 if entry>sl else -1) if off else entry
                levels.append({"entry": round(e,5), "risk_pct": round(rp,2),
                    "size": round(capital*rp/100*rm/risk_per_unit,2), "trigger": trig})
        elif grade in ["A++","A+"] and score >= 90:
            for mult, rp, off, trig in [(1.0, risk_pct, 0, "BASE ENTRY"),
                                         (0.5, risk_pct*0.5, 0.8, "+0.8 ATR → add (SL→BE)")]:
                e = entry + atr*off*(1 if entry>sl else -1) if off else entry
                levels.append({"entry": round(e,5), "risk_pct": round(rp,2),
                    "size": round(capital*rp/100*rm/risk_per_unit,2), "trigger": trig})
        else:
            levels.append({"entry": round(entry,5), "risk_pct": round(risk_pct,2),
                "size": round(capital*risk_pct/100*rm/risk_per_unit,2), "trigger": "SINGLE ENTRY"})
        return {"levels": levels, "total_risk_pct": round(sum(l['risk_pct'] for l in levels),2),
                "total_size": round(sum(l['size'] for l in levels),2), "n_levels": len(levels)}

# ==============================================================================
# NETWORK — Deriv API
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
            # V24-BC: ONLY Boom and Crash indices
            return {x['display_name'].upper(): x['symbol'] for x in res['active_symbols']
                    if x['market'] == 'synthetic_index'
                    and ('BOOM' in x['display_name'].upper() or 'CRASH' in x['display_name'].upper())}
    return None

async def fetch_multi_tf(code):
    """H1=800, H4=400, M15=2000, M5=500"""
    reqs = [
        {"ticks_history": code, "style": "candles", "granularity": 3600, "count": 800, "end": "latest"},
        {"ticks_history": code, "style": "candles", "granularity": 14400, "count": 400, "end": "latest"},
        {"ticks_history": code, "style": "candles", "granularity": 900, "count": 2000, "end": "latest"},
        {"ticks_history": code, "style": "candles", "granularity": 300, "count": 500, "end": "latest"},
    ]
    for url in DERIV_SERVERS:
        try:
            async with websockets.connect(url, ping_interval=20, close_timeout=15) as ws:
                results = []
                for r in reqs:
                    await ws.send(json.dumps(r))
                    results.append(json.loads(await asyncio.wait_for(ws.recv(), 15)))
                if all('candles' in x for x in results):
                    return results[0]['candles'], results[1]['candles'], results[2]['candles'], results[3]['candles'], None
        except:
            continue
    return None, None, None, None, "CONNECTION LOST"

async def fetch_single(code, granularity, count):
    req = {"ticks_history": code, "style": "candles", "granularity": granularity, "count": count, "end": "latest"}
    for url in DERIV_SERVERS:
        res = await socket_req(url, req)
        if res and 'candles' in res: return res['candles']
    return None

# ==============================================================================
# INDICADORES TÉCNICOS (limpo, sem mudanças — funcional)
# ==============================================================================

def prep_df(data):
    df = pd.DataFrame(data)
    for c in ['open','high','low','close']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df['date'] = pd.to_datetime(df['epoch'], unit='s')
    df.set_index('date', inplace=True)
    return df

def calculate_rsi_wilder(series, period=14):
    delta = series.diff(); gain = delta.where(delta>0,0.0); loss = -delta.where(delta<0,0.0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    for i in range(period, len(series)):
        if pd.notna(avg_gain.iloc[i-1]):
            avg_gain.iloc[i] = (avg_gain.iloc[i-1]*(period-1)+gain.iloc[i])/period
            avg_loss.iloc[i] = (avg_loss.iloc[i-1]*(period-1)+loss.iloc[i])/period
    rs = avg_gain / avg_loss.replace(0,np.nan)
    return 100 - (100/(1+rs))

def calculate_macd(df, fast=12, slow=26, signal=9):
    ema_f = df['close'].ewm(span=fast,adjust=False).mean()
    ema_s = df['close'].ewm(span=slow,adjust=False).mean()
    df['MACD'] = ema_f-ema_s; df['MACD_signal'] = df['MACD'].ewm(span=signal,adjust=False).mean()
    df['MACD_hist'] = df['MACD']-df['MACD_signal']; return df

def calculate_adx(df, window=14):
    df['trh']=df['high']-df['low']; df['trc']=abs(df['high']-df['close'].shift()); df['trl']=abs(df['low']-df['close'].shift())
    df['TR']=df[['trh','trc','trl']].max(axis=1)
    df['+DM']=np.where((df['high']>df['high'].shift())&(df['low']<=df['low'].shift()),df['high']-df['high'].shift(),0)
    df['-DM']=np.where((df['low']<df['low'].shift())&(df['high']>=df['high'].shift()),df['low'].shift()-df['low'],0)
    df['+DM']=np.where(df['+DM']>df['-DM'],df['+DM'],0); df['-DM']=np.where(df['-DM']>df['+DM'],df['-DM'],0)
    df['TR_E']=df['TR'].ewm(span=window,adjust=False).mean()
    df['+DM_E']=df['+DM'].ewm(span=window,adjust=False).mean(); df['-DM_E']=df['-DM'].ewm(span=window,adjust=False).mean()
    df['+DI']=(df['+DM_E']/df['TR_E'])*100; df['-DI']=(df['-DM_E']/df['TR_E'])*100
    di_sum=(df['+DI']+df['-DI']).replace(0,np.nan); df['DX']=(abs(df['+DI']-df['-DI'])/di_sum)*100
    df['ADX']=df['DX'].ewm(span=window,adjust=False).mean()
    df.drop(columns=['trh','trc','trl','TR','+DM','-DM','TR_E','+DM_E','-DM_E','DX'],inplace=True)
    # V21: +DI and -DI PRESERVED (not dropped)
    return df

def calculate_zscore(series, window=50):
    mean = series.rolling(window=window).mean(); std = series.rolling(window=window).std()
    return (series-mean)/std.replace(0,np.nan)

# 🟠 MATH FIX #2: HURST COM VALIDAÇÃO R²
def calculate_hurst_exponent(series, max_lag=100):
    try:
        ts = series.dropna().values
        if len(ts) < 50: return 0.5, "RANDOM_WALK", 0.0
        lags = range(10, min(max_lag, len(ts)//3))
        rs_values = []
        for lag in lags:
            n_chunks = len(ts)//lag
            if n_chunks < 1: continue
            rs_lag = []
            for i in range(n_chunks):
                chunk = ts[i*lag:(i+1)*lag]; mean_val = np.mean(chunk); dev = chunk-mean_val
                cum = np.cumsum(dev); R = np.max(cum)-np.min(cum); S = np.std(chunk, ddof=1)
                if S > 0: rs_lag.append(R/S)
            if rs_lag: rs_values.append((np.log(lag), np.log(np.mean(rs_lag))))
        if len(rs_values) < 3: return 0.5, "INSUFFICIENT_DATA", 0.0
        x = np.array([v[0] for v in rs_values]); y = np.array([v[1] for v in rs_values])
        coeffs = np.polyfit(x, y, 1); H = max(0.0, min(1.0, coeffs[0]))
        # R² VALIDATION
        y_pred = coeffs[0]*x + coeffs[1]
        ss_res = np.sum((y-y_pred)**2); ss_tot = np.sum((y-np.mean(y))**2)
        r_squared = 1 - ss_res/ss_tot if ss_tot > 0 else 0
        if r_squared < 0.7:
            return round(H,3), "UNRELIABLE", round(r_squared,3)
        if H > 0.6: regime = "STRONG_TREND"
        elif H > 0.53: regime = "WEAK_TREND"
        elif H > 0.47: regime = "RANDOM_WALK"
        elif H > 0.4: regime = "WEAK_MEAN_REVERT"
        else: regime = "STRONG_MEAN_REVERT"
        return round(H,3), regime, round(r_squared,3)
    except:
        return 0.5, "ERROR", 0.0

def find_pivot_highs(data, order=5):
    pivots = []; values = data.values if hasattr(data,'values') else np.array(data)
    for i in range(order, len(values)-order):
        if np.isnan(values[i]): continue
        if all(values[i]>values[i-j] and values[i]>values[i+j] for j in range(1,order+1)): pivots.append(i)
    return np.array(pivots)

def find_pivot_lows(data, order=5):
    pivots = []; values = data.values if hasattr(data,'values') else np.array(data)
    for i in range(order, len(values)-order):
        if np.isnan(values[i]): continue
        if all(values[i]<values[i-j] and values[i]<values[i+j] for j in range(1,order+1)): pivots.append(i)
    return np.array(pivots)

def detect_divergence(df, indicator='RSI', order=5):
    try:
        if len(df) < (order*2+5) or indicator not in df.columns: return None, 0, ""
        ph=find_pivot_highs(df['high'],order); pl=find_pivot_lows(df['low'],order)
        ih=find_pivot_highs(df[indicator],order); il=find_pivot_lows(df[indicator],order)
        if len(ph)>=2 and len(ih)>=2:
            ph1,ph2=ph[-2],ph[-1]; ih1=ih[np.argmin(np.abs(ih-ph1))]; ih2=ih[np.argmin(np.abs(ih-ph2))]
            if abs(ih1-ph1)<=3 and abs(ih2-ph2)<=3:
                if df['high'].iloc[ph2]>df['high'].iloc[ph1] and df[indicator].iloc[ih2]<df[indicator].iloc[ih1]:
                    s=min((df['high'].iloc[ph2]-df['high'].iloc[ph1])/df['high'].iloc[ph1]*100+(df[indicator].iloc[ih1]-df[indicator].iloc[ih2])/max(df[indicator].iloc[ih1],1)*100,10)
                    if s>1: return "BEARISH_DIVERGENCE",-int(min(s*3,20)),f"Preço HH vs {indicator} LH"
        if len(pl)>=2 and len(il)>=2:
            pl1,pl2=pl[-2],pl[-1]; il1=il[np.argmin(np.abs(il-pl1))]; il2=il[np.argmin(np.abs(il-pl2))]
            if abs(il1-pl1)<=3 and abs(il2-pl2)<=3:
                if df['low'].iloc[pl2]<df['low'].iloc[pl1] and df[indicator].iloc[il2]>df[indicator].iloc[il1]:
                    s=min((df['low'].iloc[pl1]-df['low'].iloc[pl2])/df['low'].iloc[pl1]*100+(df[indicator].iloc[il2]-df[indicator].iloc[il1])/max(abs(df[indicator].iloc[il1]),1)*100,10)
                    if s>1: return "BULLISH_DIVERGENCE",int(min(s*3,20)),f"Preço LL vs {indicator} HL"
        if len(pl)>=2 and len(il)>=2:
            pl1,pl2=pl[-2],pl[-1]; il1=il[np.argmin(np.abs(il-pl1))]; il2=il[np.argmin(np.abs(il-pl2))]
            if abs(il1-pl1)<=3 and abs(il2-pl2)<=3:
                if df['low'].iloc[pl2]>df['low'].iloc[pl1] and df[indicator].iloc[il2]<df[indicator].iloc[il1]:
                    return "HIDDEN_BULLISH",15,"Hidden: HL vs LL"
        if len(ph)>=2 and len(ih)>=2:
            ph1,ph2=ph[-2],ph[-1]; ih1=ih[np.argmin(np.abs(ih-ph1))]; ih2=ih[np.argmin(np.abs(ih-ph2))]
            if abs(ih1-ph1)<=3 and abs(ih2-ph2)<=3:
                if df['high'].iloc[ph2]<df['high'].iloc[ph1] and df[indicator].iloc[ih2]>df[indicator].iloc[ih1]:
                    return "HIDDEN_BEARISH",-15,"Hidden: LH vs HH"
        return None, 0, ""
    except: return None, 0, ""

def detect_sr_clustered(df, window=100, min_touches=3):
    try:
        if len(df)<window or 'ATR' not in df.columns: return []
        recent=df.tail(window); atr=recent['ATR'].iloc[-1]
        if pd.isna(atr) or atr==0: return []
        tolerance=atr*0.3
        hp=find_pivot_highs(recent['high'],3); lp=find_pivot_lows(recent['low'],3)
        prices=sorted([recent['high'].iloc[i] for i in hp]+[recent['low'].iloc[i] for i in lp])
        if not prices: return []
        clusters,current=[],[prices[0]]
        for i in range(1,len(prices)):
            if prices[i]-current[-1]<=tolerance: current.append(prices[i])
            else:
                if len(current)>=min_touches: clusters.append(current)
                current=[prices[i]]
        if len(current)>=min_touches: clusters.append(current)
        cp=df['close'].iloc[-1]
        levels=[{'price':round(np.mean(c),4),'touches':len(c),'type':'RESISTANCE' if np.mean(c)>cp else 'SUPPORT',
                'strength':len(c)+(1 if max(c)-min(c)<tolerance*0.5 else 0),
                'zone_high':round(max(c),4),'zone_low':round(min(c),4)} for c in clusters]
        levels.sort(key=lambda x:x['strength'],reverse=True); return levels[:6]
    except: return []

def calculate_fibonacci(df, lookback=100):
    try:
        if len(df)<lookback: return {},None,None
        recent=df.tail(lookback); hp=find_pivot_highs(recent['high'],7); lp=find_pivot_lows(recent['low'],7)
        if len(hp)==0 or len(lp)==0: return {},None,None
        sh=recent['high'].iloc[hp[-1]]; sl_v=recent['low'].iloc[lp[-1]]
        if pd.isna(sh) or pd.isna(sl_v) or sh==sl_v: return {},None,None
        diff=sh-sl_v
        if hp[-1]>lp[-1]:
            d="UPTREND"; fibs={'23.6%':sh-diff*0.236,'38.2%':sh-diff*0.382,'50.0%':sh-diff*0.50,'61.8%':sh-diff*0.618,'78.6%':sh-diff*0.786}
        else:
            d="DOWNTREND"; fibs={'23.6%':sl_v+diff*0.236,'38.2%':sl_v+diff*0.382,'50.0%':sl_v+diff*0.50,'61.8%':sl_v+diff*0.618,'78.6%':sl_v+diff*0.786}
        return fibs,d,{'high':sh,'low':sl_v}
    except: return {},None,None

def check_fib_confluence(price, fibs, atr):
    try:
        if not fibs or pd.isna(price) or pd.isna(atr) or atr==0: return None,0
        for name,lvl in fibs.items():
            if pd.notna(lvl) and abs(price-lvl)<atr*0.4:
                return name,(15 if '61.8' in name else 10 if '50.0' in name or '38.2' in name else 5)
        return None,0
    except: return None,0

def detect_bb_cycle(df, profile, lookback=30):
    try:
        if len(df)<lookback: return "UNKNOWN",0,0
        recent=df.tail(lookback); bw=recent['BB_width']; avg=bw.mean(); cur=bw.iloc[-1]
        if avg==0: return "UNKNOWN",0,0
        ratio=cur/avg; threshold=profile.get('bb_squeeze_threshold',0.6)
        sc=sum(bw<avg*threshold)
        if ratio<threshold: return "SQUEEZE",ratio,sc
        elif ratio>1.5: return "EXPANSION",ratio,0
        return "NORMAL",ratio,0
    except: return "UNKNOWN",0,0

def count_consecutive(df, lookback=20):
    try:
        recent=df.tail(lookback); dirs=(recent['close']>recent['open']).astype(int)
        cd=dirs.iloc[-1]; streak=0
        for i in range(len(dirs)-1,-1,-1):
            if dirs.iloc[i]==cd: streak+=1
            else: break
        return streak, "BULLISH" if cd==1 else "BEARISH"
    except: return 0, "UNKNOWN"

def detect_roc_extreme(df, profile, periods=[5,10,20]):
    try:
        results={}; threshold=profile.get('roc_extreme_pct',1.0)
        for p in periods:
            if len(df)<p+1: continue
            roc=((df['close'].iloc[-1]-df['close'].iloc[-p-1])/df['close'].iloc[-p-1])*100
            if abs(roc)>threshold*2: status="EXTREME"
            elif abs(roc)>threshold: status="ELEVATED"
            else: status="NORMAL"
            results[f"ROC_{p}"]={'value':round(roc,3),'status':status,'direction':"UP" if roc>0 else "DOWN"}
        overall="NORMAL"
        for r in results.values():
            if r['status']=="EXTREME": overall="EXTREME"; break
            elif r['status']=="ELEVATED": overall="ELEVATED"
        return overall,results
    except: return "NORMAL",{}

# 🟡 EDGE #8: TRIGGER CANDLE CONFIRMATION
def trigger_candle_confirmed(df, direction):
    """Verifica se último candle confirma a entrada"""
    try:
        if len(df) < 3: return False, "NO_DATA"
        last = df.iloc[-1]; prev = df.iloc[-2]
        body = abs(last['close']-last['open']); rng = last['high']-last['low']
        body_pct = body/rng if rng > 0 else 0
        if direction == "BULLISH":
            bullish = last['close'] > last['open']
            above_prev = last['close'] > prev['close']
            strong = body_pct > 0.5
            if bullish and above_prev and strong: return True, "STRONG_TRIGGER"
            elif bullish and above_prev: return True, "WEAK_TRIGGER"
            return False, "NO_TRIGGER"
        else:
            bearish = last['close'] < last['open']
            below_prev = last['close'] < prev['close']
            strong = body_pct > 0.5
            if bearish and below_prev and strong: return True, "STRONG_TRIGGER"
            elif bearish and below_prev: return True, "WEAK_TRIGGER"
            return False, "NO_TRIGGER"
    except: return False, "ERROR"

# 🟢 PRECISION #3: SMART TP COM S/R AWARENESS
def smart_tp(entry, direction, risk, base_r1, base_r2, sr_levels):
    """Ajusta TP se S/R forte no caminho"""
    raw_tp1 = entry + base_r1 * risk if direction=="LONG" else entry - base_r1 * risk
    raw_tp2 = entry + base_r2 * risk if direction=="LONG" else entry - base_r2 * risk
    for sr in (sr_levels or []):
        if sr.get('strength',0) < 4: continue
        sp = sr['price']
        if direction == "LONG":
            if entry < sp < raw_tp1: raw_tp1 = sp - risk * 0.1; break
        else:
            if raw_tp1 < sp < entry: raw_tp1 = sp + risk * 0.1; break
    return round(raw_tp1, 5), round(raw_tp2, 5)

def detect_micro_pullback(df, direction, atr):
    try:
        if len(df)<5: return None,"MARKET"
        last=df.tail(3); curr=last.iloc[-1]; prev=last.iloc[-2]
        if direction=="BULLISH":
            if curr['close']<prev['close'] and curr['close']>curr['EMA_20'] and curr['low']>curr['EMA_50']:
                return (curr['low']+curr['EMA_20'])/2, "MICRO_PULLBACK"
            if abs(curr['low']-curr['EMA_20'])<atr*0.3 and curr['close']>curr['EMA_20']:
                return curr['EMA_20']+atr*0.1, "EMA_RETEST"
        elif direction=="BEARISH":
            if curr['close']>prev['close'] and curr['close']<curr['EMA_20'] and curr['high']<curr['EMA_50']:
                return (curr['high']+curr['EMA_20'])/2, "MICRO_PULLBACK"
            if abs(curr['high']-curr['EMA_20'])<atr*0.3 and curr['close']<curr['EMA_20']:
                return curr['EMA_20']-atr*0.1, "EMA_RETEST"
        return None,"MARKET"
    except: return None,"MARKET"

def detect_patterns(df):
    patterns,scores=[],[]
    for i in range(1,len(df)):
        c,p=df.iloc[i],df.iloc[i-1]; pl,sc=[],0
        body=abs(c['close']-c['open']); rng=c['high']-c['low']
        if rng>0:
            uw=c['high']-max(c['open'],c['close']); lw=min(c['open'],c['close'])-c['low']
            if lw>0 and body/rng<0.35 and uw<body:
                r=lw/max(body,0.0001)
                if r>3: pl.append("PIN_BULL_STRONG"); sc+=10
                elif r>2: pl.append("PIN_BULL_MOD"); sc+=5
            elif uw>0 and body/rng<0.35 and lw<body:
                r=uw/max(body,0.0001)
                if r>3: pl.append("PIN_BEAR_STRONG"); sc+=10
                elif r>2: pl.append("PIN_BEAR_MOD"); sc+=5
        cb=abs(c['close']-c['open']); pb=abs(p['close']-p['open'])
        ct,cb2=max(c['open'],c['close']),min(c['open'],c['close'])
        pt,pb3=max(p['open'],p['close']),min(p['open'],p['close'])
        if c['close']>c['open'] and p['close']<p['open'] and cb2<pb3 and ct>pt:
            r=cb/max(pb,0.0001)
            if r>2: pl.append("ENGULF_BULL_STRONG"); sc+=10
            else: pl.append("ENGULF_BULL"); sc+=5
        elif c['close']<c['open'] and p['close']>p['open'] and cb2<pb3 and ct>pt:
            r=cb/max(pb,0.0001)
            if r>2: pl.append("ENGULF_BEAR_STRONG"); sc+=10
            else: pl.append("ENGULF_BEAR"); sc+=5
        if c['high']<=p['high'] and c['low']>=p['low']: pl.append("INSIDE_BAR"); sc+=5
        if rng>0 and body/rng<0.1: pl.append("DOJI"); sc+=3
        patterns.append(pl); scores.append(sc)
    df['patterns']=[[]]+patterns; df['pattern_score']=[0]+scores; return df

def detect_swing_points(df, window=5):
    df['swing_high']=False; df['swing_low']=False
    for i in range(window,len(df)):
        lb=df.iloc[max(0,i-window):i+1]
        if df['high'].iloc[i]==lb['high'].max(): df.iloc[i,df.columns.get_loc('swing_high')]=True
        if df['low'].iloc[i]==lb['low'].min(): df.iloc[i,df.columns.get_loc('swing_low')]=True
    return df

def classify_market_structure(df):
    sh=df[df['swing_high']]['high'].tail(4); sl=df[df['swing_low']]['low'].tail(4)
    if len(sh)<2 or len(sl)<2: return "INSUFFICIENT"
    hh=sh.iloc[-1]>sh.iloc[-2]; hl=sl.iloc[-1]>sl.iloc[-2]
    ll=sl.iloc[-1]<sl.iloc[-2]; lh=sh.iloc[-1]<sh.iloc[-2]
    if hh and hl: return "UPTREND_STRONG"
    elif ll and lh: return "DOWNTREND_STRONG"
    elif hh or hl: return "UPTREND_WEAK"
    elif ll or lh: return "DOWNTREND_WEAK"
    return "RANGE_BOUND"

def classify_regime(df, lookback=50):
    try:
        if len(df)<lookback: return "UNKNOWN",0
        recent=df.tail(lookback); c=recent.iloc[-1]; adx=c['ADX']
        slope=(recent['EMA_50'].iloc[-1]-recent['EMA_50'].iloc[-10])/(c['ATR']*10) if c['ATR']>0 else 0
        bb_ratio=c['BB_width']/recent['BB_width'].mean() if recent['BB_width'].mean()>0 else 1
        sc=0
        if adx>30: sc+=3
        elif adx>20: sc+=2
        elif adx>15: sc+=1
        if abs(slope)>0.3: sc+=2
        elif abs(slope)>0.15: sc+=1
        if bb_ratio>1.3: sc+=1
        elif bb_ratio<0.7: sc-=1
        if sc>=4: return "TRENDING_STRONG",sc
        elif sc>=2: return "TRENDING_WEAK",sc
        elif sc<=0: return "RANGING",sc
        return "TRANSITIONAL",sc
    except: return "UNKNOWN",0

def analyze_tick_volume(df, lookback=20):
    try:
        if len(df)<lookback: return "NORMAL",1.0
        recent=df.tail(lookback); ranges=recent['high']-recent['low']; bodies=abs(recent['close']-recent['open'])
        rr=ranges.iloc[-1]/ranges.mean() if ranges.mean()>0 else 1
        br=bodies.iloc[-1]/bodies.mean() if bodies.mean()>0 else 1
        proxy=(rr+br)/2
        if proxy>2.0: return "VERY_HIGH",proxy
        elif proxy>1.5: return "HIGH",proxy
        elif proxy>0.7: return "NORMAL",proxy
        return "LOW",proxy
    except: return "NORMAL",1.0

def confirm_breakout_volume(df):
    try:
        if len(df)<20: return False,0
        ranges=df['high']-df['low']; ratio=ranges.iloc[-1]/ranges.iloc[-20:-1].mean() if ranges.iloc[-20:-1].mean()>0 else 1
        return ratio>1.3, ratio
    except: return False,0

def indicators(df):
    df['EMA_20']=df['close'].ewm(span=20,adjust=False).mean()
    df['EMA_50']=df['close'].ewm(span=50,adjust=False).mean()
    df['EMA_200']=df['close'].ewm(span=200,adjust=False).mean()
    df['RSI']=calculate_rsi_wilder(df['close'],14)
    hl=df['high']-df['low']; hc=(df['high']-df['close'].shift()).abs(); lc=(df['low']-df['close'].shift()).abs()
    df['tr']=pd.concat([hl,hc,lc],axis=1).max(axis=1); df['ATR']=df['tr'].ewm(span=14,adjust=False).mean()
    df=calculate_adx(df); df=calculate_macd(df)
    df['BB_middle']=df['close'].rolling(20).mean(); df['BB_std']=df['close'].rolling(20).std()
    df['BB_upper']=df['BB_middle']+df['BB_std']*2; df['BB_lower']=df['BB_middle']-df['BB_std']*2
    df['BB_width']=((df['BB_upper']-df['BB_lower'])/df['BB_middle'].replace(0,np.nan))*100
    df['ZSCORE']=calculate_zscore(df['close'],50)
    df=detect_patterns(df); df=detect_swing_points(df); df.dropna(inplace=True); return df

def detect_alignment(h4r, h1r, m15r, d):
    sc=0
    if d=="BULLISH":
        if h4r['close']>h4r['EMA_20']>h4r['EMA_50']>h4r['EMA_200']: sc+=10
        if h1r['close']>h1r['EMA_20']>h1r['EMA_50']>h1r['EMA_200']: sc+=10
        if m15r['close']>m15r['EMA_20']>m15r['EMA_50']>m15r['EMA_200']: sc+=10
    else:
        if h4r['close']<h4r['EMA_20']<h4r['EMA_50']<h4r['EMA_200']: sc+=10
        if h1r['close']<h1r['EMA_20']<h1r['EMA_50']<h1r['EMA_200']: sc+=10
        if m15r['close']<m15r['EMA_20']<m15r['EMA_50']<m15r['EMA_200']: sc+=10
    if sc==30: return "PERFECT",25
    elif sc>=20: return "STRONG",15
    elif sc>=10: return "WEAK",5
    return "NONE",0

def check_momentum(h4,h1,m15,d):
    sc=0
    if d=="BULLISH":
        if h4['MACD'].iloc[-1]>0:sc+=1
        if h1['MACD'].iloc[-1]>0:sc+=1
        if m15['MACD'].iloc[-1]>0:sc+=1
    else:
        if h4['MACD'].iloc[-1]<0:sc+=1
        if h1['MACD'].iloc[-1]<0:sc+=1
        if m15['MACD'].iloc[-1]<0:sc+=1
    return sc

def detect_swing_level(df, direction, atr_mult=1.5):
    if direction=="BUY":
        sw=df[df['swing_low']]['low']
        return (sw.iloc[-1]-df['ATR'].iloc[-1]*atr_mult) if not sw.empty else df['low'].tail(20).min()-df['ATR'].iloc[-1]*atr_mult
    else:
        sw=df[df['swing_high']]['high']
        return (sw.iloc[-1]+df['ATR'].iloc[-1]*atr_mult) if not sw.empty else df['high'].tail(20).max()+df['ATR'].iloc[-1]*atr_mult

# ==============================================================================
# 🔴 BUG FIX #4: WALK-FORWARD QUE TESTA CADA TIPO DE SETUP
# ==============================================================================

def run_walk_forward_v21(df, bias, profile, n_folds=4):
    """V24: Walk-forward with BC-AWARE setups (FIX #1 CRITICAL).
    Adds DRIFT_RIDE, POST_SPIKE_FADE, SPIKE_CATCH to backtest.
    FIX #10: Correct Sharpe annualization using PPY.
    Slippage added, SL without look-ahead, honest results"""
    spread = profile.get('spread', 0.05)
    sl_mult = profile.get('sl_atr_mult', 2.5)
    fold_size = len(df) // (n_folds + 1)
    all_trades = []
    is_bc = profile.get('gen_type', 'GBM') in ["BOOM", "CRASH"]
    is_boom = profile.get('gen_type') == "BOOM"

    # V24: Detect PPY for correct Sharpe annualization
    ppy = detect_periods_per_year(df)

    for fold in range(n_folds):
        ts = fold_size * (fold + 1)
        te = fold_size * (fold + 2) if fold < n_folds - 1 else len(df)
        if ts >= len(df) - 80:
            break
        si = max(200, ts)

        # V21 FIX-A: Recalcular edge tests usando APENAS dados de treino
        train_data = df.iloc[:ts]
        fold_vr = variance_ratio_test(train_data['close'])
        fold_acf = autocorrelation_analysis(train_data['close'])

        for i in range(si, min(te, len(df) - 60)):
            row = df.iloc[i]
            if pd.isna(row['ADX']) or pd.isna(row['ATR']) or row['ATR'] == 0:
                continue
            sig = None
            atr = row['ATR']
            entry = sl = risk = 0
            setup = "NONE"

            # ═══ V24 FIX #1: BC-SPECIFIC SETUPS IN WALK-FORWARD ═══
            if is_bc and i >= 30:
                # Use clean ATR for BC
                lookback_data = df.iloc[max(0, i-50):i+1]
                ranges = (lookback_data['high'] - lookback_data['low']).values
                median_range = float(np.median(ranges)) if len(ranges) > 5 else atr
                clean_mask = ranges < (2.0 * median_range)
                bc_atr = float(np.mean(ranges[clean_mask])) if clean_mask.sum() > 5 else median_range

                # BC-SETUP A: DRIFT_RIDE — follow natural drift
                if not sig:
                    recent = df.iloc[max(0, i-20):i+1]
                    ema_f = recent['close'].ewm(span=profile.get('drift_ema_fast', 5)).mean()
                    ema_s = recent['close'].ewm(span=profile.get('drift_ema_slow', 15)).mean()
                    rsi_val = row['RSI'] if pd.notna(row['RSI']) else 50
                    if is_boom:
                        drift_ok = ema_f.iloc[-1] < ema_s.iloc[-1]  # Boom drifts DOWN
                        safe = rsi_val > 35
                        if drift_ok and safe:
                            sig = "SELL"; setup = "BC_DRIFT"
                    else:
                        drift_ok = ema_f.iloc[-1] > ema_s.iloc[-1]  # Crash drifts UP
                        safe = rsi_val < 65
                        if drift_ok and safe:
                            sig = "BUY"; setup = "BC_DRIFT"

                # BC-SETUP B: POST_SPIKE_FADE — fade after spike
                if not sig:
                    spike_min = profile.get('spike_size_min_atr', 2.0)
                    for k in range(max(0, i-5), i):
                        move = df['close'].iloc[k+1] - df['close'].iloc[k] if k+1 <= i else 0
                        abs_move = abs(move)
                        candles_since = i - k - 1
                        if bc_atr > 0 and abs_move > spike_min * bc_atr and candles_since <= 4:
                            # Check no continuation (simplified absorption)
                            cont_count = 0
                            for c in range(k+1, min(k+4, i+1)):
                                post_m = df['close'].iloc[c] - df['close'].iloc[c-1] if c > 0 else 0
                                if (move > 0 and post_m > 0) or (move < 0 and post_m < 0):
                                    cont_count += 1
                            if cont_count < 2:
                                if is_boom and move > 0:
                                    sig = "SELL"; setup = "BC_FADE"
                                elif not is_boom and move < 0:
                                    sig = "BUY"; setup = "BC_FADE"
                            break

                # BC-SETUP C: SPIKE_CATCH — catch imminent spike
                if not sig:
                    rsi_val = row['RSI'] if pd.notna(row['RSI']) else 50
                    # Count drift candles
                    drift_count = 0
                    for k in range(i, max(i-15, 0), -1):
                        if is_boom and df['close'].iloc[k] < df['open'].iloc[k]:
                            drift_count += 1
                        elif not is_boom and df['close'].iloc[k] > df['open'].iloc[k]:
                            drift_count += 1
                        else:
                            break
                    if is_boom and rsi_val < 25 and drift_count >= 5:
                        sig = "BUY"; setup = "BC_SPIKE"
                    elif not is_boom and rsi_val > 75 and drift_count >= 5:
                        sig = "SELL"; setup = "BC_SPIKE"

            # LEGACY SETUP 1: TREND
            if not sig and row['ADX'] > max(profile.get('adx_strong', 25), 22):
                if bias == "BULLISH" and row['close'] > row['EMA_200'] and row['RSI'] < 60:
                    sig = "BUY"; setup = "SWING"
                elif bias == "BEARISH" and row['close'] < row['EMA_200'] and row['RSI'] > 40:
                    sig = "SELL"; setup = "SWING"

            # LEGACY SETUP 2: MEAN REVERSION
            if not sig and 'ZSCORE' in df.columns:
                z = row['ZSCORE']
                if pd.notna(z) and abs(z) > profile.get('zscore_extreme', 2.0) * 0.7:
                    if z < -1.5:
                        sig = "BUY"; setup = "MEAN_REVERSION"
                    elif z > 1.5:
                        sig = "SELL"; setup = "MEAN_REVERSION"

            # LEGACY SETUP 3: VOL COMPRESS
            if not sig and fold_vr.get('has_edge') and fold_vr.get('dominant_type') == 'MEAN_REVERT':
                z = row.get('ZSCORE', 0)
                if pd.notna(z) and z < -1.0:
                    sig = "BUY"; setup = "VOL_COMPRESS"
                elif pd.notna(z) and z > 1.0:
                    sig = "SELL"; setup = "VOL_COMPRESS"

            # LEGACY SETUP 4: ACF MOMENTUM
            if not sig and fold_acf.get('has_pattern') and fold_acf.get('dominant_type') == 'MOMENTUM':
                if i >= 2:
                    prev_ret = df['close'].iloc[i] - df['close'].iloc[i-1]
                    if prev_ret > atr * 0.3:
                        sig = "BUY"; setup = "ACF_MOMENTUM"
                    elif prev_ret < -atr * 0.3:
                        sig = "SELL"; setup = "ACF_MOMENTUM"

            if not sig:
                continue

            # V23: Slippage realista (0.3× ATR)
            slippage = atr * 0.3
            entry = row['close'] + (spread + slippage if sig == "BUY" else -(spread + slippage))

            # V23 FIX: SL sem look-ahead
            past_data = df.iloc[max(0,i-20):i+1]

            # V24 M5: Regime-aware SL for BC setups
            if setup.startswith("BC_"):
                if setup == "BC_DRIFT":
                    sl_m = profile.get('sl_scalp_mult', 1.0) * 0.8  # Tight for drift
                elif setup == "BC_FADE":
                    sl_m = profile.get('sl_scalp_mult', 1.0) * 1.2  # Wider post-spike
                elif setup == "BC_SPIKE":
                    sl_m = profile.get('sl_atr_mult', 1.5) * 1.3  # Widest for spike catch
                else:
                    sl_m = sl_mult
            else:
                sl_m = sl_mult

            if sig == "BUY":
                sl_base = past_data['low'].min() - atr * 0.5
                sl = max(entry - sl_m * atr, sl_base)
            else:
                sl_base = past_data['high'].max() + atr * 0.5
                sl = min(entry + sl_m * atr, sl_base)

            risk = abs(entry - sl)
            if risk == 0: risk = atr

            # V24: Setup-specific TP/trailing
            tp_configs = {
                "BC_DRIFT": (1.5, 2.5, 1.0),   # Tight TP, tight trail
                "BC_FADE": (1.2, 2.0, 1.2),     # Conservative fade
                "BC_SPIKE": (3.0, 6.0, 2.5),    # Wide TP for spike catch
                "SWING": (profile.get('tp1_r', 3.0), profile.get('tp2_r', 5.0), 2.5),
                "MEAN_REVERSION": (2.0, 3.0, 1.2),
                "VOL_COMPRESS": (2.0, 3.5, 1.5),
                "ACF_MOMENTUM": (2.0, 3.5, 2.0),
            }
            tp1_r, tp2_r, trail_mult = tp_configs.get(setup, (3.0, 5.0, 2.0))
            tp1 = entry + tp1_r * risk if sig == "BUY" else entry - tp1_r * risk
            tp2 = entry + tp2_r * risk if sig == "BUY" else entry - tp2_r * risk

            # V24: Max hold by setup type
            max_hold = {"BC_DRIFT": 30, "BC_FADE": 15, "BC_SPIKE": 50}.get(
                setup, profile.get('max_hold_day', 80))

            p1_open, p2_open = True, True
            r1, r2 = 0, 0
            csl = sl
            for f in range(i + 1, min(i + max_hold, len(df))):
                nx = df.iloc[f]
                if sig == "BUY":
                    if nx['low'] <= csl:
                        if p1_open: r1 = (csl - entry) / risk
                        if p2_open: r2 = (csl - entry) / risk
                        break
                    if p1_open and nx['high'] >= tp1:
                        r1 = tp1_r - spread/risk; p1_open = False; csl = entry + spread
                    if not p1_open and p2_open:
                        csl = max(csl, nx['high'] - trail_mult * atr)
                        if nx['high'] >= tp2:
                            r2 = tp2_r - spread/risk; p2_open = False; break
                else:
                    if nx['high'] >= csl:
                        if p1_open: r1 = (entry - csl) / risk
                        if p2_open: r2 = (entry - csl) / risk
                        break
                    if p1_open and nx['low'] <= tp1:
                        r1 = tp1_r - spread/risk; p1_open = False; csl = entry - spread
                    if not p1_open and p2_open:
                        csl = min(csl, nx['low'] + trail_mult * atr)
                        if nx['low'] <= tp2:
                            r2 = tp2_r - spread/risk; p2_open = False; break

            result = r1 * 0.5 + r2 * 0.5
            if not (p1_open and p2_open):
                all_trades.append({'fold': fold, 'result': result, 'setup': setup, 'win': result > 0})

    if not all_trades:
        return {"WR":0,"NET":0,"DD":0,"PF":0,"SHARPE":0,"SORTINO":0,"TOTAL_TRADES":0,
                "WF_STABLE":False,"FOLD_WRS":[],"RESULTS":[]}

    results = [t['result'] for t in all_trades]
    wins = [r for r in results if r > 0]
    losses = [r for r in results if r <= 0]
    wr = len(wins)/len(results)*100
    net = sum(results)
    gp = sum(wins) if wins else 0
    gl = abs(sum(losses)) if losses else 0
    pf = gp/gl if gl > 0 else (gp if gp > 0 else 0)
    cum = np.cumsum(results)
    peak = np.maximum.accumulate(cum)
    dd = float((peak - cum).max()) if len(cum) > 0 else 0
    rs = pd.Series(results)
    # V24 FIX #10: Correct Sharpe annualization using PPY (not √252)
    sharpe = float(rs.mean()/rs.std()*np.sqrt(ppy)) if len(rs) >= 2 and rs.std() > 0 else 0
    ds = rs[rs<0]
    sortino = float(rs.mean()/ds.std()*np.sqrt(ppy)) if len(ds) >= 2 and ds.std() > 0 else 0

    # Per-fold WRs
    fold_wrs = []
    for fold_id in range(n_folds):
        ft = [t for t in all_trades if t['fold'] == fold_id]
        if ft:
            fold_wrs.append(round(sum(1 for t in ft if t['win'])/len(ft)*100, 1))

    # Per-setup stats
    setup_stats = {}
    for setup_name in set(t['setup'] for t in all_trades):
        st_list = [t for t in all_trades if t['setup'] == setup_name]
        sw = [t for t in st_list if t['win']]
        sl_list = [abs(t['result']) for t in st_list if not t['win']]
        sw_vals = [t['result'] for t in sw]
        setup_stats[setup_name] = {
            "trades": len(st_list),
            "wr": round(len(sw)/len(st_list)*100,1) if st_list else 0,
            "avg_win": round(np.mean(sw_vals), 2) if sw_vals else 0,
            "avg_loss": round(np.mean(sl_list), 2) if sl_list else 0,
        }

    # V24 A3: Expectancy with stress test
    avg_w = np.mean([r for r in results if r > 0]) if wins else 0
    avg_l = np.mean([abs(r) for r in results if r <= 0]) if losses else 1
    exp_data = calculate_expectancy(wr, avg_w, avg_l)

    return {"WR":round(wr,1),"NET":round(net,1),"DD":round(dd,1),"PF":round(pf,2),
            "SHARPE":round(sharpe,2),"SORTINO":round(sortino,2),"TOTAL_TRADES":len(results),
            "WF_STABLE":len(fold_wrs)>=2 and all(w>30 for w in fold_wrs),
            "FOLD_WRS":fold_wrs,"SETUP_STATS":setup_stats,"RESULTS":results,
            "EXPECTANCY":exp_data.get('expectancy',0),
            "EXPECTANCY_STRESSED":exp_data.get('expectancy_stressed',0),
            "HIGH_RISK":exp_data.get('high_risk',False),
            "AVG_WIN":round(avg_w,2),"AVG_LOSS":round(avg_l,2)}

# ==============================================================================
# 🔴 BUG FIX #6: MONTE CARLO BOOTSTRAP REAL
# ==============================================================================

def monte_carlo_bootstrap(results, n_sim=1000, n_trades=50):
    """Bootstrap dos resultados REAIS do backtest"""
    try:
        if len(results) < 5:
            return {"median":0,"p5":0,"p95":0,"p25":0,"p75":0,"positive_pct":0}
        arr = np.array(results)
        sims = np.array([np.sum(np.random.choice(arr, size=min(n_trades, len(arr)), replace=True))
                         for _ in range(n_sim)])
        return {"median":round(float(np.median(sims)),1),
                "p5":round(float(np.percentile(sims,5)),1),
                "p95":round(float(np.percentile(sims,95)),1),
                "p25":round(float(np.percentile(sims,25)),1),
                "p75":round(float(np.percentile(sims,75)),1),
                "positive_pct":round(float(np.mean(sims>0)*100),1)}
    except:
        return {"median":0,"p5":0,"p95":0,"p25":0,"p75":0,"positive_pct":0}

# ==============================================================================
# SCORING V20 — 16 fatores (14 + VR + ACF)
# ==============================================================================

@dataclass
class SetupScore:
    trend_strength:float; momentum_align:float; patterns:float
    value_zone:float; historical:float; base_total:float
    divergence_bonus:float; fib_bonus:float; sr_bonus:float
    alignment_bonus:float; storm_bonus:float; regime_bonus:float
    volume_bonus:float; hurst_bonus:float; zscore_bonus:float
    consecutive_bonus:float; generator_bonus:float; distribution_bonus:float
    vr_bonus:float; acf_bonus:float
    cpi_bonus:float; markov_bonus:float; spectral_bonus:float
    adx_slope_bonus:float; ribbon_bonus:float; coherence_bonus:float
    candle_bonus:float; mom_accel_bonus:float
    bonus_total:float; total:float; grade:str

def calculate_score(adx, momentum_score, pattern_score, dist_ema50, atr,
                    win_rate, profit_factor, profile, **bonuses):
    ts=25 if adx>profile.get('adx_strong',25) else(15 if adx>profile.get('adx_trend_min',15) else 0)
    mp=(momentum_score/3)*20
    dr=dist_ema50/atr if atr>0 else 999
    vs=15 if dr<0.5 else(10 if dr<1.0 else(5 if dr<1.5 else 0))
    hs=min((win_rate*0.15)+(profit_factor*5),25)
    base=ts+mp+pattern_score+vs+hs

    # V23: BONUS GROUPS com caps por categoria (anti-inflação)
    grp_trend = min(20, bonuses.get('ribbon_bonus',0) + bonuses.get('coherence_bonus',0) +
                    bonuses.get('alignment_bonus',0) + bonuses.get('adx_slope_bonus',0))
    grp_stat = min(20, bonuses.get('vr_bonus',0) + bonuses.get('acf_bonus',0) +
                   bonuses.get('hurst_bonus',0) + bonuses.get('cpi_bonus',0))
    grp_struct = min(18, bonuses.get('fib_bonus',0) + bonuses.get('sr_bonus',0) +
                     bonuses.get('divergence_bonus',0))
    grp_gen = min(12, bonuses.get('generator_bonus',0))
    grp_mom = min(18, bonuses.get('mom_accel_bonus',0) + bonuses.get('candle_bonus',0) +
                  bonuses.get('volume_bonus',0) + bonuses.get('zscore_bonus',0) +
                  bonuses.get('consecutive_bonus',0))
    grp_dist = min(10, bonuses.get('distribution_bonus',0))
    grp_market = min(8, bonuses.get('regime_bonus',0) + bonuses.get('markov_bonus',0) +
                     bonuses.get('spectral_bonus',0))
    grp_storm = min(25, bonuses.get('storm_bonus',0))
    # V23 new bonuses
    grp_v23 = min(20, bonuses.get('market_structure_bonus',0) + bonuses.get('pullback_bonus',0) +
                  bonuses.get('sweep_bonus',0) + bonuses.get('entry_sync_bonus',0) +
                  bonuses.get('continuation_bonus',0) + bonuses.get('candle_mom_bonus',0) +
                  bonuses.get('retest_bonus',0))

    bonus = grp_trend + grp_stat + grp_struct + grp_gen + grp_mom + grp_dist + grp_market + grp_storm + grp_v23
    total=base+bonus
    if total>=190: g="S"
    elif total>=155: g="A++"
    elif total>=125: g="A+"
    elif total>=95: g="A"
    elif total>=65: g="B"
    elif total>=45: g="C"
    else: g="D"

    all_keys=['divergence_bonus','fib_bonus','sr_bonus','alignment_bonus','storm_bonus',
          'regime_bonus','volume_bonus','hurst_bonus','zscore_bonus','consecutive_bonus',
          'generator_bonus','distribution_bonus','vr_bonus','acf_bonus',
          'cpi_bonus','markov_bonus','spectral_bonus',
          'adx_slope_bonus','ribbon_bonus','coherence_bonus','candle_bonus','mom_accel_bonus']
    return SetupScore(ts,mp,pattern_score,vs,hs,base,
        *[bonuses.get(k,0) for k in all_keys],bonus,total,g)

# ==============================================================================
# STORM DETECTOR V20
# ==============================================================================

def calculate_storm_bonus(sd):
    met, lst = 0, []
    checks = [
        (sd.get('adx',0)>30,"ADX>30"),(sd.get('momentum_score',0)==3,"Mom 3/3"),
        (sd.get('pattern_score',0)>=10,"Padrões"),(sd.get('divergence') is not None,"Div"),
        (sd.get('fib'),"Fib"),(sd.get('sr_touch'),"S/R"),(sd.get('alignment'),"Align"),
        (sd.get('bb_squeeze'),"BB Squeeze"),(sd.get('trending'),"Trending"),
        (sd.get('volume'),"Volume"),(sd.get('hurst_trending'),"Hurst"),
        (sd.get('zscore'),"Z-Score"),(sd.get('gen_signal'),"Generator"),
        (sd.get('dist'),"Distrib"),(sd.get('vr_edge'),"VR Edge"),(sd.get('acf_edge'),"ACF Edge"),
        # V21+ new checks
        (sd.get('ribbon_quality') in ["EXCELLENT","GOOD"],"EMA Ribbon"),
        (sd.get('coherence') in ["PERFECT","STRONG"],"TF Coherence"),
        (sd.get('candle_quality') in ["EXCELLENT","GOOD"],"Candle Struct"),
        (sd.get('mom_accel'),"Mom Accel"),
        # V23 new checks
        (sd.get('mkt_struct'),"Mkt Structure"),
        (sd.get('candle_mom'),"Candle Mom"),
        (sd.get('pullback'),"Pullback Q"),
        (sd.get('entry_sync'),"Entry Sync"),
    ]
    for c,l in checks:
        if c: met+=1; lst.append(l)
    if met>=15: return "PERFECT_STORM",25,lst
    elif met>=12: return "STRONG_CONFLUENCE",20,lst
    elif met>=9: return "GOOD_CONFLUENCE",15,lst
    elif met>=6: return "MODERATE",10,lst
    return None,0,lst

# ==============================================================================
# CHART V20
# ==============================================================================

def plot_candles(df, title, entry=None, sl=None, tp1=None, tp2=None, sr_levels=None, fib_levels=None):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), height_ratios=[3.5, 1],
                                     facecolor='#09090b', gridspec_kw={'hspace': 0.08})
    ax1.set_facecolor('#09090b')
    ax2.set_facecolor('#09090b')

    # Candles — thin, clean
    for i in range(len(df)):
        bull = df['close'].iloc[i] >= df['open'].iloc[i]
        c = '#22c55e' if bull else '#ef4444'
        ca = 0.9 if i > len(df) - 30 else 0.45  # Fade older candles
        ax1.plot([df.index[i]]*2, [df['low'].iloc[i], df['high'].iloc[i]], color=c, lw=0.6, alpha=ca)
        ax1.plot([df.index[i]]*2, [df['open'].iloc[i], df['close'].iloc[i]], color=c, lw=2.8, alpha=ca, solid_capstyle='round')

    # EMAs — subtle
    ax1.plot(df.index, df['EMA_20'], color='#3b82f6', lw=1, alpha=0.5, label='20')
    ax1.plot(df.index, df['EMA_50'], color='#f59e0b', lw=1, alpha=0.4, label='50')
    ax1.plot(df.index, df['EMA_200'], color='#6b7280', lw=1.2, alpha=0.3, label='200')

    # BB — very subtle fill
    ax1.fill_between(df.index, df['BB_upper'], df['BB_lower'], alpha=0.02, color='#a1a1aa')

    # S/R — clean zones
    if sr_levels:
        for sr in sr_levels[:3]:
            c = '#ef4444' if sr['type'] == 'RESISTANCE' else '#22c55e'
            ax1.axhspan(sr['zone_low'], sr['zone_high'], alpha=0.04, color=c, linewidth=0)
            ax1.axhline(y=sr['price'], color=c, ls='-', alpha=0.15, lw=0.5)

    # Fib — dotted, faint
    if fib_levels:
        for n, p in fib_levels.items():
            if pd.notna(p):
                ax1.axhline(y=p, color='#a1a1aa', ls=':', alpha=0.12, lw=0.5)

    # Trade levels — clean, minimal
    if entry:
        ax1.axhline(y=entry, color='#fafafa', ls='-', lw=1.5, alpha=0.9)
        ax1.text(df.index[-1], entry, '  ENTRY', fontsize=8, color='#fafafa',
                 fontweight='500', va='center', fontfamily='Inter')
    if sl:
        ax1.axhline(y=sl, color='#ef4444', ls='-', lw=1.2, alpha=0.7)
        ax1.text(df.index[-1], sl, '  SL', fontsize=8, color='#ef4444',
                 fontweight='500', va='center', fontfamily='Inter')
    if tp1:
        ax1.axhline(y=tp1, color='#22c55e', ls='--', lw=1, alpha=0.6)
        ax1.text(df.index[-1], tp1, '  TP1', fontsize=8, color='#22c55e',
                 fontweight='500', va='center', fontfamily='Inter')
    if tp2:
        ax1.axhline(y=tp2, color='#22c55e', ls='-', lw=1.2, alpha=0.7)
        ax1.text(df.index[-1], tp2, '  TP2', fontsize=8, color='#22c55e',
                 fontweight='500', va='center', fontfamily='Inter')

    # Title — minimal
    ax1.text(0.01, 0.97, title, transform=ax1.transAxes, fontsize=11,
             color='#a1a1aa', fontweight='400', va='top', fontfamily='Inter')
    ax1.legend(loc='upper right', fontsize=7, facecolor='#09090b', edgecolor='#1e1e23',
               labelcolor='#52525b', framealpha=0.8)

    # Grid — barely visible
    ax1.grid(True, alpha=0.04, color='#27272a', linewidth=0.5)
    ax1.tick_params(colors='#3f3f46', labelsize=8, length=0)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['bottom'].set_color('#1e1e23')
    ax1.spines['left'].set_color('#1e1e23')

    # MACD — clean bars
    hist = df['MACD_hist']
    colors = ['#22c55e' if x > 0 else '#ef4444' for x in hist]
    alphas = [0.6 if abs(x) > hist.abs().mean() else 0.3 for x in hist]
    for i, (idx, val) in enumerate(zip(df.index, hist)):
        ax2.bar(idx, val, color=colors[i], alpha=alphas[i], width=0.8)
    ax2.plot(df.index, df['MACD'], color='#3b82f6', lw=0.8, alpha=0.6)
    ax2.plot(df.index, df['MACD_signal'], color='#a1a1aa', lw=0.8, alpha=0.4)
    ax2.axhline(y=0, color='#27272a', lw=0.5)
    ax2.grid(True, alpha=0.03, color='#27272a', linewidth=0.5)
    ax2.tick_params(colors='#3f3f46', labelsize=7, length=0)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.spines['bottom'].set_color('#1e1e23')
    ax2.spines['left'].set_color('#1e1e23')

    plt.xticks(rotation=45)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=140, facecolor='#09090b', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf)

def convert_np(obj):
    if isinstance(obj,dict): return {k:convert_np(v) for k,v in obj.items()}
    elif isinstance(obj,list): return [convert_np(i) for i in obj]
    elif isinstance(obj,np.integer): return int(obj)
    elif isinstance(obj,np.floating): return float(obj)
    elif isinstance(obj,np.ndarray): return obj.tolist()
    elif isinstance(obj,np.bool_): return bool(obj)
    elif isinstance(obj,float) and pd.isna(obj): return None
    return obj

# ==============================================================================
# 🔧 GEMINI AI — RETRY + FALLBACK + COMPRESSION ENGINE
# ==============================================================================

# Modelos em ordem de preferência (fallback automático)
GEMINI_MODELS = [
    "models/gemini-2.0-flash",
    "models/gemini-3.0-flash",
    "models/gemini-3.0-pro",
    "models/gemini-3.1-pro",
]

def compress_image_for_ai(img, max_size=800):
    """Reduz tamanho da imagem para diminuir payload ao Gemini.
    Imagem 14×8 @ 140 DPI = ~1960×1120 px → reduz para max 800px lado maior."""
    try:
        w, h = img.size
        if max(w, h) <= max_size:
            return img
        ratio = max_size / max(w, h)
        new_w, new_h = int(w * ratio), int(h * ratio)
        resample = getattr(Image, 'LANCZOS', getattr(Image, 'ANTIALIAS', None))
        resized = img.resize((new_w, new_h), resample)
        return resized
    except:
        return img

def trim_data_for_ai(data):
    """Remove campos pesados/redundantes que a IA não precisa para análise.
    Mantém apenas os campos essenciais para o prompt."""
    essential_keys = [
        "FINAL_DECISION", "TRADE_STYLE", "SETUP_TYPE", "SETUP_SCORE", "SETUP_GRADE",
        "INDEX_PROFILE", "GEN_TYPE", "GEN_SIGNAL", "GEN_BONUS", "SIGMA_CALIBRATED",
        "VR_TEST", "ACF_TEST", "VOL_CLUSTER", "DIST_ANALYSIS",
        "HURST", "HURST_REGIME", "HURST_R2", "ZSCORE",
        "BB_CYCLE", "CONSECUTIVE", "CONSECUTIVE_DIR", "ROC_STATUS",
        "MARKET_STRUCTURE", "MARKET_REGIME", "MOMENTUM", "MOMENTUM_V21",
        "TRIGGER_OK", "TRIGGER_TYPE", "CONFLUENCES", "RISKS",
        "ENTRY_TYPE", "SL_REASON",
        "WIN_RATE", "NET_PROFIT", "MAX_DRAWDOWN", "PROFIT_FACTOR",
        "SHARPE", "SORTINO", "WF_STABLE", "TOTAL_TRADES",
        "MC_MEDIAN", "MC_P5", "MC_P95", "MC_POSITIVE",
        "ENTRY", "SL", "TP1", "TP2", "ATR",
        "CPI_VAL", "REGIME_TRANSITION", "BIAS_CONFIDENCE", "BIAS_SCORE",
        "HOLDING_PERIOD", "SCORE_BREAKDOWN",
        "ADX_SLOPE", "EMA_RIBBON", "TREND_COHERENCE", "CANDLE_STRUCTURE",
        "MOM_ACCELERATION", "ATR_CHANNEL", "VWAP_ZONE",
        # V23 sniper data
        "MKT_STRUCTURE", "CANDLE_MOMENTUM", "PULLBACK_QUALITY",
        "LIQ_SWEEP", "ENTRY_SYNC", "CONT_PATTERN",
        "EARLY_REVERSAL", "REVERSAL_DIR", "RW_PENALTY",
        "ENTRY_AGGRESSIVE", "ENTRY_IDEAL", "ENTRY_SNIPER",
        "TRAIL_BE", "TRAIL_1R", "MC_CONFIDENCE",
        # V24-BC: Boom/Crash engine data (critical for AI analysis)
        "BC_SPIKE", "BC_DRIFT", "BC_FADE", "BC_SD_ZONES",
        "BC_FREQ", "BC_ABSORB", "BC_MULTI", "BC_STOCH",
        # V24-BC: Audit-driven data
        "BC_REGIME", "BC_KURTOSIS", "BC_CONFLICTS", "BC_CLEAN_ATR",
        "EXPECTANCY", "EXPECTANCY_STRESSED", "HIGH_RISK", "MELTDOWN",
    ]
    trimmed = {}
    for k in essential_keys:
        if k in data:
            v = data[k]
            # Truncar dicts muito grandes (ex: VR_TEST com arrays)
            if isinstance(v, dict):
                clean = {}
                for dk, dv in v.items():
                    if isinstance(dv, list) and len(dv) > 10:
                        clean[dk] = dv[:5]  # Só primeiros 5 elementos
                    else:
                        clean[dk] = dv
                trimmed[k] = clean
            else:
                trimmed[k] = v
    return trimmed

def call_gemini_with_retry(api_key, system_prompt, data, images, status_widget=None,
                            max_retries=2, base_timeout=120):
    """Chama Gemini com retry, fallback de modelos, e compressão de payload.
    
    Fluxo:
    1. Comprime imagens (1960px → 800px)
    2. Trima dados (remove campos pesados)
    3. Tenta modelo primário com retry
    4. Se falhar, tenta modelos fallback
    5. Se tudo falhar, retorna análise sem IA
    """
    genai.configure(api_key=api_key)
    
    # Comprimir imagens para reduzir payload (~60% menor)
    compressed_imgs = [compress_image_for_ai(img, max_size=800) for img in images]
    
    # Trimar dados para reduzir JSON (~40% menor)
    trimmed_data = trim_data_for_ai(data)
    json_payload = json.dumps(trimmed_data, ensure_ascii=False)
    
    # Limitar tamanho do JSON (Gemini tem limite de contexto)
    if len(json_payload) > 15000:
        json_payload = json_payload[:15000] + "...(truncated)"
    
    content = [system_prompt, f"ANALYSIS DATA: {json_payload}"] + compressed_imgs
    
    last_error = None
    
    for model_name in GEMINI_MODELS:
        for attempt in range(max_retries + 1):
            try:
                if status_widget:
                    model_short = model_name.split("/")[-1].split("-preview")[0]
                    if attempt > 0:
                        status_widget.write(f"🔄 Retry {attempt}/{max_retries} ({model_short})...")
                    else:
                        status_widget.write(f"🤖 Gerando análise IA ({model_short})...")
                
                model = genai.GenerativeModel(
                    model_name,
                    safety_settings=SAFETY_SETTINGS,
                )
                
                # Tentar com timeout configurável (compatível com versões recentes)
                try:
                    response = model.generate_content(
                        content,
                        request_options={"timeout": base_timeout}
                    )
                except TypeError:
                    # Versão antiga da lib não suporta request_options
                    response = model.generate_content(content)
                
                if response and response.text:
                    if status_widget:
                        status_widget.write(f"✅ Análise gerada com {model_short}")
                    return response.text, None
                    
            except Exception as e:
                last_error = str(e)
                error_lower = last_error.lower()
                
                # 503 = high demand → tentar próximo modelo imediatamente
                if "503" in last_error or "high demand" in error_lower or "overloaded" in error_lower:
                    if status_widget:
                        status_widget.write(f"⚠️ {model_name.split('/')[-1]} sobrecarregado, tentando próximo...")
                    break  # Pula para próximo modelo (não faz retry no mesmo)
                
                # Timeout → retry com backoff
                if "timeout" in error_lower or "deadline" in error_lower:
                    if attempt < max_retries:
                        wait = (attempt + 1) * 5  # 5s, 10s
                        if status_widget:
                            status_widget.write(f"⏱️ Timeout, aguardando {wait}s...")
                        time.sleep(wait)
                        continue
                    else:
                        break  # Esgotou retries, tenta próximo modelo
                
                # Rate limit → esperar e retry
                if "429" in last_error or "rate" in error_lower:
                    wait = (attempt + 1) * 10
                    if status_widget:
                        status_widget.write(f"⏳ Rate limit, aguardando {wait}s...")
                    time.sleep(wait)
                    continue
                
                # Outro erro → retry simples
                if attempt < max_retries:
                    time.sleep(3)
                    continue
                else:
                    break
    
    # Todos os modelos falharam — retornar análise básica sem IA
    return None, last_error

# ==============================================================================
# SYSTEM PROMPT V24-BC
# ==============================================================================

SYSTEM_PROMPT = """
FUNÇÃO: ANALISTA V24-BC — BOOM/CRASH PRECISION SNIPER [Gemini + Fallback]
Missão: Sinais de alta precisão EXCLUSIVOS para Boom e Crash indices da Deriv
APENAS Day Trade + Scalp — SEM Swing Trade

**RESPONDA SEMPRE EM PORTUGUÊS BRASILEIRO**

**REGRAS BOOM/CRASH:**
- BOOM: Preço faz DRIFT para BAIXO e SPIKE para CIMA
  → SELL = seguir o drift (mais seguro)
  → BUY = capturar o spike (maior R:R)
- CRASH: Preço faz DRIFT para CIMA e SPIKE para BAIXO
  → BUY = seguir o drift (mais seguro)
  → SELL = capturar o crash (maior R:R)

**ENGINES ESPECIALIZADOS:**
- Spike Detection (RSI extreme + drift duration + BB squeeze + Poisson timing)
- Drift Analyzer (força e qualidade do drift — count + magnitude)
- Post-Spike Fade (trade após spike/crash — com validação absorção)
- Supply/Demand Zones (níveis institucionais — com decay temporal)
- Spike Frequency (timing baseado em frequência empírica M15)
- Stochastic Timer (combinação Stoch + RSI — lookback paramétrico)
- Absorption Detector (pressão institucional)
- Multi-Spike Pattern (clusters de spikes — com gap tolerance)
- Returns Kurtosis (detecção de fat-tails = spike-prone regime)
- BC Regime Classifier (DRIFT_SMOOTH / CHOPPY / PRE_SPIKE / POST_SPIKE / SPIKE_CLUSTER)
- Engine Conflict Resolution (SPIKE vs DRIFT, FADE vs CLUSTER, etc.)

**V24 MELHORIAS:**
- Walk-forward agora testa setups BC (DRIFT_RIDE, POST_SPIKE, SPIKE_CATCH)
- Kelly Criterion corrigido (usa avg_win/avg_loss, não PF)
- Sharpe/Sortino com annualização PPY correta
- Expectância explícita + stress test -20% WR
- Clean ATR (mediano, exclui spikes) para thresholds mais estáveis
- Anti-Meltdown Kill-Switch (3 losses = score +50%, 5 losses = bloqueio)
- Regime-Aware SL (drift=tight, post-spike=wide)

**FORMATO:**

## ⚡ VEREDICTO V24-BC: [ {DECISION} ]
**Grade:** {GRADE} | **Score:** {SCORE} | **Tipo:** {BOOM/CRASH}
**Setup:** {DRIFT_RIDE / SPIKE_CATCH / POST_SPIKE / SCALP / DAY / REVERSAL}
**BC Regime:** {DRIFT_SMOOTH/CHOPPY/PRE_SPIKE/POST_SPIKE/SPIKE_CLUSTER}

### 🎯 SPIKE ANALYSIS
- Spike Detector: {prob}% iminente ({IMMINENT/SOON/NORMAL})
- Último spike há: {N} candles (média empírica: {avg} M15)
- RSI Zone: {EXTREME_LOW/LOW/NEUTRAL/HIGH/EXTREME_HIGH}
- Stoch Timer: K={k} D={d} → {SPIKE_BUY/DRIFT_SELL/WAIT}
- Kurtosis: {value} ({NORMAL/MODERATE/SPIKE_PRONE/EXTREME_SPIKE})

### 📊 DRIFT ANALYSIS
- Drift: {ACTIVE/INACTIVE} ({UP/DOWN}) Força: {strength}%
- Qualidade: {SMOOTH/MODERATE/CHOPPY}
- Seguro para ride: {SIM/NÃO}

### 🔄 POST-SPIKE FADE
- Post-spike detectado: {SIM/NÃO}
- Absorção confirmada: {SIM/NÃO}
- Direção fade: {BUY/SELL}
- Alvo fade: {price}

### 📐 RISK METRICS
- Expectancy: {value}R (Stressed: {stressed_value}R)
- Kill-Switch: {streak} losses ({OK/CAUTION/BLOCKED})
- Engine Conflicts: {conflicts or None}
- Clean ATR: {value} vs Raw ATR: {raw_value}

### 🎯 PLANO DE TRADE
Entry: {price} | SL: {price} | TP1: {price} | TP2: {price}
Trail BE: {price} | Trail 1R: {price}
Entries: Agressivo={E1} | Ideal={E2} | Sniper={E3}

### ⚠️ CONFLUÊNCIAS + RISCOS

*V24-BC Insight:* {Analisar especificamente o comportamento Boom/Crash.
Considerar BC Regime para adaptar recomendação.
Se regime PRE_SPIKE e prob > 60%, recomendar spike catch com SL adaptado.
Se DRIFT_SMOOTH e drift forte, recomendar drift ride com SL tight.
Se POST_SPIKE e absorção confirmada, recomendar fade com target calculado.
Se engine conflicts presentes, alertar e ajustar recomendação.
Se expectancy stressed < 0, alertar HIGH RISK.
NUNCA recomendar Swing Trade. Apenas Day Trade e Scalp.
Ser AGRESSIVO mas PRECISO — entrar com convicção.}
"""

# ==============================================================================
# SNIPER CORE V20.0 — STATISTICAL EDGE ENGINE
# ==============================================================================

def sniper_core_v20(name, h1_raw, h4_raw, m15_raw, m5_raw, capital=10000, risk_pct=1.0):
    profile = get_profile(name)
    h1 = indicators(prep_df(h1_raw))
    h4 = indicators(prep_df(h4_raw))
    m15 = indicators(prep_df(m15_raw))
    m5 = indicators(prep_df(m5_raw)) if m5_raw else None
    c1, c4, cm = h1.iloc[-1], h4.iloc[-1], m15.iloc[-1]
    c5 = m5.iloc[-1] if m5 is not None and len(m5) > 0 else None

    # V23: Multi-Speed Bias (substitui V21 dynamic bias)
    bias, bias_confidence, bias_score, early_reversal, reversal_dir = calculate_multi_speed_bias(h4, h1, m15, m5)
    bias_old = "BULLISH" if c4['close'] > c4['EMA_200'] else "BEARISH"
    if bias == "NEUTRAL": bias = bias_old  # fallback
    # V23: Early reversal override — se fast+medium concordam, seguir
    if early_reversal and reversal_dir:
        bias = reversal_dir
    adx = c4['ADX']
    structure = classify_market_structure(h1)
    regime, regime_sc = classify_regime(h1)
    momentum_old = check_momentum(h4, h1, m15, bias)
    momentum_v21 = enhanced_momentum_v21(h4, h1, m15, bias)
    momentum = momentum_old  # keep for scoring compatibility

    # 🔴 FIX #1: Auto-detect periods/year
    ppy = detect_periods_per_year(h1)

    # 🟠 FIX #1: CALIBRAR SIGMA REAL
    sigma_calibrated = calibrate_sigma(h1, ppy)

    # ═══ GENERATOR MODEL V20 ═══
    gen_type = profile.get('gen_type', 'GBM')
    if gen_type == "GBM":
        gen = GeneratorModelV20.analyze_gbm(h1, profile, sigma_calibrated, ppy)
    elif gen_type in ["BOOM", "CRASH"]:
        gen = GeneratorModelV20.analyze_crash_boom(h1, profile, ppy)
    elif gen_type == "STEP":
        gen = GeneratorModelV20.analyze_step(h1, profile, ppy)
    else:
        gen = {"signal": "NEUTRAL", "confidence": 0}

    # ═══ EDGE TESTS V20 ═══
    vr = variance_ratio_test(h1['close'])
    acf = autocorrelation_analysis(h1['close'])
    vol_cluster = volatility_clustering_test(h1['close'])
    dist = DistributionAnalyzer.analyze(h1)

    # ═══ V21 PREDICTABILITY ENGINES ═══
    cpi = compound_predictability_index(h1['close'], vr, acf)
    spectral = spectral_analysis_v21(h1['close'])
    markov = transition_matrix_v21(h1['close'])
    regime_transition, rt_mult, rt_detail = detect_regime_transition(h1)

    # ═══ CLASSIC STATS ═══
    hurst_val, hurst_regime, hurst_r2 = calculate_hurst_exponent(h1['close'])
    z_current = float(cm['ZSCORE']) if pd.notna(cm.get('ZSCORE')) else 0
    bb_cycle, bb_ratio, bb_squeeze_count = detect_bb_cycle(h1, profile)
    consec_count, consec_dir = count_consecutive(m15)
    roc_status, roc_details = detect_roc_extreme(m15, profile)

    # ═══ V21+ PRECISION ENGINES ═══
    adx_slope = adx_slope_analysis(h1)
    ema_ribbon = ema_ribbon_analysis(h1)
    trend_coherence = multi_tf_trend_coherence(h4, h1, m15, m5)
    vwap_data = vwap_proxy_analysis(h1)
    candle_struct = candle_structure_score(m15, bias)
    mom_accel = momentum_acceleration(h1)
    atr_channel = atr_channel_entry(h1, bias)

    # ═══ V23 SNIPER ENGINES ═══
    mkt_struct = detect_market_structure(h1)
    candle_mom = candle_momentum_engine(m15, bias, lookback=10)
    pb_quality = pullback_quality_score(m15, bias, c1['ATR'])
    liq_sweep = detect_liquidity_sweep(m15, c1['ATR'])
    entry_sync = entry_sync_score(h4, h1, m15, m5, bias)
    cont_pattern = detect_continuation_pattern(m15, bias, c1['ATR'])

    # ═══ V24-BC BOOM/CRASH ENGINES ═══
    # V24: Use clean ATR for BC engines (FIX #6)
    bc_atr_clean = bc_clean_atr(m15, profile, lookback=50)
    bc_spike = bc_spike_detector(m15, profile, lookback=30)
    bc_drift = bc_drift_analyzer(m15, profile, lookback=20)
    # V24 FIX #8: Pass absorption data to fade engine
    bc_absorb = bc_absorption_detector(m15, bias, lookback=10)
    bc_fade = bc_post_spike_fade(m15, profile, lookback=10, absorption_data=bc_absorb)
    bc_sd = bc_supply_demand_zones(h1, bc_atr_clean, lookback=50)
    bc_freq = bc_spike_frequency(m15, profile, lookback=100)
    bc_multi = bc_multi_spike_pattern(m15, profile, lookback=30)
    bc_stoch = bc_stochastic_timer(m15, profile)
    # V24 M4: Returns kurtosis analysis
    bc_kurt = bc_returns_kurtosis(m15, lookback=50)
    # V24 M5: BC Regime classifier
    bc_regime = bc_regime_classifier(m15, profile, bc_spike, bc_drift, bc_freq)
    # V24 O3: Engine conflict resolution
    bc_conflicts = bc_resolve_engine_conflicts(bc_spike, bc_drift, bc_fade, bc_multi, bc_absorb)

    # Divergências
    rsi_div, rsi_db, rsi_dd = detect_divergence(m15, 'RSI', 4)
    macd_div, macd_db, macd_dd = detect_divergence(m15, 'MACD', 4)
    divergence = rsi_div or macd_div
    div_bonus = max(rsi_db, macd_db); div_detail = rsi_dd or macd_dd

    # S/R, Fib
    sr_levels = detect_sr_clustered(h1)
    sr_bonus, sr_touch, closest_sr = 0, False, None
    if sr_levels:
        closest_sr = min(sr_levels, key=lambda x: abs(x['price']-c1['close']))
        if abs(closest_sr['price']-c1['close']) < c1['ATR']*0.5:
            sr_bonus = min(closest_sr['strength']*3, 15); sr_touch = True
    fibs, fib_dir, _ = calculate_fibonacci(h1)
    fib_level, fib_bonus = check_fib_confluence(c1['close'], fibs, c1['ATR'])

    align_type, align_bonus = detect_alignment(c4, c1, cm, bias)
    vol_st, vol_proxy = analyze_tick_volume(m15)
    vol_confirmed = vol_proxy > 1.3; vol_bonus = 5 if vol_confirmed else 0
    regime_bonus = 5 if "TRENDING" in regime else 0
    pat_score = min(cm.get('pattern_score', 0), 15)
    bb_compression = bb_cycle == "SQUEEZE"

    # BONUSES V20
    gen_bonus = 0; gen_signal = gen.get('signal', 'NEUTRAL')
    if gen_type == "GBM":
        if gen.get('consensus') in ["VOL_OVEREXTENDED","VOL_COMPRESSED"] and gen.get('consensus_confidence',0) > 30:
            gen_bonus = min(int(gen['consensus_confidence'] / 8), 12)
        if abs(gen.get('z_price',0)) > 2:
            gen_bonus += 5
    elif gen_type in ["BOOM","CRASH"]:
        if gen.get('spike_phase') in ["DRIFT_STRONG","DRIFT_NORMAL"]:
            gen_bonus = min(int(gen.get('decay_strength',0)*8), 12)
    elif gen_type == "STEP":
        if gen.get('signal') in ["EXTREME_DEVIATION","HIGH_DEVIATION"]:
            gen_bonus = min(int(gen.get('confidence',0)/8), 12)

    hurst_bonus = 0; hurst_trending = False
    if hurst_r2 >= 0.7:
        if hurst_val > profile.get('hurst_trend_min',0.53): hurst_bonus=10; hurst_trending=True
        elif hurst_val < 0.45: hurst_bonus=5

    zscore_bonus = 0; zscore_favorable = False
    if bias=="BULLISH" and z_current < -profile.get('zscore_extreme',2)*0.6:
        zscore_bonus=10; zscore_favorable=True
    elif bias=="BEARISH" and z_current > profile.get('zscore_extreme',2)*0.6:
        zscore_bonus=10; zscore_favorable=True

    consec_reversal = consec_count >= profile.get('consecutive_reversal',6)
    consecutive_bonus = 0
    if consec_reversal and ((bias=="BULLISH" and consec_dir=="BEARISH") or (bias=="BEARISH" and consec_dir=="BULLISH")):
        consecutive_bonus = 10

    dist_bonus = 0; dist_favorable = False
    if dist['tail_risk'] in ["FAT_TAILS","HEAVY_TAILS"]: dist_bonus += 3
    if dist['percentile'] < 10 and bias=="BULLISH": dist_bonus+=7; dist_favorable=True
    elif dist['percentile'] > 90 and bias=="BEARISH": dist_bonus+=7; dist_favorable=True

    vr_bonus = 0
    if vr.get('has_edge'): vr_bonus = min(vr.get('n_significant',0)*4, 12)

    # V21: CPI bonus (cpi_val extracted from cpi dict computed above)
    cpi_val = cpi.get('cpi', 0)
    cpi_regime = cpi.get('regime', 'ERROR')
    cpi_bonus = 0
    if cpi_val >= 60: cpi_bonus = 12
    elif cpi_val >= 45: cpi_bonus = 8
    elif cpi_val >= 35: cpi_bonus = 4

    # V21: Markov bonus
    markov_bonus = 0
    if markov.get('has_dependence'): markov_bonus = min(int(markov.get('transition_edge',0) / 2), 8)

    # V21: Spectral bonus
    spectral_bonus = 0
    if spectral.get('has_cycle'): spectral_bonus = min(int(spectral.get('spectral_edge',0) * 2), 8)
    acf_bonus = 0
    if acf.get('has_pattern'): acf_bonus = min(len(acf.get('significant_lags',[]))*3, 10)

    # ═══ V21+ PRECISION BONUSES ═══
    # ADX Slope: early trend detection bonus
    adx_slope_bonus = 0
    if adx_slope.get('phase') == "TREND_FORMING" and adx_slope.get('confidence', 0) > 40:
        adx_slope_bonus = min(int(adx_slope['confidence'] / 10), 8)
    elif adx_slope.get('phase') == "TREND_ESTABLISHED":
        adx_slope_bonus = 5

    # EMA Ribbon: trend quality bonus
    ribbon_bonus = 0
    if ema_ribbon.get('quality') == "EXCELLENT":
        ribbon_bonus = 10
    elif ema_ribbon.get('quality') == "GOOD":
        ribbon_bonus = 6
    elif ema_ribbon.get('quality') == "MODERATE":
        ribbon_bonus = 3
    # Extra for direction alignment
    if ema_ribbon.get('direction') == bias and ribbon_bonus > 0:
        ribbon_bonus += 3

    # Trend Coherence: multi-TF agreement bonus
    coherence_bonus = 0
    if trend_coherence.get('coherence') == "PERFECT" and trend_coherence.get('coherent_direction') == bias:
        coherence_bonus = 12
    elif trend_coherence.get('coherence') == "STRONG" and trend_coherence.get('coherent_direction') == bias:
        coherence_bonus = 8
    elif trend_coherence.get('coherence') == "STRONG":
        coherence_bonus = 4

    # Candle Structure: entry quality bonus
    candle_bonus = 0
    if candle_struct.get('quality') == "EXCELLENT":
        candle_bonus = 8
    elif candle_struct.get('quality') == "GOOD":
        candle_bonus = 5
    elif candle_struct.get('quality') == "MODERATE":
        candle_bonus = 2

    # Momentum Acceleration: timing precision bonus
    mom_accel_bonus = 0
    if bias == "BULLISH" and mom_accel.get('phase') == "BULL_ACCELERATING":
        mom_accel_bonus = min(int(mom_accel.get('confidence', 0) / 12), 8)
    elif bias == "BEARISH" and mom_accel.get('phase') == "BEAR_ACCELERATING":
        mom_accel_bonus = min(int(mom_accel.get('confidence', 0) / 12), 8)
    # Penalty for decelerating in our direction
    if (bias == "BULLISH" and mom_accel.get('phase') == "BULL_DECELERATING") or \
       (bias == "BEARISH" and mom_accel.get('phase') == "BEAR_DECELERATING"):
        mom_accel_bonus = -3  # Slight penalty

    # ═══ V23 SNIPER BONUSES ═══
    # Market Structure bonus
    market_structure_bonus = 0
    if mkt_struct.get('bos') and mkt_struct.get('trend') == bias:
        market_structure_bonus = 8  # Break of Structure in our direction
    elif mkt_struct.get('choch'):
        if ("BULL" in str(mkt_struct.get('last_event','')) and bias == "BULLISH") or \
           ("BEAR" in str(mkt_struct.get('last_event','')) and bias == "BEARISH"):
            market_structure_bonus = 10  # CHoCH confirming our direction
    elif mkt_struct.get('trend') == bias:
        market_structure_bonus = 4

    # Candle Momentum bonus
    candle_mom_bonus = 0
    if candle_mom.get('conviction') == "STRONG": candle_mom_bonus = 8
    elif candle_mom.get('conviction') == "MODERATE": candle_mom_bonus = 4

    # Pullback Quality bonus
    pullback_bonus = 0
    if pb_quality.get('quality') == "EXCELLENT": pullback_bonus = 8
    elif pb_quality.get('quality') == "GOOD": pullback_bonus = 5
    elif pb_quality.get('quality') == "MODERATE": pullback_bonus = 2

    # Liquidity Sweep bonus
    sweep_bonus = 0
    if liq_sweep.get('sweep'):
        if (liq_sweep['type'] == "BULL_SWEEP" and bias == "BULLISH") or \
           (liq_sweep['type'] == "BEAR_SWEEP" and bias == "BEARISH"):
            sweep_bonus = 8

    # Entry Sync bonus
    entry_sync_bonus = 0
    if entry_sync.get('ready') == "READY": entry_sync_bonus = 6
    elif entry_sync.get('ready') == "ALMOST": entry_sync_bonus = 3

    # Continuation Pattern bonus
    continuation_bonus = 0
    if cont_pattern.get('pattern') != "NONE":
        continuation_bonus = min(8, cont_pattern.get('confidence', 0) // 10)

    # Breakout Retest bonus (calculated after SR levels)
    retest_bonus = 0

    # V23: RANDOM WALK PENALTY
    random_walk_penalty = 0
    if 0.47 <= hurst_val <= 0.53 and hurst_r2 >= 0.7:
        random_walk_penalty = -20  # Honest: no edge in random walk

    # V23: CPI GATE ADAPTATIVO por asset class
    vol_class = profile.get('vol_class', 'MEDIUM')
    cpi_min_map = {
        'ULTRA_LOW': 20, 'LOW': 18, 'MEDIUM': 16,
        'HIGH': 14, 'EXTREME': 12,
        'BOOM': 10, 'CRASH': 10, 'STEP': 8
    }
    cpi_gate_min = cpi_min_map.get(vol_class, 18)

    # ═══ 🔴 FIX #5: BACKTEST 1× (não 2×) + V20 multi-setup ═══
    sim = run_walk_forward_v21(h1, bias, profile, n_folds=4)

    # ADAPTIVE (usa resultado do único backtest)
    adapted_profile = AdaptiveLearnerV20.adjust_profile(profile, sim, dist)

    # 🔴 FIX #6: Monte Carlo REAL
    mc = monte_carlo_bootstrap(sim.get('RESULTS', []))

    # ═══ V21: CPI GATE — Nao operar se imprevisivel ═══
    # (cpi_val and cpi_regime already extracted above)

    # ═══ SETUP DETECTION V21 — PREDICTABILITY-GATED ═══
    sig = "MONITORING"; entry = float(c1['close']); sl_val = float(c1['close'])
    entry_type = "Wait"; sl_reason = "Pivot"; trade_style = None; setup_type = None
    vc = profile['vol_class']

    # M5 trigger check
    trigger_ok, trigger_type = (True, "N/A")
    if m5 is not None and len(m5) > 0:
        trigger_ok, trigger_type = trigger_candle_confirmed(m5, bias)

    mp_price, mp_type = detect_micro_pullback(m15, bias, c1['ATR'])

    def try_setup(direction):
        nonlocal sig, sl_val, entry_type, trade_style, setup_type, entry
        is_long = direction == "BULLISH"
        div_block = divergence and (("BEARISH" in str(divergence) and is_long and "HIDDEN" not in str(divergence)) or
                                     ("BULLISH" in str(divergence) and not is_long and "HIDDEN" not in str(divergence)))
        if div_block:
            sig = f"BLOCKED (DIV: {div_detail})"; return

        # REGIME-SPECIFIC STRATEGY
        # TRENDING → Swing/Breakout
        # RANGING → Mean Reversion
        # VOL_COMPRESS → Contra o movimento
        # TRANSITIONAL → Esperar ou size reduzido

        # ═══ V24-BC: BOOM/CRASH PRIORITY SETUPS ═══
        # O2: Dedicated BC Pipeline — BC setups only for BC assets
        # O3: Conflict resolution applied BEFORE setup selection
        is_bc = gen_type in ["BOOM", "CRASH"]

        # V24 M5: Regime-aware SL multiplier
        regime_sl_mult = bc_regime.get('sl_mult', 1.0) if is_bc else 1.0

        # BC-0: POST-SPIKE FADE (highest priority — time sensitive)
        # O3: Check if fade is allowed by conflict resolver
        if is_bc and bc_fade.get('post_spike') and bc_conflicts.get('allow_fade', True):
            fade_dir = bc_fade['fade_direction']
            if (fade_dir == "BUY" and is_long) or (fade_dir == "SELL" and not is_long):
                d = "LONG" if is_long else "SHORT"
                sig = f"{d} (POST-SPIKE FADE)"
                if is_long:
                    sl_val = entry - profile.get('sl_scalp_mult', 1.0) * bc_atr_clean * regime_sl_mult
                else:
                    sl_val = entry + profile.get('sl_scalp_mult', 1.0) * bc_atr_clean * regime_sl_mult
                absorb_str = " ✓absorb" if bc_fade.get('absorption_confirmed') else ""
                entry_type = f"Fade spike {bc_fade.get('candles_ago',0)} bars ago (size={bc_fade.get('spike_size',0):.2f}){absorb_str}"
                trade_style = "SCALP"; setup_type = "POST_SPIKE"
                return

        # BC-1: SPIKE CATCH (imminent spike — high R:R)
        # O3: Check if spike catch is allowed
        if is_bc and bc_spike.get('spike_imminent') and bc_spike.get('probability', 0) >= 50 \
                and bc_conflicts.get('allow_spike_catch', True):
            is_boom = gen_type == "BOOM"
            if is_boom and is_long:  # Boom spike UP → BUY
                sig = "LONG (SPIKE CATCH)"
                sl_val = entry - profile.get('sl_atr_mult', 1.5) * bc_atr_clean * regime_sl_mult
                entry_type = f"Spike UP {bc_spike['probability']}% | RSI:{bc_spike.get('rsi_zone','?')} | Drift:{bc_spike.get('drift_count',0)} bars | Kurt:{bc_kurt.get('kurtosis',3):.1f}"
                trade_style = "DAY"; setup_type = "SPIKE_CATCH"
                return
            elif not is_boom and not is_long:  # Crash spike DOWN → SELL
                sig = "SHORT (SPIKE CATCH)"
                sl_val = entry + profile.get('sl_atr_mult', 1.5) * bc_atr_clean * regime_sl_mult
                entry_type = f"Crash DOWN {bc_spike['probability']}% | RSI:{bc_spike.get('rsi_zone','?')} | Drift:{bc_spike.get('drift_count',0)} bars | Kurt:{bc_kurt.get('kurtosis',3):.1f}"
                trade_style = "DAY"; setup_type = "SPIKE_CATCH"
                return

        # BC-2: DRIFT RIDE (follow the natural drift — safest)
        # O3: Check if drift ride is allowed (blocked when spike imminent)
        if is_bc and bc_drift.get('safe_to_ride') and bc_drift.get('strength', 0) >= 40 \
                and bc_conflicts.get('allow_drift_ride', True):
            is_boom = gen_type == "BOOM"
            if is_boom and not is_long:  # Boom drifts DOWN → SELL
                sig = "SHORT (DRIFT RIDE)"
                sl_val = entry + profile.get('sl_scalp_mult', 1.0) * bc_atr_clean * regime_sl_mult
                entry_type = f"Drift DOWN str={bc_drift['strength']}% q={bc_drift['quality']} RSI:{bc_drift.get('rsi',50):.0f} Rgm:{bc_regime.get('regime','?')}"
                trade_style = "SCALP" if bc_drift['strength'] < 60 else "DAY"
                setup_type = "DRIFT_RIDE"
                return
            elif not is_boom and is_long:  # Crash drifts UP → BUY
                sig = "LONG (DRIFT RIDE)"
                sl_val = entry - profile.get('sl_scalp_mult', 1.0) * bc_atr_clean * regime_sl_mult
                entry_type = f"Drift UP str={bc_drift['strength']}% q={bc_drift['quality']} RSI:{bc_drift.get('rsi',50):.0f} Rgm:{bc_regime.get('regime','?')}"
                trade_style = "SCALP" if bc_drift['strength'] < 60 else "DAY"
                setup_type = "DRIFT_RIDE"
                return

        # BC-3: STOCHASTIC SPIKE TIMER (confirmed signal)
        if is_bc and bc_stoch.get('ready'):
            stoch_sig = bc_stoch['signal']
            if stoch_sig == "SPIKE_BUY" and is_long:
                sig = "LONG (STOCH SPIKE)"
                sl_val = entry - profile.get('sl_atr_mult', 1.5) * c1['ATR']
                entry_type = f"Stoch K={bc_stoch['stoch_k']:.0f} RSI={bc_stoch.get('rsi',50):.0f} → SPIKE BUY"
                trade_style = "DAY"; setup_type = "SPIKE_CATCH"
                return
            elif stoch_sig == "SPIKE_SELL" and not is_long:
                sig = "SHORT (STOCH CRASH)"
                sl_val = entry + profile.get('sl_atr_mult', 1.5) * c1['ATR']
                entry_type = f"Stoch K={bc_stoch['stoch_k']:.0f} RSI={bc_stoch.get('rsi',50):.0f} → CRASH SELL"
                trade_style = "DAY"; setup_type = "SPIKE_CATCH"
                return
            elif stoch_sig == "DRIFT_SELL" and not is_long:
                sig = "SHORT (STOCH DRIFT)"
                sl_val = entry + profile.get('sl_scalp_mult', 1.0) * c1['ATR']
                entry_type = f"Stoch K={bc_stoch['stoch_k']:.0f} RSI={bc_stoch.get('rsi',50):.0f} → DRIFT SELL"
                trade_style = "SCALP"; setup_type = "DRIFT_RIDE"
                return
            elif stoch_sig == "DRIFT_BUY" and is_long:
                sig = "LONG (STOCH DRIFT)"
                sl_val = entry - profile.get('sl_scalp_mult', 1.0) * c1['ATR']
                entry_type = f"Stoch K={bc_stoch['stoch_k']:.0f} RSI={bc_stoch.get('rsi',50):.0f} → DRIFT BUY"
                trade_style = "SCALP"; setup_type = "DRIFT_RIDE"
                return

        # BC-4: REVERSAL (CHoCH + absorption + supply/demand)
        if is_bc and mkt_struct.get('choch'):
            choch_bull = "BULL" in str(mkt_struct.get('last_event', ''))
            choch_bear = "BEAR" in str(mkt_struct.get('last_event', ''))
            if choch_bull and is_long and bc_absorb.get('absorption'):
                sig = "LONG (REVERSAL)"
                sl_val = entry - profile.get('sl_atr_mult', 1.5) * c1['ATR']
                entry_type = f"CHoCH Bull + Absorption ({bc_absorb.get('strength',0):.0f}%)"
                trade_style = "DAY"; setup_type = "REVERSAL"
                return
            elif choch_bear and not is_long and bc_absorb.get('absorption'):
                sig = "SHORT (REVERSAL)"
                sl_val = entry + profile.get('sl_atr_mult', 1.5) * c1['ATR']
                entry_type = f"CHoCH Bear + Absorption ({bc_absorb.get('strength',0):.0f}%)"
                trade_style = "DAY"; setup_type = "REVERSAL"
                return

        # O4: GBM/STEP setups removed — V24-BC is Boom/Crash only
        # (Legacy code removed: GEN_VOL_COMPRESS, GEN_PRICE_DEV, GEN_STEP_REVERT)

        # 🔴 FIX #3: Crash/Boom — drift direction real
        if gen_type in ["BOOM","CRASH"]:
            phase = gen.get('spike_phase','')
            drift_dir = gen.get('drift_direction','')
            if phase in ["DRIFT_STRONG","DRIFT_NORMAL"]:
                if (drift_dir=="UP" and is_long) or (drift_dir=="DOWN" and not is_long):
                    d = "LONG" if is_long else "SHORT"
                    sig = f"{d} (SPIKE DRIFT {phase})"
                    sl_val = entry - adapted_profile['sl_atr_mult']*c1['ATR'] if is_long else entry + adapted_profile['sl_atr_mult']*c1['ATR']
                    entry_type = f"Drift {drift_dir} ({gen.get('last_spike_bars',0)} bars)"
                    trade_style = "DAY"; setup_type = "GEN_SPIKE_DRIFT"
                    return

        # O4: STEP setup removed — V24-BC is Boom/Crash only

        # 2. REGIME-SPECIFIC CLASSIC SETUPS
        if "TRENDING" in regime and adx > adapted_profile.get('adx_strong',25):
            if (is_long and abs(c1['close']-c1['EMA_50'])<c1['ATR']*1.5) or \
               (not is_long and abs(c1['close']-c1['EMA_50'])<c1['ATR']*1.5):
                d = "LONG" if is_long else "SHORT"
                sig = f"{d} (SWING)"
                sl_val = detect_swing_level(h1, "BUY" if is_long else "SELL", adapted_profile['sl_atr_mult'])
                entry_type = f"Swing — {mp_type}"
                trade_style = "SWING"; setup_type = "SWING"
                if mp_price and mp_type != "MARKET": entry = mp_price
                return

        if "RANGING" in regime or hurst_val < 0.48:
            if abs(z_current) > profile.get('zscore_extreme',2)*0.6:
                if (z_current < 0 and is_long) or (z_current > 0 and not is_long):
                    d = "LONG" if is_long else "SHORT"
                    sig = f"{d} (MEAN REVERSION)"
                    sl_val = entry - adapted_profile['sl_atr_mult']*c1['ATR'] if is_long else entry + adapted_profile['sl_atr_mult']*c1['ATR']
                    entry_type = f"MR Z={z_current:.1f}"
                    trade_style = "REVERSAL"; setup_type = "MEAN_REVERSION"
                    return

        # 3. DAY
        # V21 FIX-C: DAY requires ADX >= 22 (not catch-all)
        if adx > max(adapted_profile.get('adx_trend_min',15), 22):
            d = "LONG" if is_long else "SHORT"
            sig = f"{d} (DAY)"
            sl_val = detect_swing_level(h1, "BUY" if is_long else "SELL", adapted_profile['sl_atr_mult']*0.8)
            entry_type = f"Day — {mp_type}"
            trade_style = "DAY"; setup_type = "DAY"
            if mp_price and mp_type != "MARKET": entry = mp_price
            return

        # 4. BREAKOUT
        # V21 PREC #5: Breakout needs close ABOVE/BELOW SR (not just near)
        if sr_touch and closest_sr:
            bk_ok, bk_r = confirm_breakout_volume(m15)
            broke_through = (is_long and c1['close'] > closest_sr['price'] + c1['ATR']*0.1) or \
                            (not is_long and c1['close'] < closest_sr['price'] - c1['ATR']*0.1)
            if bk_ok and broke_through:
                d = "LONG" if is_long else "SHORT"
                sig = f"{d} (BREAKOUT)"
                sl_val = closest_sr['price'] - c1['ATR'] if is_long else closest_sr['price'] + c1['ATR']
                entry_type = f"Breakout S/R (×{bk_r:.1f})"
                trade_style = "BREAKOUT"; setup_type = "BREAKOUT"
                return

        # 5. V23: BREAKOUT RETEST (pullback to broken S/R)
        br_retest = detect_breakout_retest(h1, sr_levels, direction, c1['ATR'])
        if br_retest.get('retest') and pb_quality.get('quality') in ['EXCELLENT', 'GOOD']:
            d = "LONG" if is_long else "SHORT"
            sig = f"{d} (RETEST)"
            if is_long:
                sl_val = br_retest['level'] - c1['ATR'] * 1.2
            else:
                sl_val = br_retest['level'] + c1['ATR'] * 1.2
            entry_type = f"S/R Retest ({br_retest.get('type','')}) PB:{pb_quality['quality']}"
            trade_style = "RETEST"; setup_type = "BREAKOUT_RETEST"
            return

        # 6. V23: SCALP (M15 momentum + M5 trigger — rápido, tight)
        if entry_sync.get('ready') == "READY" and candle_mom.get('conviction') in ['STRONG', 'MODERATE']:
            if c1['ADX'] > 18:  # Minimal trend requirement
                d = "LONG" if is_long else "SHORT"
                sig = f"{d} (SCALP)"
                sl_val = entry - c1['ATR'] * 1.2 if is_long else entry + c1['ATR'] * 1.2
                entry_type = f"Scalp — Sync:{entry_sync['score']} Mom:{candle_mom['conviction']}"
                trade_style = "SCALP"; setup_type = "SCALP"
                return

        # 7. V23: CONTINUATION PATTERN (Flag/Pennant)
        if cont_pattern.get('pattern') != "NONE" and cont_pattern.get('confidence', 0) > 50:
            d = "LONG" if is_long else "SHORT"
            sig = f"{d} (CONTINUATION)"
            sl_val = entry - c1['ATR'] * adapted_profile['sl_atr_mult'] if is_long else entry + c1['ATR'] * adapted_profile['sl_atr_mult']
            entry_type = f"{cont_pattern['pattern']} (conf:{cont_pattern['confidence']}%)"
            trade_style = "DAY"; setup_type = "CONTINUATION"
            return

    # V24 FIX #5: For Crash/Boom: try BOTH drift and spike directions
    # Score for each direction is evaluated independently
    # (fixes circular dependency where bias → scoring → setup → filtering)
    if gen_type in ["BOOM","CRASH"]:
        drift_dir = gen.get('drift_direction','')
        spike_dir = profile.get('spike_direction', '')

        # Primary: Try drift direction first (safest)
        if drift_dir == "UP": try_setup("BULLISH")
        elif drift_dir == "DOWN": try_setup("BEARISH")

        # If no signal from drift, try spike direction
        if sig == "MONITORING":
            if spike_dir == "UP": try_setup("BULLISH")
            elif spike_dir == "DOWN": try_setup("BEARISH")

        # Final fallback: try bias
        if sig == "MONITORING": try_setup(bias)
    else:
        try_setup(bias)

    # V24 O3: Apply conflict penalty to effective score
    conflict_penalty = bc_conflicts.get('conflict_penalty', 0) if gen_type in ["BOOM", "CRASH"] else 0

    # ═══ V21+ ENTRY REFINEMENT ═══
    # Use ATR channel and VWAP for more precise entry when setup detected
    if "LONG" in sig or "SHORT" in sig:
        # V23: Breakout Retest bonus
        br_rt = detect_breakout_retest(h1, sr_levels, bias, c1['ATR'])
        if br_rt.get('retest'): retest_bonus = 6

        ch_quality = atr_channel.get('quality', 'UNKNOWN')
        ch_entry = atr_channel.get('channel_entry')
        if ch_quality in ['OPTIMAL', 'GOOD'] and ch_entry is not None:
            # Refine entry to ATR channel level for better R:R
            if "LONG" in sig and ch_entry < entry:
                entry = ch_entry
                entry_type = f"{entry_type} → ATR-CH {ch_quality}"
            elif "SHORT" in sig and ch_entry > entry:
                entry = ch_entry
                entry_type = f"{entry_type} → ATR-CH {ch_quality}"
        # VWAP proximity refinement
        vwap_qual = vwap_data.get('entry_quality', 'UNKNOWN')
        if vwap_qual == 'EXCELLENT':
            entry_type = f"{entry_type} (VWAP✓)"

    # Spread
    if "LONG" in sig: entry += profile['spread']
    elif "SHORT" in sig: entry -= profile['spread']

    # Clamp SL
    if "LONG" in sig and (entry - sl_val) > adapted_profile['sl_atr_mult'] * c1['ATR']:
        sl_val = entry - adapted_profile['sl_atr_mult'] * c1['ATR']
    elif "SHORT" in sig and (sl_val - entry) > adapted_profile['sl_atr_mult'] * c1['ATR']:
        sl_val = entry + adapted_profile['sl_atr_mult'] * c1['ATR']

    # Storm — V23: Added new checks
    storm_data = {'adx':adx,'momentum_score':momentum,'pattern_score':pat_score,
        'divergence':divergence,'fib':fib_level is not None,'sr_touch':sr_touch,
        'alignment':align_type=="PERFECT",'bb_squeeze':bb_compression,
        'trending':"TRENDING" in regime,'volume':vol_confirmed,'hurst_trending':hurst_trending,
        'zscore':zscore_favorable,'gen_signal':gen_bonus>0,'dist':dist_favorable,
        'vr_edge':vr.get('has_edge',False),'acf_edge':acf.get('has_pattern',False),
        # V21+ storm checks
        'ribbon_quality':ema_ribbon.get('quality'),
        'coherence':trend_coherence.get('coherence'),
        'candle_quality':candle_struct.get('quality'),
        'mom_accel':mom_accel_bonus > 0,
        # V23 storm checks
        'mkt_struct': mkt_struct.get('bos') or mkt_struct.get('choch'),
        'candle_mom': candle_mom.get('conviction') in ['STRONG', 'MODERATE'],
        'pullback': pb_quality.get('quality') in ['EXCELLENT', 'GOOD'],
        'entry_sync': entry_sync.get('ready') == 'READY',
        }
    storm_level, storm_bonus, storm_criteria = calculate_storm_bonus(storm_data)

    if storm_level == "PERFECT_STORM" and "BLOCKED" not in sig and sig != "MONITORING":
        sig = sig.replace("LONG","LONG ⭐STORM⭐").replace("SHORT","SHORT ⭐STORM⭐")
        setup_type = "PERFECT_STORM"

    # V21: Independent Edge Correlation
    indep_edges = calculate_independent_edges(
        vr, acf, hurst_val, gen_bonus, dist, z_current,
        divergence, fib_level, sr_touch, align_type, vol_confirmed)

    final_db = 0
    if divergence and (("LONG" in sig and "BULLISH" in str(divergence)) or ("SHORT" in sig and "BEARISH" in str(divergence))):
        final_db = abs(div_bonus)

    score = calculate_score(
        adx=adx, momentum_score=momentum, pattern_score=pat_score,
        dist_ema50=abs(c1['close']-c1['EMA_50']), atr=c1['ATR'],
        win_rate=sim['WR'], profit_factor=sim['PF'], profile=adapted_profile,
        divergence_bonus=final_db, fib_bonus=fib_bonus, sr_bonus=sr_bonus,
        alignment_bonus=align_bonus, storm_bonus=storm_bonus,
        regime_bonus=regime_bonus, volume_bonus=vol_bonus,
        hurst_bonus=hurst_bonus, zscore_bonus=zscore_bonus,
        consecutive_bonus=consecutive_bonus, generator_bonus=gen_bonus,
        distribution_bonus=dist_bonus, vr_bonus=vr_bonus, acf_bonus=acf_bonus,
        cpi_bonus=cpi_bonus, markov_bonus=markov_bonus, spectral_bonus=spectral_bonus,
        adx_slope_bonus=adx_slope_bonus, ribbon_bonus=ribbon_bonus,
        coherence_bonus=coherence_bonus, candle_bonus=candle_bonus,
        mom_accel_bonus=mom_accel_bonus,
        # V23 bonuses
        market_structure_bonus=market_structure_bonus,
        candle_mom_bonus=candle_mom_bonus, pullback_bonus=pullback_bonus,
        sweep_bonus=sweep_bonus, entry_sync_bonus=entry_sync_bonus,
        continuation_bonus=continuation_bonus, retest_bonus=retest_bonus)

    # Filters — V24-BC: Aggressive but precise for Boom/Crash
    configs = {"PERFECT_STORM":(80,1.2),"BREAKOUT":(50,1.2),"MEAN_REVERSION":(35,1.0),
               "GEN_VOL_COMPRESS":(35,0.9),"GEN_SPIKE_DRIFT":(30,0.8),"GEN_STEP_REVERT":(30,0.8),
               "GEN_PRICE_DEV":(35,1.0),"DAY":(40,1.1),"SWING":(55,1.2),
               # BC-specific — more aggressive thresholds
               "SPIKE_CATCH":(30,0.8),"DRIFT_RIDE":(25,0.8),"POST_SPIKE":(20,0.7),
               "REVERSAL":(40,1.0),
               "SCALP":(25,0.9),"BREAKOUT_RETEST":(40,1.1),"CONTINUATION":(35,1.0)}
    ms, mpf = configs.get(setup_type, (60, 1.3))
    is_gen_setup = setup_type and "GEN" in str(setup_type)

    # V23: Score override — reduce minimums with ultra-high confluence
    if trend_coherence.get('coherence') == "PERFECT" and ema_ribbon.get('quality') == "EXCELLENT":
        ms = int(ms * 0.80)  # 20% reduction
    if sim['WR'] > 65 and sim['PF'] > 1.8:
        ms = int(ms * 0.85)  # 15% reduction
    if storm_level in ["PERFECT_STORM", "STRONG_CONFLUENCE"]:
        ms = int(ms * 0.75)  # 25% reduction — trust the confluence

    # V24 FIX #11: Floor — prevent cascade from zeroing minimums
    ms = max(ms, 15)  # Absolute minimum score = 15

    # V24 O5: Anti-Meltdown Kill-Switch
    meltdown = bc_meltdown_check()
    if meltdown.get('blocked'):
        sig = f"BLOCKED ({meltdown['reason']})"
    elif meltdown.get('score_boost', 0) > 0:
        ms = int(ms * (1 + meltdown['score_boost'] / 100))  # Increase min score

    # V24 A3: Expectancy stress test — block if stressed expectancy < 0
    if sim.get('HIGH_RISK', False) and not is_gen_setup:
        # Expectancy goes negative under -20% WR stress → high risk warning
        pass  # Don't block, but flag in output

    if "BLOCKED" not in sig and sig != "MONITORING":
        fails = []
        # V23: Random Walk penalty + V24 O3 conflict penalty applied to score
        effective_score = score.total + random_walk_penalty - conflict_penalty
        if effective_score < ms: fails.append(f"SCORE={effective_score:.0f}<{ms}")
        # V23: CPI gate ADAPTATIVO por asset class
        if cpi_val < cpi_gate_min and not is_gen_setup: fails.append(f"CPI={cpi_val:.0f}<{cpi_gate_min}")
        if sim['NET'] <= 0 and not is_gen_setup: fails.append("NET≤0")
        # V23: PF mínimo global 1.1 (honesto)
        pf_min = max(mpf, 1.1) if not is_gen_setup else mpf
        if sim['PF'] < pf_min and not is_gen_setup: fails.append(f"PF={sim['PF']:.1f}<{pf_min:.1f}")
        # V23: Entry Sync check — don't enter if TFs misaligned
        if entry_sync.get('ready') == "WAIT" and setup_type not in ["MEAN_REVERSION", "GEN_VOL_COMPRESS", "GEN_PRICE_DEV"]:
            fails.append(f"SYNC={entry_sync.get('score',0)}<60")
        if fails: sig = f"BLOCKED ({', '.join(fails)})"

    # Targets — V23: Adaptive TP (S/R aware + regime aware)
    risk = abs(entry - sl_val)
    if risk == 0: risk = float(c1['ATR'])
    tc = {"PERFECT_STORM":(5,10),"BREAKOUT":(adapted_profile['tp1_r'],adapted_profile['tp2_r']+2),
          "MEAN_REVERSION":(2,3),"GEN_VOL_COMPRESS":(2.5,4),"GEN_SPIKE_DRIFT":(2,5),
          "GEN_STEP_REVERT":(1.5,2.5),"GEN_PRICE_DEV":(2,3.5),"DAY":(2,3),
          "SWING":(adapted_profile['tp1_r'],adapted_profile['tp2_r']),
          # BC-specific TP (scalp = tighter, spike catch = wider)
          "SPIKE_CATCH":(3.0,6.0),"DRIFT_RIDE":(1.5,2.5),"POST_SPIKE":(1.2,2.0),
          "REVERSAL":(2.5,4.0),
          "SCALP":(1.5,2.5),"BREAKOUT_RETEST":(2.5,4),"CONTINUATION":(2,3.5)}
    r1, r2 = tc.get(setup_type, (adapted_profile['tp1_r'], adapted_profile['tp2_r']))

    # V23: Regime-adaptive TP
    if "TRENDING" in regime and adx > 30:
        r1 *= 1.3; r2 *= 1.3  # Extend TP in strong trends
    elif "RANGING" in regime:
        r1 = min(r1, 2.0); r2 = min(r2, 3.0)  # Cap TP in ranges

    direction = "LONG" if "LONG" in sig else "SHORT"
    tp1, tp2 = smart_tp(entry, direction, risk, r1, r2, sr_levels)

    # V23: Cap TP at nearest opposing S/R
    if sr_levels and ("LONG" in sig or "SHORT" in sig):
        for sr in sr_levels[:5]:
            if "LONG" in sig and sr['type'] == 'RESISTANCE' and sr['price'] > entry:
                sr_tp_cap = sr['price'] - c1['ATR'] * 0.2
                if tp2 > sr_tp_cap and sr_tp_cap > entry:
                    tp2 = sr_tp_cap
                    if tp1 > tp2: tp1 = entry + (tp2 - entry) * 0.6
                break
            elif "SHORT" in sig and sr['type'] == 'SUPPORT' and sr['price'] < entry:
                sr_tp_cap = sr['price'] + c1['ATR'] * 0.2
                if tp2 < sr_tp_cap and sr_tp_cap < entry:
                    tp2 = sr_tp_cap
                    if tp1 < tp2: tp1 = entry - (entry - tp2) * 0.6
                break

    # V23: Multi-entry levels
    entry_ideal = entry  # Current close
    entry_aggressive = entry  # Market
    entry_sniper = entry  # Pullback level
    if "LONG" in sig:
        entry_sniper = min(entry, float(c1['EMA_20'])) if abs(float(c1['close']) - float(c1['EMA_20'])) < c1['ATR'] * 1.5 else entry
        entry_aggressive = entry + c1['ATR'] * 0.1
    elif "SHORT" in sig:
        entry_sniper = max(entry, float(c1['EMA_20'])) if abs(float(c1['close']) - float(c1['EMA_20'])) < c1['ATR'] * 1.5 else entry
        entry_aggressive = entry - c1['ATR'] * 0.1

    # V23: Trailing stop levels
    trail_be = entry + risk * 0.5 if "LONG" in sig else entry - risk * 0.5  # Move to BE at 0.5R
    trail_1 = entry + risk * 1.0 if "LONG" in sig else entry - risk * 1.0  # Trail at 1R

    # Pyramid
    pyramid = ScalingEngine.calculate_pyramid(score.grade, score.total, capital, risk_pct, entry, sl_val, float(c1['ATR']), adapted_profile)

    show = any(x in sig for x in ["DAY","BREAKOUT","STORM","REVERSION","COMPRESS","DRIFT","SPIKE","STEP","DEVIATION","PRICE","SCALP","RETEST","CONTINUATION","FADE","REVERSAL"])

    imgs = [
        plot_candles(h4.tail(150), f"{name} H4 — {regime} | Gen:{gen_signal}", entry if show else None, sl_val if show else None, tp1 if show else None, tp2 if show else None, sr_levels if show else None),
        plot_candles(h1.tail(200), f"{name} H1 — H:{hurst_val} Z:{z_current:.1f} σ:{sigma_calibrated or 0:.3f}", entry if show else None, sl_val if show else None, tp1 if show else None, tp2 if show else None, sr_levels, fibs if show else None),
        plot_candles(m15.tail(200), f"{name} M15 — BB:{bb_cycle} VR:{vr.get('dominant_type','?')} ACF:{acf.get('dominant_type','?')}", entry if show else None, sl_val if show else None, tp1 if show else None, tp2 if show else None),
    ]

    # V21: Optimal holding
    hold = optimal_holding_period(acf, setup_type)

    confs = []
    if cpi_val >= 45: confs.append(f"\U0001f9e0 CPI: {cpi_val:.0f} ({cpi_regime})")
    if markov.get('has_dependence'): confs.append(f"\U0001f52e Markov: {markov['best_transition']}")
    if spectral.get('has_cycle'): confs.append(f"\U0001f4c8 Cycle: {spectral['dominant_period']:.0f} bars")
    if rt_detail: confs.append(f"\U0001f504 {regime_transition}: {rt_detail}")
    if gen_bonus>0: confs.append(f"🧮 Gen: {gen_signal} (+{gen_bonus})")
    if vr.get('has_edge'): confs.append(f"📐 VR: {vr['dominant_type']} ({vr.get('n_significant',0)} sig)")
    if acf.get('has_pattern'): confs.append(f"📊 ACF: {acf['dominant_type']} (lag-1={acf.get('acf_1',0):.3f})")
    if vol_cluster.get('has_clustering'): confs.append(f"🔥 VolCluster: {vol_cluster['vol_regime']}")
    if dist_favorable: confs.append(f"📊 Dist P{dist['percentile']:.0f}")
    if divergence: confs.append(f"🔍 {divergence}")
    if fib_level: confs.append(f"📐 Fib {fib_level}")
    if sr_touch: confs.append(f"🎯 S/R")
    if align_type!="NONE": confs.append(f"⭐ Align {align_type}")
    if storm_level: confs.append(f"🌟 {storm_level} ({len(storm_criteria)}/20)")
    if hurst_trending: confs.append(f"🧬 Hurst {hurst_val}")
    if zscore_favorable: confs.append(f"📊 Z {z_current:.1f}")
    if bb_compression: confs.append("💥 BB Squeeze")
    if trigger_ok and trigger_type!="N/A": confs.append(f"✅ Trigger: {trigger_type}")
    # V21+ precision confluences
    if ema_ribbon.get('quality') in ['EXCELLENT','GOOD']:
        confs.append(f"🌈 Ribbon {ema_ribbon['quality']} ({ema_ribbon.get('direction','?')})")
    if trend_coherence.get('coherence') in ['PERFECT','STRONG']:
        confs.append(f"🎯 TF Coherence {trend_coherence['coherence']} ({trend_coherence.get('coherent_direction','?')})")
    if candle_struct.get('quality') in ['EXCELLENT','GOOD']:
        confs.append(f"🔥 Candle {candle_struct['quality']} ({candle_struct.get('pattern_type','?')})")
    if mom_accel_bonus > 0:
        confs.append(f"🚀 Mom Accel {mom_accel.get('phase','?')}")
    if vwap_data.get('entry_quality') == 'EXCELLENT':
        confs.append(f"🏦 VWAP Zone ({vwap_data.get('zone','?')})")
    if adx_slope.get('phase') == 'TREND_FORMING':
        confs.append(f"📈 ADX Forming (slope={adx_slope.get('slope',0):.2f})")
    # V23 confluences
    if mkt_struct.get('bos'):
        confs.append(f"🔥 BOS ({mkt_struct.get('last_event','?')})")
    if mkt_struct.get('choch'):
        confs.append(f"⚡ CHoCH ({mkt_struct.get('last_event','?')})")
    if candle_mom.get('conviction') in ['STRONG', 'MODERATE']:
        confs.append(f"💪 CandleMom {candle_mom['conviction']} ({candle_mom.get('score',0):.0f})")
    if pb_quality.get('quality') in ['EXCELLENT', 'GOOD']:
        confs.append(f"🎯 Pullback {pb_quality['quality']} ({pb_quality.get('depth_pct',0):.0%})")
    if liq_sweep.get('sweep'):
        confs.append(f"💧 {liq_sweep['type']}")
    if entry_sync.get('ready') == 'READY':
        confs.append(f"✅ Entry Sync {entry_sync['score']}/100")
    if cont_pattern.get('pattern') != 'NONE':
        confs.append(f"🚩 {cont_pattern['pattern']} ({cont_pattern.get('confidence',0)}%)")
    if early_reversal:
        confs.append(f"⚡ EARLY REVERSAL → {reversal_dir}")
    if retest_bonus > 0:
        confs.append("🔄 Breakout Retest")
    # V24-BC: Boom/Crash specific confluences
    if bc_spike.get('spike_imminent'):
        confs.append(f"⚡ SPIKE IMMINENT ({bc_spike['probability']}%) RSI:{bc_spike.get('rsi_zone','?')}")
    if bc_drift.get('safe_to_ride'):
        confs.append(f"🌊 Drift {bc_drift['direction']} str={bc_drift['strength']}% ({bc_drift['quality']})")
    if bc_fade.get('post_spike'):
        confs.append(f"🔄 Post-Spike Fade → {bc_fade['fade_direction']} (target={bc_fade.get('fade_target',0):.2f})")
    if bc_freq.get('overdue'):
        confs.append(f"⏰ Spike OVERDUE (last {bc_freq['last_spike_ago']} bars, avg {bc_freq.get('avg_interval',0):.0f})")
    if bc_stoch.get('ready'):
        confs.append(f"📊 Stoch Timer: {bc_stoch['signal']} (K={bc_stoch['stoch_k']:.0f})")
    if bc_absorb.get('absorption'):
        confs.append(f"💪 Absorption {bc_absorb['type']} ({bc_absorb['strength']:.0f}%)")
    if bc_multi.get('cluster'):
        confs.append(f"🔥 {bc_multi['pattern']} ({bc_multi['consecutive_spikes']} spikes)")
    if bc_sd.get('nearest_demand') and bias == "BULLISH":
        confs.append(f"📍 Demand Zone @ {bc_sd['nearest_demand']['price']:.2f}")
    if bc_sd.get('nearest_supply') and bias == "BEARISH":
        confs.append(f"📍 Supply Zone @ {bc_sd['nearest_supply']['price']:.2f}")

    risks = []
    if cpi_val < 35: risks.append(f"\u26a0\ufe0f CPI LOW: {cpi_val:.0f} (unpredictable)")
    if regime_transition == "EXHAUSTION": risks.append("\u26a0\ufe0f Regime EXHAUSTION")
    if indep_edges['quality'] == "WEAK": risks.append(f"\u26a0\ufe0f Edges WEAK ({indep_edges['n_independent']} indep)")
    if "RANGING" in regime: risks.append("⚠️ RANGING")
    if not sim['WF_STABLE']: risks.append("⚠️ WF instável")
    if mc.get('positive_pct',0)<55: risks.append(f"⚠️ MC {mc['positive_pct']}%")
    if roc_status=="EXTREME": risks.append("⚠️ ROC EXTREMO")
    if hurst_regime=="RANDOM_WALK": risks.append("⚠️ Random Walk")
    if hurst_regime=="UNRELIABLE": risks.append(f"⚠️ Hurst unreliable R²={hurst_r2}")
    if not vr.get('has_edge'): risks.append("⚠️ VR: sem edge estatístico")
    if gen.get('spike_phase')=="SPIKE_IMMINENT": risks.append("💥 SPIKE IMINENTE")
    if not trigger_ok and c5 is not None: risks.append(f"⚠️ M5 sem trigger ({trigger_type})")
    # V21+ precision risks
    if candle_struct.get('quality') == 'WEAK': risks.append("⚠️ Candle structure WEAK")
    if adx_slope.get('phase') == 'TREND_DYING': risks.append("⚠️ ADX trend dying")
    if trend_coherence.get('coherence') == 'WEAK': risks.append("⚠️ TF coherence WEAK")
    if mom_accel_bonus < 0: risks.append(f"⚠️ Momentum decelerating ({mom_accel.get('phase','?')})")
    if atr_channel.get('quality') == 'OVEREXTENDED': risks.append("⚠️ Price overextended in ATR channel")
    # V23 risks
    if random_walk_penalty < 0: risks.append(f"🚫 RANDOM WALK (H:{hurst_val:.2f} R²:{hurst_r2:.2f}) — No statistical edge")
    if entry_sync.get('ready') == 'WAIT': risks.append(f"⏳ TF Sync LOW ({entry_sync.get('score',0)}/100)")
    if candle_mom.get('conviction') == 'NONE': risks.append("⚠️ Candle momentum NONE")
    if mkt_struct.get('choch') and mkt_struct.get('trend') != bias:
        risks.append(f"⚡ CHoCH AGAINST bias ({mkt_struct.get('last_event','?')})")
    if sim.get('TOTAL_TRADES', 0) < 20: risks.append(f"⚠️ Low trades ({sim.get('TOTAL_TRADES',0)})")
    if early_reversal: risks.append(f"⚡ EARLY REVERSAL active — H4 not confirmed")
    # V24-BC: Boom/Crash specific risks
    if bc_spike.get('spike_imminent') and bc_spike.get('probability', 0) > 60:
        spike_dir = bc_spike.get('type', '')
        if ("UP" in spike_dir and "SHORT" in sig) or ("DOWN" in spike_dir and "LONG" in sig):
            risks.append(f"🚨 SPIKE CONTRA sua posição! ({bc_spike['probability']}%)")
    if bc_freq.get('next_spike_window') == "RECENTLY_SPIKED":
        risks.append("⚠️ Spike recente — pode repetir ou reverter")
    if bc_drift.get('quality') == "CHOPPY":
        risks.append("⚠️ Drift CHOPPY — entradas menos confiáveis")
    if not bc_drift.get('safe_to_ride') and setup_type == "DRIFT_RIDE":
        risks.append("🚫 RSI em zona de perigo para drift")

    return {
        "FINAL_DECISION": sig, "TRADE_STYLE": trade_style or "N/A", "SETUP_TYPE": setup_type or "N/A",
        "SETUP_SCORE": float(round(score.total,1)), "BASE_SCORE": float(round(score.base_total,1)),
        "BONUS_SCORE": float(round(score.bonus_total,1)), "SETUP_GRADE": score.grade,
        "INDEX_PROFILE": vc, "GEN_TYPE": gen_type,
        "GEN_ANALYSIS": convert_np(gen), "GEN_SIGNAL": gen_signal, "GEN_BONUS": gen_bonus,
        "SIGMA_CALIBRATED": sigma_calibrated,
        "VR_TEST": convert_np(vr), "VR_BONUS": vr_bonus,
        "ACF_TEST": convert_np(acf), "ACF_BONUS": acf_bonus,
        "VOL_CLUSTER": convert_np(vol_cluster),
        "DIST_ANALYSIS": convert_np(dist), "DIST_BONUS": dist_bonus,
        "HURST": float(hurst_val), "HURST_REGIME": hurst_regime, "HURST_R2": float(hurst_r2),
        "ZSCORE": float(round(z_current,2)),
        "BB_CYCLE": bb_cycle, "CONSECUTIVE": int(consec_count), "CONSECUTIVE_DIR": consec_dir,
        "ROC_STATUS": roc_status, "MARKET_STRUCTURE": structure, "MARKET_REGIME": regime,
        "TRIGGER_OK": trigger_ok, "TRIGGER_TYPE": trigger_type,
        "CONFLUENCES": confs, "RISKS": risks, "MOMENTUM": f"{momentum}/3",
        "ENTRY_TYPE": entry_type, "SL_REASON": sl_reason,
        "WIN_RATE": float(sim['WR']), "NET_PROFIT": float(sim['NET']),
        "MAX_DRAWDOWN": float(sim['DD']), "PROFIT_FACTOR": float(sim['PF']),
        "SHARPE": float(sim['SHARPE']), "SORTINO": float(sim['SORTINO']),
        "WF_STABLE": sim['WF_STABLE'], "FOLD_WRS": sim['FOLD_WRS'],
        "TOTAL_TRADES": int(sim['TOTAL_TRADES']),
        "SETUP_STATS": convert_np(sim.get('SETUP_STATS',{})),
        "MC_MEDIAN": float(mc.get('median',0)), "MC_P5": float(mc.get('p5',0)),
        "MC_P95": float(mc.get('p95',0)), "MC_POSITIVE": float(mc.get('positive_pct',0)),
        "ENTRY": float(round(entry,5)), "SL": float(round(sl_val,5)),
        "TP1": float(round(tp1,5)), "TP2": float(round(tp2,5)),
        "PYRAMID": convert_np(pyramid), "ADAPTED_PROFILE": convert_np({k:v for k,v in adapted_profile.items() if k in ['risk_mult','sl_atr_mult','tp2_r']}),
        "IMAGES": imgs, "ATR": float(c1['ATR']),
        "CPI": convert_np(cpi), "CPI_VAL": cpi_val,
        "SPECTRAL": convert_np(spectral), "MARKOV": convert_np(markov),
        "REGIME_TRANSITION": regime_transition, "RT_MULT": rt_mult, "RT_DETAIL": rt_detail,
        "BIAS_CONFIDENCE": bias_confidence, "BIAS_SCORE": bias_score,
        "MOMENTUM_V21": momentum_v21,
        "INDEPENDENT_EDGES": convert_np(indep_edges),
        "HOLDING_PERIOD": convert_np(hold),
        "SCORE_BREAKDOWN": convert_np({
            "ADX":score.trend_strength,"MOM":score.momentum_align,"PAT":score.patterns,
            "VAL":score.value_zone,"HIST":score.historical,
            "DIV":score.divergence_bonus,"FIB":score.fib_bonus,"SR":score.sr_bonus,
            "ALIGN":score.alignment_bonus,"STORM":score.storm_bonus,"REGIME":score.regime_bonus,
            "VOL":score.volume_bonus,"HURST":score.hurst_bonus,"ZSCORE":score.zscore_bonus,
            "CONSEC":score.consecutive_bonus,"GEN":score.generator_bonus,"DIST":score.distribution_bonus,
            "VR":score.vr_bonus,"ACF":score.acf_bonus,
            "CPI":score.cpi_bonus,"MARKOV":score.markov_bonus,"SPECTRAL":score.spectral_bonus,
            "ADX_SLOPE":score.adx_slope_bonus,"RIBBON":score.ribbon_bonus,
            "COHERENCE":score.coherence_bonus,"CANDLE":score.candle_bonus,
            "MOM_ACCEL":score.mom_accel_bonus
        }),
        # V21+ precision data
        "ADX_SLOPE": convert_np(adx_slope),
        "EMA_RIBBON": convert_np(ema_ribbon),
        "TREND_COHERENCE": convert_np(trend_coherence),
        "VWAP_DATA": convert_np(vwap_data),
        "CANDLE_STRUCT": convert_np(candle_struct),
        "MOM_ACCEL": convert_np(mom_accel),
        "ATR_CHANNEL": convert_np(atr_channel),
        # V23 precision data
        "MKT_STRUCTURE": convert_np(mkt_struct),
        "CANDLE_MOMENTUM": convert_np(candle_mom),
        "PULLBACK_QUALITY": convert_np(pb_quality),
        "LIQ_SWEEP": convert_np(liq_sweep),
        "ENTRY_SYNC": convert_np(entry_sync),
        "CONT_PATTERN": convert_np(cont_pattern),
        "EARLY_REVERSAL": early_reversal,
        "REVERSAL_DIR": reversal_dir,
        "RW_PENALTY": random_walk_penalty,
        "CPI_GATE_MIN": cpi_gate_min,
        # V23: Multi-entry levels
        "ENTRY_AGGRESSIVE": float(round(entry_aggressive, 5)),
        "ENTRY_IDEAL": float(round(entry_ideal, 5)),
        "ENTRY_SNIPER": float(round(entry_sniper, 5)),
        # V23: Trailing stop levels
        "TRAIL_BE": float(round(trail_be, 5)),
        "TRAIL_1R": float(round(trail_1, 5)),
        # V23: MC confidence
        "MC_CONFIDENCE": "HIGH" if sim.get('TOTAL_TRADES', 0) >= 30 else "LOW",
        # V24-BC: Boom/Crash engine data
        "BC_SPIKE": convert_np(bc_spike),
        "BC_DRIFT": convert_np(bc_drift),
        "BC_FADE": convert_np(bc_fade),
        "BC_SD_ZONES": convert_np(bc_sd),
        "BC_FREQ": convert_np(bc_freq),
        "BC_ABSORB": convert_np(bc_absorb),
        "BC_MULTI": convert_np(bc_multi),
        "BC_STOCH": convert_np(bc_stoch),
        # V24-BC: New audit-driven data
        "BC_REGIME": convert_np(bc_regime),
        "BC_KURTOSIS": convert_np(bc_kurt),
        "BC_CONFLICTS": convert_np(bc_conflicts),
        "BC_CLEAN_ATR": round(float(bc_atr_clean), 5),
        "RAW_ATR": round(float(c1['ATR']), 5),
        "EXPECTANCY": sim.get('EXPECTANCY', 0),
        "EXPECTANCY_STRESSED": sim.get('EXPECTANCY_STRESSED', 0),
        "HIGH_RISK": sim.get('HIGH_RISK', False),
        "MELTDOWN": convert_np(bc_meltdown_check()),
    }

# ==============================================================================
# SCANNER V20 — 🟢 FIX #4: Todos os gen types
# ==============================================================================

async def quick_scan(code, name):
    try:
        raw = await fetch_single(code, 3600, 300)
        if not raw: return None
        df = indicators(prep_df(raw)); profile = get_profile(name)
        if len(df) < 50: return None
        c = df.iloc[-1]; ppy = detect_periods_per_year(df)
        hurst_val, _, hr2 = calculate_hurst_exponent(df['close'])
        z = float(c['ZSCORE']) if pd.notna(c.get('ZSCORE')) else 0
        vr = variance_ratio_test(df['close'])
        gt = profile.get('gen_type','GBM')
        if gt == 'GBM':
            sig_cal = calibrate_sigma(df, ppy)
            gen = GeneratorModelV20.analyze_gbm(df, profile, sig_cal, ppy)
        elif gt in ['BOOM','CRASH']:
            gen = GeneratorModelV20.analyze_crash_boom(df, profile, ppy)
        elif gt == 'STEP':
            gen = GeneratorModelV20.analyze_step(df, profile, ppy)
        else: gen = {}
        regime, _ = classify_regime(df)
        qs = 0
        if c['ADX'] > profile.get('adx_strong',25): qs += 25
        elif c['ADX'] > profile.get('adx_trend_min',15): qs += 12
        if abs(z) > profile.get('zscore_extreme',2)*0.6: qs += 18
        if hurst_val > profile.get('hurst_trend_min',0.53) or hurst_val < 0.45: qs += 12
        if gen.get('signal','NEUTRAL') not in ['NEUTRAL','VOL_NORMAL']: qs += 20
        if vr.get('has_edge'): qs += 15
        if "TRENDING" in regime: qs += 8
        # V21: CPI in scanner
        cpi_r = compound_predictability_index(df['close'], vr)
        cpi_v = cpi_r.get('cpi', 0)
        if cpi_v >= 50: qs += 15
        elif cpi_v >= 35: qs += 8
        bias = "BULLISH" if c['close'] > c['EMA_200'] else "BEARISH"
        return {"name":name,"code":code,"score":qs,"bias":bias,"adx":round(c['ADX'],1),
                "hurst":round(hurst_val,3),"zscore":round(z,2),"regime":regime,
                "gen_signal":gen.get('signal','N/A'),"vr_edge":vr.get('has_edge',False),
                "cpi":round(cpi_v,1),
                "vr_type":vr.get('dominant_type','?'),"cpi_regime":cpi_r.get('regime','?'),"profile":profile['vol_class']}
    except: return None

# ==============================================================================
# STREAMLIT UI V20 — MODERN MINIMAL
# ==============================================================================

# ── SIDEBAR ──
with st.sidebar:
    st.markdown("""<div style='padding:8px 0 16px;'>
        <span style='font-size:24px;font-weight:300;color:#fafafa;letter-spacing:-0.5px;'>APATECO</span>
        <span style='font-size:11px;color:#52525b;margin-left:6px;font-weight:500;'>V24-BC</span>
    </div>""", unsafe_allow_html=True)

    if "GEMINI_API_KEY" in st.secrets:
        api = st.secrets["GEMINI_API_KEY"]
        st.markdown("<span class='pill pill-green' style='font-size:11px;'>API Connected</span>", unsafe_allow_html=True)
    else:
        api = st.text_input("Gemini API Key", type="password", label_visibility="collapsed",
                             placeholder="Enter API key...")

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    mode = st.radio("Mode", ["Analysis", "Scanner"], label_visibility="collapsed",
                     horizontal=True)

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    capital = st.number_input("Capital", min_value=100, value=10000, step=100,
                               label_visibility="collapsed")
    st.caption("Capital ($)")
    risk_pct = st.slider("Risk", 0.5, 3.0, 1.0, 0.1, label_visibility="collapsed")
    st.caption(f"Risk per trade: {risk_pct}%")

    st.markdown("""<div style='margin-top:32px;padding:14px;background:#111113;border:1px solid #1e1e23;
        border-radius:8px;font-size:11px;color:#3f3f46;line-height:1.6;'>
        Boom/Crash Sniper V24-BC<br>
        Spike · Drift · Post-Spike Fade<br>
        Day Trade + Scalp Only
    </div>""", unsafe_allow_html=True)

# ── HEADER ──
st.markdown("""<div style='padding:0 0 8px;'>
    <span style='font-size:32px;font-weight:300;color:#fafafa;letter-spacing:-1px;'>APATECO</span>
    <span style='font-size:13px;color:#3f3f46;margin-left:8px;'>Boom/Crash Sniper V24-BC | Day Trade + Scalp</span>
</div>""", unsafe_allow_html=True)

with st.spinner("Loading assets..."): assets = get_assets()
if not assets: st.error("Connection failed"); st.stop()

# ==============================================================================
# ANALYSIS MODE
# ==============================================================================
if mode == "Analysis":
    left, right = st.columns([1, 3])

    with left:
        target = st.selectbox("Asset", list(assets.keys()), label_visibility="collapsed")
        prof = get_profile(target)
        st.markdown(f"""<div style='padding:10px 14px;background:#111113;border:1px solid #1e1e23;
            border-radius:8px;margin:8px 0 16px;'>
            <span style='color:#fafafa;font-size:13px;font-weight:500;'>{prof['vol_class']}</span><br>
            <span class='mono text-xs muted'>{prof.get('gen_type','—')}</span>
        </div>""", unsafe_allow_html=True)
        run = st.button("Analyze", use_container_width=True)

    with right:
        if run:
            if not api: st.error("API key required"); st.stop()

            status = st.status("Analyzing...", expanded=True)
            status.write("📡 Fetching multi-timeframe data...")
            h1r, h4r, m15r, m5r, err = asyncio.run(fetch_multi_tf(assets[target]))
            if err: status.update(state='error'); st.error(err); st.stop()
            status.write("🧮 Running statistical analysis...")
            data = sniper_core_v20(target, h1r, h4r, m15r, m5r, capital, risk_pct)
            imgs = data.pop("IMAGES")
            
            # ── GEMINI AI COM RETRY + FALLBACK ──
            dc = convert_np(data)
            ai_text, ai_error = call_gemini_with_retry(
                api_key=api,
                system_prompt=SYSTEM_PROMPT,
                data=dc,
                images=imgs,
                status_widget=status,
                max_retries=2,
                base_timeout=120
            )
            
            if ai_text:
                ai = ai_text
                status.update(label="✅ Complete", state="complete")
            else:
                # Fallback: análise automática SEM IA (dados já calculados)
                g = data.get('SETUP_GRADE', '?')
                s = data.get('SETUP_SCORE', 0)
                dec = data.get('FINAL_DECISION', '?')
                wr = data.get('WIN_RATE', 0)
                pf = data.get('PROFIT_FACTOR', 0)
                confs = data.get('CONFLUENCES', [])
                risks = data.get('RISKS', [])
                ai = f"""## ⚡ VEREDICTO: {dec}
**Grade:** {g} | **Score:** {s}/220 | **WR:** {wr:.0f}% | **PF:** {pf:.1f}

### 📊 CONFLUÊNCIAS
{chr(10).join(f'- {c}' for c in confs) if confs else '- Nenhuma confluência forte'}

### ⚠️ RISCOS
{chr(10).join(f'- {r}' for r in risks) if risks else '- Sem riscos identificados'}

---
*⚠️ Análise IA indisponível ({ai_error[:80] if ai_error else 'todos os modelos falharam'}). 
Dados estatísticos acima são 100% válidos — apenas o resumo narrativo da IA não foi gerado.*
*💡 Dica: Se o erro persistir, verifique sua API key e tente novamente em alguns minutos.*"""
                status.update(label="⚠️ Done (sem IA)", state="complete")

            # ── GRADE CARD ──
            g = data['SETUP_GRADE']
            grade_class = {"S":"grade-s","A++":"grade-app","A+":"grade-ap","A":"grade-a"}.get(g,"grade-low")
            score_pct = min(data['SETUP_SCORE'] / 220 * 100, 100)
            bar_color = {"S":"#a78bfa","A++":"#34d399","A+":"#60a5fa","A":"#67e8f9"}.get(g,"#52525b")

            # Decision tag
            d = data['FINAL_DECISION']
            if "LONG" in d:
                tag = f"<span class='tag-long'>LONG</span>"
            elif "SHORT" in d:
                tag = f"<span class='tag-short'>SHORT</span>"
            elif "BLOCKED" in d:
                tag = f"<span class='tag-blocked'>BLOCKED</span>"
            else:
                tag = f"<span class='tag-monitoring'>MONITORING</span>"

            st.markdown(f"""
            <div class='{grade_class}' style='margin:8px 0 20px;'>
                <div class='grade-letter'>{g}</div>
                <div style='font-family:JetBrains Mono,monospace;font-size:22px;margin:4px 0;color:#fafafa;'>
                    {data['SETUP_SCORE']:.0f}<span style='color:#52525b;font-size:14px;'> / 220</span>
                </div>
                <div class='score-bar-outer'>
                    <div class='score-bar-inner' style='width:{score_pct}%;background:{bar_color};'></div>
                </div>
                <div style='margin-top:12px;'>{tag}</div>
                <div style='color:#52525b;font-size:12px;margin-top:6px;'>
                    {data.get('SETUP_TYPE','—')} · {data['GEN_TYPE']}
                </div>
            </div>""", unsafe_allow_html=True)

            # ── GENERATOR MODEL ──
            st.markdown("## Generator")
            ga = data.get('GEN_ANALYSIS', {})
            g1, g2, g3, g4 = st.columns(4)
            g1.metric("Type", data['GEN_TYPE'])
            g2.metric("Signal", data['GEN_SIGNAL'])
            g3.metric("σ Real", f"{data.get('SIGMA_CALIBRATED',0) or 0:.4f}")
            g4.metric("Bonus", f"+{data['GEN_BONUS']}")

            if data['GEN_TYPE'] == 'GBM':
                wins = ga.get('windows', {})
                w1, w2, w3 = st.columns(3)
                for col, lbl in [(w1,"SHORT"),(w2,"MEDIUM"),(w3,"LONG")]:
                    w = wins.get(lbl, {})
                    sig = w.get('signal', '—')
                    delta_color = "normal" if sig == "VOL_NORMAL" else ("inverse" if sig == "VOL_COMPRESS" else "normal")
                    col.metric(f"Vol {lbl}", f"{w.get('vol_ratio',1):.3f}", sig, delta_color=delta_color)
                pc, pz = st.columns(2)
                pc.metric("Direction", ga.get('compress_direction', '—'))
                pz.metric("Price Z", f"{ga.get('z_price',0):.2f}")

            # ── STATISTICAL EDGE ──
            st.markdown("## Edge Analysis")
            e1, e2, e3, e4 = st.columns(4)
            vrt = data.get('VR_TEST', {})
            e1.metric("Variance Ratio",
                       "Edge Found" if vrt.get('has_edge') else "No Edge",
                       vrt.get('dominant_type', ''))
            acft = data.get('ACF_TEST', {})
            e2.metric("Autocorrelation",
                       acft.get('dominant_type', '—'),
                       f"lag1 = {acft.get('acf_1',0):.4f}")
            vc = data.get('VOL_CLUSTER', {})
            e3.metric("Vol Cluster", vc.get('vol_regime', '—'))
            e4.metric("Hurst",
                       f"{data['HURST']:.3f}",
                       f"R² = {data.get('HURST_R2',0):.2f}")

            # ── DISTRIBUTION ──
            # ═══ V21: PREDICTABILITY INDEX ═══
            st.markdown("## Predictability")
            cpi_data = data.get('CPI', {})
            cpi_v = cpi_data.get('cpi', 0)
            cpi_reg = cpi_data.get('regime', '?')
            comps = cpi_data.get('components', {})
            pc1, pc2, pc3, pc4 = st.columns(4)
            cpi_color = '#22c55e' if cpi_v >= 60 else '#f59e0b' if cpi_v >= 35 else '#ef4444'
            pc1.metric("CPI", f"{cpi_v:.0f}/100", cpi_reg)
            pc2.metric("SampleEn", f"{comps.get('se',0):.0f}/25")
            pc3.metric("PermEn", f"{comps.get('pe',0):.0f}/25")
            pc4.metric("VR+ACF", f"{comps.get('vr',0)+comps.get('acf',0):.0f}/50")

            mrkv = data.get('MARKOV', {})
            spec = data.get('SPECTRAL', {})
            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("Markov", "Dep Found" if mrkv.get('has_dependence') else "No Dep", mrkv.get('best_transition',''))
            mc2.metric("Cycles", f"{spec.get('dominant_period',0):.0f} bars" if spec.get('has_cycle') else "None")
            mc3.metric("Regime Shift", data.get('REGIME_TRANSITION', 'STABLE'), data.get('RT_DETAIL',''))

            # ── V21+ ENTRY PRECISION ──
            st.markdown("## Entry Precision")
            adx_sl = data.get('ADX_SLOPE', {})
            ribbon = data.get('EMA_RIBBON', {})
            coherence = data.get('TREND_COHERENCE', {})
            vwap = data.get('VWAP_DATA', {})
            candle = data.get('CANDLE_STRUCT', {})
            maccel = data.get('MOM_ACCEL', {})
            atr_ch = data.get('ATR_CHANNEL', {})

            ep1, ep2, ep3, ep4 = st.columns(4)
            ep1.metric("ADX Slope", adx_sl.get('phase', '?'), f"slope={adx_sl.get('slope',0):.2f}")
            ep2.metric("EMA Ribbon", ribbon.get('quality', '?'), ribbon.get('direction', '?'))
            ep3.metric("TF Coherence", coherence.get('coherence', '?'), f"{coherence.get('score',0):.0f}%")
            ep4.metric("VWAP Zone", vwap.get('zone', '?'), vwap.get('entry_quality', '?'))

            ep5, ep6, ep7 = st.columns(3)
            ep5.metric("Candle Struct", candle.get('quality', '?'), candle.get('pattern_type', '?'))
            ep6.metric("Mom Accel", maccel.get('phase', '?'), f"conf={maccel.get('confidence',0):.0f}%")
            ep7.metric("ATR Channel", atr_ch.get('quality', '?'), f"pos={atr_ch.get('channel_position',0.5):.2f}")

            # ── V23 SNIPER ENGINE ──
            st.markdown("## Sniper Engine V23")
            ms_data = data.get('MKT_STRUCTURE', {})
            cm_data = data.get('CANDLE_MOMENTUM', {})
            pb_data = data.get('PULLBACK_QUALITY', {})
            sw_data = data.get('LIQ_SWEEP', {})
            es_data = data.get('ENTRY_SYNC', {})
            cp_data = data.get('CONT_PATTERN', {})

            s1, s2, s3, s4 = st.columns(4)
            ms_trend = ms_data.get('trend', '?')
            ms_event = ms_data.get('last_event', 'NONE')
            ms_color = "🟢" if ms_event.startswith("BOS_BULL") or ms_event.startswith("CHOCH_BULL") else "🔴" if ms_event.startswith("BOS_BEAR") or ms_event.startswith("CHOCH_BEAR") else "⚪"
            s1.metric(f"Mkt Structure {ms_color}", ms_trend, ms_event)
            s2.metric("Candle Mom", cm_data.get('conviction', '?'), f"score={cm_data.get('score',0):.0f}")
            s3.metric("Pullback Q", pb_data.get('quality', '?'), f"depth={pb_data.get('depth_pct',0):.0%}")
            s4.metric("Entry Sync", f"{es_data.get('score', 0)}/100", es_data.get('ready', '?'))

            s5, s6, s7 = st.columns(3)
            sweep_txt = sw_data.get('type', 'NONE')
            s5.metric("Liq Sweep", "🎯 YES" if sw_data.get('sweep') else "—", sweep_txt if sweep_txt != 'NONE' else '')
            s6.metric("Continuation", cp_data.get('pattern', 'NONE'), f"{cp_data.get('confidence',0)}%")
            er_txt = f"→ {data.get('REVERSAL_DIR','?')}" if data.get('EARLY_REVERSAL') else "No"
            rw_txt = f"{data.get('RW_PENALTY',0)}" if data.get('RW_PENALTY',0) != 0 else "OK"
            s7.metric("Early Reversal", "⚡ YES" if data.get('EARLY_REVERSAL') else "—", er_txt if data.get('EARLY_REVERSAL') else '')

            # V23: Multi-entry levels (if signal active)
            if data.get('ENTRY_SNIPER') and any(x in data.get('FINAL_DECISION','') for x in ["LONG","SHORT"]):
                st.markdown("### 🎯 Entry Levels")
                el1, el2, el3 = st.columns(3)
                el1.metric("Agressivo", f"{data.get('ENTRY_AGGRESSIVE',0):.5f}")
                el2.metric("Ideal", f"{data.get('ENTRY_IDEAL',0):.5f}")
                el3.metric("Sniper", f"{data.get('ENTRY_SNIPER',0):.5f}")
                tl1, tl2, tl3 = st.columns(3)
                tl1.metric("Trail → BE", f"{data.get('TRAIL_BE',0):.5f}")
                tl2.metric("Trail → 1R", f"{data.get('TRAIL_1R',0):.5f}")
                mc_conf = data.get('MC_CONFIDENCE', 'LOW')
                mc_color = "🟢" if mc_conf == "HIGH" else "🟡"
                tl3.metric(f"MC Confidence {mc_color}", mc_conf, f"{data.get('TOTAL_TRADES',0)} trades")

            # ── V24-BC: BOOM/CRASH ENGINE ──
            st.markdown("## ⚡ Boom/Crash Engine")
            bcs = data.get('BC_SPIKE', {})
            bcd = data.get('BC_DRIFT', {})
            bcf = data.get('BC_FADE', {})
            bcfr = data.get('BC_FREQ', {})
            bcst = data.get('BC_STOCH', {})
            bcab = data.get('BC_ABSORB', {})
            bcm = data.get('BC_MULTI', {})

            # Spike Detection row
            bc1, bc2, bc3, bc4 = st.columns(4)
            spike_prob = bcs.get('probability', 0)
            spike_color = "🔴" if spike_prob >= 60 else "🟡" if spike_prob >= 40 else "🟢"
            bc1.metric(f"Spike Prob {spike_color}", f"{spike_prob}%", bcs.get('type', 'NONE'))
            bc2.metric("RSI Zone", bcs.get('rsi_zone', '?'), f"RSI={bcs.get('rsi_value', 50)}")
            bc3.metric("Drift Count", f"{bcs.get('drift_count', 0)} bars")
            bc4.metric("Last Spike", f"{bcs.get('candles_since_last', '?')} bars ago")

            # Drift Analysis row
            bc5, bc6, bc7, bc8 = st.columns(4)
            drift_safe = "✅ SAFE" if bcd.get('safe_to_ride') else "❌ RISKY"
            bc5.metric("Drift", f"{bcd.get('direction','?')} {bcd.get('strength',0)}%", bcd.get('quality', '?'))
            bc6.metric("Drift Ride", drift_safe)
            # Frequency
            freq_win = bcfr.get('next_spike_window', '?')
            freq_color = "🔴" if freq_win == "IMMINENT" else "🟡" if freq_win == "SOON" else "🟢"
            bc7.metric(f"Spike Window {freq_color}", freq_win, f"avg={bcfr.get('avg_interval',0):.0f} bars")
            bc8.metric("Spike Count", f"{bcfr.get('spike_count',0)}", f"in last 100 bars")

            # Stochastic + Post-spike + Absorption row
            bc9, bc10, bc11 = st.columns(3)
            stoch_sig = bcst.get('signal', 'WAIT')
            stoch_color = "🟢" if stoch_sig != "WAIT" else "⚪"
            bc9.metric(f"Stoch Timer {stoch_color}", stoch_sig, f"K={bcst.get('stoch_k',50):.0f} D={bcst.get('stoch_d',50):.0f}")
            fade_txt = f"→ {bcf.get('fade_direction','?')}" if bcf.get('post_spike') else "No spike"
            bc10.metric("Post-Spike", "🎯 ACTIVE" if bcf.get('post_spike') else "—", fade_txt)
            bc11.metric("Absorption", "💪 YES" if bcab.get('absorption') else "—",
                       f"{bcab.get('type','')} {bcab.get('strength',0):.0f}%" if bcab.get('absorption') else "")

            # V24: Regime + Kurtosis + Conflicts row
            bc_rgm = data.get('BC_REGIME', {})
            bc_krt = data.get('BC_KURTOSIS', {})
            bc_cfl = data.get('BC_CONFLICTS', {})
            bc12, bc13, bc14, bc15 = st.columns(4)
            rgm = bc_rgm.get('regime', '?')
            rgm_colors = {"DRIFT_SMOOTH":"🟢","CHOPPY":"🟡","PRE_SPIKE":"🔴","POST_SPIKE":"🟠","SPIKE_CLUSTER":"⚫"}
            bc12.metric(f"BC Regime {rgm_colors.get(rgm,'⚪')}", rgm, f"SL×{bc_rgm.get('sl_mult',1.0):.1f}")
            kurt_v = bc_krt.get('kurtosis', 3.0)
            kurt_c = "🔴" if kurt_v > 5 else "🟡" if kurt_v > 3.5 else "🟢"
            bc13.metric(f"Kurtosis {kurt_c}", f"{kurt_v:.1f}", bc_krt.get('regime', '?'))
            conflicts = bc_cfl.get('conflicts', [])
            cfl_txt = ", ".join(conflicts) if conflicts else "None"
            bc14.metric("⚠ Conflicts" if conflicts else "✅ No Conflicts", cfl_txt[:20],
                       f"penalty=-{bc_cfl.get('conflict_penalty',0)}")
            # Multi-spike
            bc15.metric("Multi-Spike", bcm.get('pattern', 'NONE'), f"{bcm.get('consecutive_spikes',0)} spikes")

            # V24: Expectancy + Kill-Switch row
            exp_val = data.get('EXPECTANCY', 0)
            exp_stress = data.get('EXPECTANCY_STRESSED', 0)
            meltdown_info = data.get('MELTDOWN', {})
            bc16, bc17, bc18 = st.columns(3)
            exp_c = "🟢" if exp_val > 0 else "🔴"
            bc16.metric(f"Expectancy {exp_c}", f"{exp_val:.3f}R",
                       f"Stressed: {exp_stress:.3f}R {'⚠ HIGH RISK' if exp_stress < 0 else '✅'}")
            streak = meltdown_info.get('streak', 0)
            ks_c = "🔴" if streak >= 5 else "🟡" if streak >= 3 else "🟢"
            bc17.metric(f"Kill-Switch {ks_c}", f"{streak} losses",
                       meltdown_info.get('reason', 'OK') or 'OK')
            # Clean ATR
            clean_atr_val = data.get('BC_CLEAN_ATR', 0)
            bc18.metric("Clean ATR", f"{clean_atr_val:.2f}",
                       f"vs raw={data.get('RAW_ATR',0):.2f}")

            # Supply/Demand zones
            bcsd = data.get('BC_SD_ZONES', {})
            if bcsd.get('nearest_demand') or bcsd.get('nearest_supply'):
                sd1, sd2 = st.columns(2)
                if bcsd.get('nearest_demand'):
                    sd1.metric("📍 Demand", f"{bcsd['nearest_demand']['price']:.2f}",
                              f"str={bcsd['nearest_demand'].get('strength',0):.1f}×ATR")
                if bcsd.get('nearest_supply'):
                    sd2.metric("📍 Supply", f"{bcsd['nearest_supply']['price']:.2f}",
                              f"str={bcsd['nearest_supply'].get('strength',0):.1f}×ATR")

            st.markdown("## Distribution")
            da = data.get('DIST_ANALYSIS', {})
            d1, d2, d3, d4 = st.columns(4)
            d1.metric("Skewness", f"{da.get('skewness',0):.3f}")
            d2.metric("Kurtosis", f"{da.get('kurtosis',3):.3f}")
            d3.metric("Tails", da.get('tail_risk', '—'))
            d4.metric("Percentile", f"{da.get('percentile',50):.0f}%")

            # ── BACKTEST ──
            st.markdown("## Validation")
            v1, v2, v3, v4, v5, v6 = st.columns(6)
            v1.metric("Win Rate", f"{data['WIN_RATE']}%")
            v2.metric("Profit Factor", f"{data['PROFIT_FACTOR']}")
            v3.metric("Sharpe", f"{data['SHARPE']}")
            v4.metric("Sortino", f"{data['SORTINO']}")
            v5.metric("Max DD", f"{data['MAX_DRAWDOWN']}R")
            v6.metric("Trades", f"{data['TOTAL_TRADES']}")

            # V24: Setup breakdown with avg_win/avg_loss
            if data.get('SETUP_STATS'):
                parts = []
                for k, v in data['SETUP_STATS'].items():
                    aw = v.get('avg_win', 0)
                    al = v.get('avg_loss', 0)
                    detail = f"{k} {v['trades']}t/{v['wr']}%"
                    if aw > 0 or al > 0:
                        detail += f" W:{aw:.1f}/L:{al:.1f}"
                    parts.append(detail)
                st.markdown(f"<p class='mono text-xs muted' style='margin-top:-8px;'>{' · '.join(parts)}</p>",
                            unsafe_allow_html=True)

            # V24: High Risk warning
            if data.get('HIGH_RISK'):
                st.warning("⚠ **HIGH RISK**: Expectancy goes negative under -20% WR stress test")

            # Monte Carlo
            mc1, mc2, mc3, mc4 = st.columns(4)
            mc1.metric("MC Median", f"{data['MC_MEDIAN']}R")
            mc2.metric("MC P5", f"{data['MC_P5']}R")
            mc3.metric("MC Positive", f"{data['MC_POSITIVE']}%")
            mc_conf = data.get('MC_CONFIDENCE', 'LOW')
            mc4.metric("MC Confidence", mc_conf, f"{data.get('TOTAL_TRADES',0)} trades")

            # ── CONFLUENCES & RISKS ──
            if data['CONFLUENCES'] or data['RISKS']:
                st.markdown("## Confluences")
                conf_html = ""
                for c in data.get('CONFLUENCES', []):
                    conf_html += f"<span class='pill pill-green'>{c}</span> "
                for r in data.get('RISKS', []):
                    conf_html += f"<span class='pill pill-red'>{r}</span> "
                st.markdown(conf_html, unsafe_allow_html=True)

            # ── TRADE PLAN ──
            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
            is_active = any(x in d for x in ["SWING","DAY","BREAKOUT","STORM","REVERSION",
                                               "COMPRESS","DRIFT","STEP","DEVIATION","PRICE"])
            if is_active:
                st.markdown("## Trade Plan")

                # Entry/SL/TP as clean card
                entry_color = "#22c55e" if "LONG" in d else "#ef4444"
                st.markdown(f"""<div class='card'>
                    <div class='plan-row'>
                        <span class='plan-label'>Entry</span>
                        <span class='plan-value' style='color:{entry_color};'>{data['ENTRY']}</span>
                        <span class='plan-note'>{data['ENTRY_TYPE']}</span>
                    </div>
                    <div class='plan-row'>
                        <span class='plan-label'>Stop</span>
                        <span class='plan-value' style='color:#ef4444;'>{data['SL']}</span>
                        <span class='plan-note'>ATR x{data.get('ADAPTED_PROFILE',{}).get('sl_atr_mult','—')}</span>
                    </div>
                    <div class='plan-row'>
                        <span class='plan-label'>TP 1</span>
                        <span class='plan-value' style='color:#22c55e;'>{data['TP1']}</span>
                        <span class='plan-note'>Smart TP (S/R aware)</span>
                    </div>
                    <div class='plan-row'>
                        <span class='plan-label'>TP 2</span>
                        <span class='plan-value' style='color:#22c55e;'>{data['TP2']}</span>
                        <span class='plan-note'>Trail target</span>
                    </div>
                    <div class='plan-row'>
                        <span class='plan-label'>Trigger</span>
                        <span class='plan-value'>{"✓" if data.get('TRIGGER_OK') else "✗"}</span>
                        <span class='plan-note'>M5 {data.get('TRIGGER_TYPE','—')}</span>
                    </div>
                </div>""", unsafe_allow_html=True)

                # Pyramid
                pyr = data.get('PYRAMID', {})
                if pyr.get('n_levels', 0) > 1:
                    st.markdown("## Pyramid")
                    pyr_html = "<div class='card'>"
                    for i, l in enumerate(pyr.get('levels', [])):
                        pyr_html += f"""<div class='plan-row'>
                            <span class='plan-label'>Level {i+1}</span>
                            <span class='plan-value'>{l['entry']}</span>
                            <span class='plan-note'>{l['risk_pct']}% · {l['trigger']}</span>
                        </div>"""
                    pyr_html += f"""<div class='plan-row' style='border-top:1px solid #27272a;'>
                        <span class='plan-label'>Total</span>
                        <span class='plan-value'>{pyr['total_risk_pct']}%</span>
                        <span class='plan-note'>{pyr['n_levels']} levels</span>
                    </div></div>"""
                    st.markdown(pyr_html, unsafe_allow_html=True)

            elif "BLOCKED" in d:
                reason = d.replace("BLOCKED (","").rstrip(")")
                st.markdown(f"""<div class='card' style='border-color:#ef444420;'>
                    <span style='color:#ef4444;font-size:14px;font-weight:500;'>Blocked</span><br>
                    <span class='mono text-sm muted'>{reason}</span>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown("""<div class='card'>
                    <span style='color:#f59e0b;font-size:14px;font-weight:500;'>Monitoring</span><br>
                    <span class='text-sm muted'>No setup detected. Waiting for conditions.</span>
                </div>""", unsafe_allow_html=True)

            # ── CHARTS ──
            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
            st.markdown("## Charts")
            tabs = st.tabs(["H4", "H1", "M15"])
            for i, t in enumerate(tabs):
                with t:
                    st.image(imgs[i], use_container_width=True)

            # ── AI INSIGHT ──
            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
            st.markdown("## AI Analysis")
            st.markdown(f"""<div class='card-accent'>
                {ai}
            </div>""", unsafe_allow_html=True)

# ==============================================================================
# SCANNER MODE
# ==============================================================================
elif mode == "Scanner":
    st.markdown("## Scanner")
    st.markdown("<p class='text-sm muted' style='margin-top:-8px;'>Scan all synthetic indices for statistical edge opportunities.</p>",
                unsafe_allow_html=True)

    if st.button("Scan All Assets", use_container_width=True):
        with st.spinner("Scanning..."):
            async def run_scan():
                return await asyncio.gather(*[quick_scan(c, n) for n, c in assets.items()])
            results = asyncio.run(run_scan())
            valid = sorted([r for r in results if r], key=lambda x: x['score'], reverse=True)

        if valid:
            st.markdown(f"<p class='text-sm muted' style='margin:12px 0;'>{len(valid)} assets scanned</p>",
                        unsafe_allow_html=True)

            for i, r in enumerate(valid[:12]):
                score = r['score']
                sc = "#22c55e" if score >= 50 else "#f59e0b" if score >= 30 else "#52525b"
                bias_c = "#22c55e" if r['bias'] == "BULLISH" else "#ef4444"
                vr_tag = "<span class='pill pill-green' style='font-size:10px;'>VR Edge</span>" if r.get('vr_edge') else ""

                st.markdown(f"""<div class='scan-row'>
                    <span class='scan-rank'>#{i+1}</span>
                    <span class='scan-name'>{r['name']}</span>
                    <span class='scan-score' style='color:{sc};'>{score}</span>
                    <div>
                        <span class='pill' style='font-size:10px;color:{bias_c};border-color:{bias_c}30;'>{r['bias']}</span>
                        {vr_tag}
                    </div>
                    <span class='scan-meta' style='min-width:260px;text-align:right;'>
                        ADX {r['adx']} · H {r['hurst']} · Z {r['zscore']} · {r['regime'][:8]} · {r['gen_signal'][:12]}
                    </span>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("No results found")
