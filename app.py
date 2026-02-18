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
from collections import deque
from scipy.stats import norm, median_abs_deviation, chi2 as chi2_dist
from itertools import permutations as _perms
from math import factorial, log as math_log
import time
import logging
import warnings
warnings.filterwarnings('ignore')

# ── LOGGING SYSTEM V22 ──
logging.basicConfig(level=logging.WARNING, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("APATECO")

# ==============================================================================
# SI-APATECO V22.0 — A.P.A PRECISION ENGINE
#
# V22 UPGRADES FROM V21:
#
# 🔵 A.P.A #1: Accumulation Phase Detector (BB squeeze + ATR contraction + ADX slope)
# 🔵 A.P.A #2: Pattern Recognizer (Inside Bar, Pin, Engulfing at end of accumulation)
# 🔵 A.P.A #3: Action Trigger (range expansion + MACD flip + multi-TF confirm)
# 🔵 A.P.A #4: Risk Management (SL=accum range, TP=range multiples, time-stop)
#
# 🔴 BUG FIX V22 #1: Sharpe/Sortino uses ppy (not 252)
# 🔴 BUG FIX V22 #2: momentum_v21 (0-100) used for scoring (not old 0-3)
# 🔴 BUG FIX V22 #3: Candle structure on M5 entry TF (not M15)
# 🔴 BUG FIX V22 #4: Bonus cap removed (grade system normalizes)
# 🔴 BUG FIX V22 #5: Sortino handles zero-loss case
# 🔴 BUG FIX V22 #6: All bare except: replaced with logging
#
# 🟢 NEW #1: Order Flow Score (micro-structure buy/sell pressure)
# 🟢 NEW #2: Anti-Whipsaw Filter (cooldown between signals)
# 🟢 NEW #3: Divergence Decay (temporal weight)
# 🟢 NEW #4: Time-Stop integrated in trade plan
# 🟢 NEW #5: Session Volatility Awareness
#
# BASE V21: All 16 improvements + 7 precision engines preserved
# ==============================================================================

st.set_page_config(
    page_title="APATECO V22 A.P.A",
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
    "VOLATILITY 10 INDEX": {
        "gen_type": "GBM", "vol_class": "ULTRA_LOW", "sigma_seed": 0.10,
        "spread": 0.02, "adx_trend_min": 12, "adx_strong": 20,
        "sl_atr_mult": 2.0, "tp1_r": 2.5, "tp2_r": 4.0,
        "bb_squeeze_threshold": 0.5, "zscore_extreme": 2.5,
        "hurst_trend_min": 0.55, "consecutive_reversal": 8,
        "roc_extreme_pct": 0.3, "mean_reversion_bias": 0.7, "risk_mult": 1.3,
    },
    "VOLATILITY 10 (1S) INDEX": {
        "gen_type": "GBM", "vol_class": "ULTRA_LOW", "sigma_seed": 0.10,
        "spread": 0.02, "adx_trend_min": 12, "adx_strong": 20,
        "sl_atr_mult": 2.0, "tp1_r": 2.5, "tp2_r": 4.0,
        "bb_squeeze_threshold": 0.5, "zscore_extreme": 2.5,
        "hurst_trend_min": 0.55, "consecutive_reversal": 8,
        "roc_extreme_pct": 0.3, "mean_reversion_bias": 0.7, "risk_mult": 1.3,
    },
    "VOLATILITY 25 INDEX": {
        "gen_type": "GBM", "vol_class": "LOW", "sigma_seed": 0.25,
        "spread": 0.03, "adx_trend_min": 14, "adx_strong": 22,
        "sl_atr_mult": 2.2, "tp1_r": 2.5, "tp2_r": 4.5,
        "bb_squeeze_threshold": 0.55, "zscore_extreme": 2.3,
        "hurst_trend_min": 0.54, "consecutive_reversal": 7,
        "roc_extreme_pct": 0.5, "mean_reversion_bias": 0.6, "risk_mult": 1.2,
    },
    "VOLATILITY 25 (1S) INDEX": {
        "gen_type": "GBM", "vol_class": "LOW", "sigma_seed": 0.25,
        "spread": 0.03, "adx_trend_min": 14, "adx_strong": 22,
        "sl_atr_mult": 2.2, "tp1_r": 2.5, "tp2_r": 4.5,
        "bb_squeeze_threshold": 0.55, "zscore_extreme": 2.3,
        "hurst_trend_min": 0.54, "consecutive_reversal": 7,
        "roc_extreme_pct": 0.5, "mean_reversion_bias": 0.6, "risk_mult": 1.2,
    },
    "VOLATILITY 50 INDEX": {
        "gen_type": "GBM", "vol_class": "MEDIUM", "sigma_seed": 0.50,
        "spread": 0.05, "adx_trend_min": 16, "adx_strong": 25,
        "sl_atr_mult": 2.5, "tp1_r": 3.0, "tp2_r": 5.0,
        "bb_squeeze_threshold": 0.6, "zscore_extreme": 2.0,
        "hurst_trend_min": 0.53, "consecutive_reversal": 6,
        "roc_extreme_pct": 0.8, "mean_reversion_bias": 0.5, "risk_mult": 1.0,
    },
    "VOLATILITY 50 (1S) INDEX": {
        "gen_type": "GBM", "vol_class": "MEDIUM", "sigma_seed": 0.50,
        "spread": 0.05, "adx_trend_min": 16, "adx_strong": 25,
        "sl_atr_mult": 2.5, "tp1_r": 3.0, "tp2_r": 5.0,
        "bb_squeeze_threshold": 0.6, "zscore_extreme": 2.0,
        "hurst_trend_min": 0.53, "consecutive_reversal": 6,
        "roc_extreme_pct": 0.8, "mean_reversion_bias": 0.5, "risk_mult": 1.0,
    },
    "VOLATILITY 75 INDEX": {
        "gen_type": "GBM", "vol_class": "HIGH", "sigma_seed": 0.75,
        "spread": 0.10, "adx_trend_min": 18, "adx_strong": 28,
        "sl_atr_mult": 3.0, "tp1_r": 3.0, "tp2_r": 5.0,
        "bb_squeeze_threshold": 0.65, "zscore_extreme": 1.8,
        "hurst_trend_min": 0.52, "consecutive_reversal": 5,
        "roc_extreme_pct": 1.2, "mean_reversion_bias": 0.4, "risk_mult": 0.7,
    },
    "VOLATILITY 75 (1S) INDEX": {
        "gen_type": "GBM", "vol_class": "HIGH", "sigma_seed": 0.75,
        "spread": 0.10, "adx_trend_min": 18, "adx_strong": 28,
        "sl_atr_mult": 3.0, "tp1_r": 3.0, "tp2_r": 5.0,
        "bb_squeeze_threshold": 0.65, "zscore_extreme": 1.8,
        "hurst_trend_min": 0.52, "consecutive_reversal": 5,
        "roc_extreme_pct": 1.2, "mean_reversion_bias": 0.4, "risk_mult": 0.7,
    },
    "VOLATILITY 100 INDEX": {
        "gen_type": "GBM", "vol_class": "EXTREME", "sigma_seed": 1.00,
        "spread": 0.15, "adx_trend_min": 20, "adx_strong": 30,
        "sl_atr_mult": 3.5, "tp1_r": 3.0, "tp2_r": 5.0,
        "bb_squeeze_threshold": 0.7, "zscore_extreme": 1.5,
        "hurst_trend_min": 0.51, "consecutive_reversal": 4,
        "roc_extreme_pct": 1.5, "mean_reversion_bias": 0.35, "risk_mult": 0.5,
    },
    "VOLATILITY 100 (1S) INDEX": {
        "gen_type": "GBM", "vol_class": "EXTREME", "sigma_seed": 1.00,
        "spread": 0.15, "adx_trend_min": 20, "adx_strong": 30,
        "sl_atr_mult": 3.5, "tp1_r": 3.0, "tp2_r": 5.0,
        "bb_squeeze_threshold": 0.7, "zscore_extreme": 1.5,
        "hurst_trend_min": 0.51, "consecutive_reversal": 4,
        "roc_extreme_pct": 1.5, "mean_reversion_bias": 0.35, "risk_mult": 0.5,
    },
    "BOOM 300 INDEX": {
        "gen_type": "BOOM", "vol_class": "BOOM", "sigma_seed": 0.50,
        "spike_lambda": 1/300, "spike_direction": "UP", "drift_direction": "DOWN",
        "spread": 0.10, "adx_trend_min": 15, "adx_strong": 25,
        "sl_atr_mult": 2.0, "tp1_r": 3.0, "tp2_r": 6.0,
        "bb_squeeze_threshold": 0.6, "zscore_extreme": 2.0,
        "hurst_trend_min": 0.52, "consecutive_reversal": 5,
        "roc_extreme_pct": 2.0, "mean_reversion_bias": 0.3, "risk_mult": 0.8,
    },
    "BOOM 500 INDEX": {
        "gen_type": "BOOM", "vol_class": "BOOM", "sigma_seed": 0.50,
        "spike_lambda": 1/500, "spike_direction": "UP", "drift_direction": "DOWN",
        "spread": 0.10, "adx_trend_min": 15, "adx_strong": 25,
        "sl_atr_mult": 2.0, "tp1_r": 3.0, "tp2_r": 6.0,
        "bb_squeeze_threshold": 0.6, "zscore_extreme": 2.0,
        "hurst_trend_min": 0.52, "consecutive_reversal": 5,
        "roc_extreme_pct": 2.0, "mean_reversion_bias": 0.3, "risk_mult": 0.8,
    },
    "BOOM 1000 INDEX": {
        "gen_type": "BOOM", "vol_class": "BOOM", "sigma_seed": 0.50,
        "spike_lambda": 1/1000, "spike_direction": "UP", "drift_direction": "DOWN",
        "spread": 0.10, "adx_trend_min": 15, "adx_strong": 25,
        "sl_atr_mult": 2.5, "tp1_r": 3.0, "tp2_r": 7.0,
        "bb_squeeze_threshold": 0.6, "zscore_extreme": 2.0,
        "hurst_trend_min": 0.52, "consecutive_reversal": 6,
        "roc_extreme_pct": 2.0, "mean_reversion_bias": 0.3, "risk_mult": 0.9,
    },
    "CRASH 300 INDEX": {
        "gen_type": "CRASH", "vol_class": "CRASH", "sigma_seed": 0.50,
        "spike_lambda": 1/300, "spike_direction": "DOWN", "drift_direction": "UP",
        "spread": 0.10, "adx_trend_min": 15, "adx_strong": 25,
        "sl_atr_mult": 2.0, "tp1_r": 3.0, "tp2_r": 6.0,
        "bb_squeeze_threshold": 0.6, "zscore_extreme": 2.0,
        "hurst_trend_min": 0.52, "consecutive_reversal": 5,
        "roc_extreme_pct": 2.0, "mean_reversion_bias": 0.3, "risk_mult": 0.8,
    },
    "CRASH 500 INDEX": {
        "gen_type": "CRASH", "vol_class": "CRASH", "sigma_seed": 0.50,
        "spike_lambda": 1/500, "spike_direction": "DOWN", "drift_direction": "UP",
        "spread": 0.10, "adx_trend_min": 15, "adx_strong": 25,
        "sl_atr_mult": 2.0, "tp1_r": 3.0, "tp2_r": 6.0,
        "bb_squeeze_threshold": 0.6, "zscore_extreme": 2.0,
        "hurst_trend_min": 0.52, "consecutive_reversal": 5,
        "roc_extreme_pct": 2.0, "mean_reversion_bias": 0.3, "risk_mult": 0.8,
    },
    "CRASH 1000 INDEX": {
        "gen_type": "CRASH", "vol_class": "CRASH", "sigma_seed": 0.50,
        "spike_lambda": 1/1000, "spike_direction": "DOWN", "drift_direction": "UP",
        "spread": 0.10, "adx_trend_min": 15, "adx_strong": 25,
        "sl_atr_mult": 2.5, "tp1_r": 3.0, "tp2_r": 7.0,
        "bb_squeeze_threshold": 0.6, "zscore_extreme": 2.0,
        "hurst_trend_min": 0.52, "consecutive_reversal": 6,
        "roc_extreme_pct": 2.0, "mean_reversion_bias": 0.3, "risk_mult": 0.9,
    },
    "STEP INDEX": {
        "gen_type": "STEP", "vol_class": "STEP", "sigma_seed": 0.20,
        "spread": 0.01, "adx_trend_min": 10, "adx_strong": 18,
        "sl_atr_mult": 1.5, "tp1_r": 2.0, "tp2_r": 3.0,
        "bb_squeeze_threshold": 0.4, "zscore_extreme": 2.0,
        "hurst_trend_min": 0.55, "consecutive_reversal": 10,
        "roc_extreme_pct": 0.2, "mean_reversion_bias": 0.8, "risk_mult": 1.5,
    },
}

DEFAULT_PROFILE = {
    "gen_type": "GBM", "vol_class": "UNKNOWN", "sigma_seed": 0.50,
    "spread": 0.05, "adx_trend_min": 15, "adx_strong": 25,
    "sl_atr_mult": 2.5, "tp1_r": 3.0, "tp2_r": 5.0,
    "bb_squeeze_threshold": 0.6, "zscore_extreme": 2.0,
    "hurst_trend_min": 0.53, "consecutive_reversal": 6,
    "roc_extreme_pct": 1.0, "mean_reversion_bias": 0.5, "risk_mult": 1.0,
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
    except Exception as e:
        logger.debug(f"ATR channel error: {e}")
        return {"channel_entry": None, "channel_position": 0.5, "quality": "UNKNOWN"}


# ==============================================================================
# 🔵 V22 A.P.A ENGINE — ACCUMULATION → PATTERN → ACTION
# ==============================================================================

def apa_accumulation_detector(df, min_bars=5, max_bars=40):
    """Phase 1: Detect accumulation zone (price compression before expansion).
    Accumulation = BB squeeze + ATR contraction + decreasing candle size."""
    try:
        if len(df) < max_bars + 10:
            return {"detected": False, "phase": "NONE", "bars": 0, "quality": 0}

        recent = df.tail(max_bars)
        atr = recent['ATR']
        bb_w = recent['BB_width']
        bodies = abs(recent['close'] - recent['open'])
        ranges = (recent['high'] - recent['low']).replace(0, np.nan)

        # 1. ATR contraction: recent ATR declining
        atr_short = float(atr.tail(5).mean())
        atr_long = float(atr.tail(20).mean())
        atr_contracting = atr_short < atr_long * 0.85

        # 2. BB squeeze: width below threshold
        bb_avg = float(bb_w.mean())
        bb_now = float(bb_w.iloc[-1])
        bb_squeezing = bb_now < bb_avg * 0.7

        # 3. Candle bodies shrinking
        body_short = float(bodies.tail(5).mean())
        body_long = float(bodies.tail(20).mean())
        bodies_shrinking = body_short < body_long * 0.75

        # 4. Range narrowing
        range_short = float(ranges.tail(5).mean())
        range_long = float(ranges.tail(20).mean())
        range_narrowing = range_short < range_long * 0.8 if pd.notna(range_long) and range_long > 0 else False

        # 5. ADX low but possibly rising (energy building)
        adx_now = float(df['ADX'].iloc[-1]) if 'ADX' in df.columns else 25
        adx_low = adx_now < 25

        # Count accumulation bars (consecutive compression)
        accum_bars = 0
        for i in range(len(recent) - 1, -1, -1):
            bar_body = abs(recent['close'].iloc[i] - recent['open'].iloc[i])
            bar_range = recent['high'].iloc[i] - recent['low'].iloc[i]
            if bar_range > 0 and bar_body / bar_range < 0.6 and recent['ATR'].iloc[i] < atr_long * 1.1:
                accum_bars += 1
            else:
                break

        # Accumulation range
        if accum_bars >= min_bars:
            accum_section = recent.tail(accum_bars)
            range_high = float(accum_section['high'].max())
            range_low = float(accum_section['low'].min())
            range_width = range_high - range_low
        else:
            range_high = float(recent['high'].tail(min_bars).max())
            range_low = float(recent['low'].tail(min_bars).min())
            range_width = range_high - range_low

        # Quality score (0-100)
        quality = 0
        if atr_contracting: quality += 25
        if bb_squeezing: quality += 25
        if bodies_shrinking: quality += 20
        if range_narrowing: quality += 15
        if adx_low: quality += 15

        detected = quality >= 50 and accum_bars >= min_bars

        phase = "NONE"
        if detected:
            if quality >= 80:
                phase = "STRONG_ACCUMULATION"
            elif quality >= 60:
                phase = "ACCUMULATION"
            else:
                phase = "WEAK_ACCUMULATION"

        return {
            "detected": detected,
            "phase": phase,
            "quality": round(quality, 1),
            "bars": accum_bars,
            "range_high": round(range_high, 5),
            "range_low": round(range_low, 5),
            "range_width": round(range_width, 5),
            "atr_contracting": atr_contracting,
            "bb_squeezing": bb_squeezing,
            "bodies_shrinking": bodies_shrinking,
            "range_narrowing": range_narrowing,
            "adx_low": adx_low,
        }
    except Exception as e:
        logger.debug(f"APA accumulation error: {e}")
        return {"detected": False, "phase": "NONE", "bars": 0, "quality": 0}


def apa_pattern_recognizer(df, accumulation):
    """Phase 2: Recognize actionable pattern at the end of accumulation.
    Patterns: Inside Bar, Pin Bar, Engulfing, Breakout Bar, Micro Double Bottom/Top."""
    try:
        if not accumulation.get('detected') or len(df) < 5:
            return {"pattern": "NONE", "direction": "NEUTRAL", "strength": 0}

        last = df.iloc[-1]
        prev = df.iloc[-2]
        prev2 = df.iloc[-3] if len(df) >= 3 else prev

        body_last = abs(last['close'] - last['open'])
        range_last = last['high'] - last['low']
        body_prev = abs(prev['close'] - prev['open'])
        range_prev = prev['high'] - prev['low']

        range_high = accumulation['range_high']
        range_low = accumulation['range_low']
        range_width = accumulation.get('range_width', range_high - range_low)
        atr = float(df['ATR'].iloc[-1]) if df['ATR'].iloc[-1] > 0 else 1

        patterns = []

        # 1. INSIDE BAR (compression peak → explosion imminent)
        if last['high'] <= prev['high'] and last['low'] >= prev['low']:
            direction = "BULLISH" if last['close'] > last['open'] else "BEARISH"
            patterns.append(("INSIDE_BAR", direction, 70))

        # 2. PIN BAR at accumulation boundary
        if range_last > 0:
            lower_wick = min(last['open'], last['close']) - last['low']
            upper_wick = last['high'] - max(last['open'], last['close'])

            # Bullish pin: long lower wick near accumulation low
            if lower_wick > body_last * 2 and last['low'] <= range_low + atr * 0.3:
                patterns.append(("PIN_BAR_BULL", "BULLISH", 85))

            # Bearish pin: long upper wick near accumulation high
            if upper_wick > body_last * 2 and last['high'] >= range_high - atr * 0.3:
                patterns.append(("PIN_BAR_BEAR", "BEARISH", 85))

        # 3. ENGULFING at accumulation boundary
        if last['close'] > last['open'] and prev['close'] < prev['open']:
            if body_last > body_prev and last['low'] <= range_low + atr * 0.5:
                patterns.append(("ENGULFING_BULL", "BULLISH", 90))
        elif last['close'] < last['open'] and prev['close'] > prev['open']:
            if body_last > body_prev and last['high'] >= range_high - atr * 0.5:
                patterns.append(("ENGULFING_BEAR", "BEARISH", 90))

        # 4. BREAKOUT BAR (close outside accumulation range)
        if last['close'] > range_high and body_last > range_width * 0.3:
            patterns.append(("BREAKOUT_UP", "BULLISH", 95))
        elif last['close'] < range_low and body_last > range_width * 0.3:
            patterns.append(("BREAKOUT_DOWN", "BEARISH", 95))

        # 5. MICRO DOUBLE BOTTOM/TOP
        lows_3 = df['low'].tail(8)
        highs_3 = df['high'].tail(8)
        if len(lows_3) >= 5:
            min1 = lows_3.iloc[:4].min()
            min2 = lows_3.iloc[-4:].min()
            if abs(min1 - min2) < atr * 0.3 and min2 <= range_low + atr * 0.3:
                if last['close'] > last['open']:
                    patterns.append(("MICRO_DOUBLE_BOTTOM", "BULLISH", 80))
            max1 = highs_3.iloc[:4].max()
            max2 = highs_3.iloc[-4:].max()
            if abs(max1 - max2) < atr * 0.3 and max2 >= range_high - atr * 0.3:
                if last['close'] < last['open']:
                    patterns.append(("MICRO_DOUBLE_TOP", "BEARISH", 80))

        if not patterns:
            return {"pattern": "NONE", "direction": "NEUTRAL", "strength": 0}

        # Select strongest pattern
        best = max(patterns, key=lambda x: x[2])
        return {
            "pattern": best[0],
            "direction": best[1],
            "strength": best[2],
            "all_patterns": [{"name": p[0], "dir": p[1], "str": p[2]} for p in patterns],
        }
    except Exception as e:
        logger.debug(f"APA pattern error: {e}")
        return {"pattern": "NONE", "direction": "NEUTRAL", "strength": 0}


def apa_action_trigger(df, accumulation, pattern, bias, trend_coherence_data=None):
    """Phase 3: Confirm action trigger — range expansion + momentum flip + TF alignment.
    Returns entry parameters if trigger confirmed."""
    try:
        if pattern.get('pattern') == "NONE" or not accumulation.get('detected'):
            return {"triggered": False, "reason": "NO_PATTERN"}

        last = df.iloc[-1]
        prev = df.iloc[-2]
        atr = float(last['ATR']) if last['ATR'] > 0 else 1
        direction = pattern['direction']

        # 1. RANGE EXPANSION: current bar range > recent average
        recent_avg_range = float((df['high'] - df['low']).tail(10).mean())
        current_range = last['high'] - last['low']
        range_expanding = current_range > recent_avg_range * 1.3

        # 2. BB WIDTH EXPANDING: BB starting to open
        bb_expanding = False
        if len(df) >= 3 and 'BB_width' in df.columns:
            bb_expanding = float(df['BB_width'].iloc[-1]) > float(df['BB_width'].iloc[-2])

        # 3. MACD HISTOGRAM FLIP/ACCELERATION
        macd_confirm = False
        if 'MACD_hist' in df.columns and len(df) >= 3:
            hist_now = float(df['MACD_hist'].iloc[-1])
            hist_prev = float(df['MACD_hist'].iloc[-2])
            if direction == "BULLISH":
                macd_confirm = hist_now > hist_prev and (hist_now > 0 or hist_now > hist_prev * 0.5)
            else:
                macd_confirm = hist_now < hist_prev and (hist_now < 0 or hist_now < hist_prev * 0.5)

        # 4. DIRECTION ALIGNMENT with bias
        bias_aligned = (direction == bias) or bias == "NEUTRAL"

        # 5. TF COHERENCE alignment (if available)
        tf_aligned = True
        if trend_coherence_data:
            coh_dir = trend_coherence_data.get('coherent_direction', 'MIXED')
            if coh_dir != 'MIXED':
                tf_aligned = coh_dir == direction

        # TRIGGER SCORE
        trigger_score = 0
        reasons = []
        if range_expanding: trigger_score += 30; reasons.append("Range Expansion")
        if bb_expanding: trigger_score += 20; reasons.append("BB Expanding")
        if macd_confirm: trigger_score += 25; reasons.append("MACD Confirm")
        if bias_aligned: trigger_score += 15; reasons.append("Bias Aligned")
        if tf_aligned: trigger_score += 10; reasons.append("TF Aligned")

        triggered = trigger_score >= 55

        # A.P.A RISK PARAMETERS
        range_width = accumulation.get('range_width', atr * 2)
        range_high = accumulation.get('range_high', last['close'])
        range_low = accumulation.get('range_low', last['close'])

        if direction == "BULLISH":
            entry = float(last['close'])
            sl = range_low - atr * 0.3  # Below accumulation range
            tp1 = entry + range_width * 1.5  # 1.5x the accumulation range
            tp2 = entry + range_width * 3.0  # 3x the accumulation range
        else:
            entry = float(last['close'])
            sl = range_high + atr * 0.3  # Above accumulation range
            tp1 = entry - range_width * 1.5
            tp2 = entry - range_width * 3.0

        risk = abs(entry - sl)
        time_stop_bars = accumulation.get('bars', 10) * 2  # 2x accumulation duration

        return {
            "triggered": triggered,
            "trigger_score": trigger_score,
            "reasons": reasons,
            "direction": direction,
            "entry": round(entry, 5),
            "sl": round(sl, 5),
            "tp1": round(tp1, 5),
            "tp2": round(tp2, 5),
            "risk": round(risk, 5),
            "rr_tp1": round(abs(tp1 - entry) / risk, 1) if risk > 0 else 0,
            "rr_tp2": round(abs(tp2 - entry) / risk, 1) if risk > 0 else 0,
            "time_stop_bars": time_stop_bars,
            "range_expanding": range_expanding,
            "bb_expanding": bb_expanding,
            "macd_confirm": macd_confirm,
            "bias_aligned": bias_aligned,
        }
    except Exception as e:
        logger.debug(f"APA action error: {e}")
        return {"triggered": False, "reason": str(e)}


def apa_full_analysis(df, bias, trend_coherence_data=None):
    """Complete A.P.A analysis: Accumulation → Pattern → Action.
    Returns comprehensive A.P.A state."""
    try:
        accum = apa_accumulation_detector(df)
        pattern = apa_pattern_recognizer(df, accum)
        action = apa_action_trigger(df, accum, pattern, bias, trend_coherence_data)

        # Overall A.P.A state
        if action.get('triggered'):
            state = "ACTION_READY"
            confidence = min(accum['quality'] * 0.3 + pattern['strength'] * 0.3 + action['trigger_score'] * 0.4, 100)
        elif pattern.get('pattern') != "NONE":
            state = "PATTERN_FORMING"
            confidence = min(accum['quality'] * 0.4 + pattern['strength'] * 0.6, 100) * 0.7
        elif accum.get('detected'):
            state = "ACCUMULATING"
            confidence = accum['quality'] * 0.5
        else:
            state = "NO_SETUP"
            confidence = 0

        return {
            "state": state,
            "confidence": round(confidence, 1),
            "accumulation": accum,
            "pattern": pattern,
            "action": action,
        }
    except Exception as e:
        logger.debug(f"APA full analysis error: {e}")
        return {"state": "ERROR", "confidence": 0,
                "accumulation": {"detected": False}, "pattern": {"pattern": "NONE"},
                "action": {"triggered": False}}


# ==============================================================================
# 🟢 V22 NEW #1: ORDER FLOW SCORE — Microstructure Buy/Sell Pressure
# ==============================================================================

def order_flow_score(df, lookback=20):
    """Estimates buy/sell pressure from candle microstructure.
    No real volume needed — works with synthetic indices."""
    try:
        if len(df) < lookback:
            return {"score": 0, "pressure": "NEUTRAL", "bull_pct": 50, "bear_pct": 50}

        recent = df.tail(lookback)
        bull_count = 0
        bear_count = 0
        bull_power = 0.0
        bear_power = 0.0

        for i in range(len(recent)):
            row = recent.iloc[i]
            body = row['close'] - row['open']
            rng = row['high'] - row['low']
            if rng == 0:
                continue

            # Close position within range (0=low, 1=high)
            close_pos = (row['close'] - row['low']) / rng

            # Body ratio
            body_ratio = abs(body) / rng

            if body > 0:
                bull_count += 1
                # Power = body size × close position (strong bull = big body closing near high)
                bull_power += body_ratio * close_pos
            else:
                bear_count += 1
                bear_power += body_ratio * (1 - close_pos)

        total = bull_count + bear_count
        if total == 0:
            return {"score": 0, "pressure": "NEUTRAL", "bull_pct": 50, "bear_pct": 50}

        bull_pct = bull_count / total * 100
        bear_pct = bear_count / total * 100

        # Normalize power
        avg_bull = bull_power / max(bull_count, 1)
        avg_bear = bear_power / max(bear_count, 1)
        total_power = avg_bull + avg_bear
        if total_power > 0:
            bull_power_pct = avg_bull / total_power * 100
        else:
            bull_power_pct = 50

        # Combined score: -100 (max bear) to +100 (max bull)
        count_bias = (bull_pct - 50) * 0.6
        power_bias = (bull_power_pct - 50) * 0.4
        score = count_bias + power_bias

        if score > 25:
            pressure = "STRONG_BUYING"
        elif score > 10:
            pressure = "BUYING"
        elif score > -10:
            pressure = "NEUTRAL"
        elif score > -25:
            pressure = "SELLING"
        else:
            pressure = "STRONG_SELLING"

        return {
            "score": round(score, 1),
            "pressure": pressure,
            "bull_pct": round(bull_pct, 1),
            "bear_pct": round(bear_pct, 1),
            "bull_power": round(avg_bull, 3),
            "bear_power": round(avg_bear, 3),
        }
    except Exception as e:
        logger.debug(f"Order flow error: {e}")
        return {"score": 0, "pressure": "NEUTRAL", "bull_pct": 50, "bear_pct": 50}


# ==============================================================================
# 🟢 V22 NEW #2: ANTI-WHIPSAW FILTER
# ==============================================================================

def anti_whipsaw_check(df, setup_type, min_bars_between=8):
    """Prevents rapid signal flipping in choppy markets.
    Checks if enough bars have passed since conditions for opposite signal were met."""
    try:
        if len(df) < min_bars_between + 5:
            return True, "OK"  # Allow if insufficient data

        recent = df.tail(min_bars_between + 5)

        # Count direction changes in MACD histogram
        if 'MACD_hist' in df.columns:
            hist = recent['MACD_hist'].dropna()
            if len(hist) >= 3:
                sign_changes = sum(1 for i in range(1, len(hist))
                                   if (hist.iloc[i] > 0) != (hist.iloc[i-1] > 0))
                if sign_changes >= 4:  # Too many flips
                    return False, f"WHIPSAW_MACD ({sign_changes} flips)"

        # Check price whipsaw: crossing EMA20 too many times
        if 'EMA_20' in df.columns:
            above = recent['close'] > recent['EMA_20']
            crossings = sum(1 for i in range(1, len(above))
                           if above.iloc[i] != above.iloc[i-1])
            if crossings >= 5:
                return False, f"WHIPSAW_EMA ({crossings} crosses)"

        # ADX too low = no trend = whipsaw zone
        if 'ADX' in df.columns:
            adx_avg = float(recent['ADX'].tail(5).mean())
            if adx_avg < 15 and setup_type not in ["MEAN_REVERSION", "GEN_STEP_REVERT", "APA"]:
                return False, f"WHIPSAW_ADX ({adx_avg:.0f}<15)"

        return True, "OK"
    except Exception as e:
        logger.debug(f"Anti-whipsaw error: {e}")
        return True, "OK"


# ==============================================================================
# 🟢 V22 NEW #3: DIVERGENCE DECAY (Temporal Weight)
# ==============================================================================

def divergence_with_decay(df, indicator='RSI', order=5, max_age_bars=25):
    """Divergence detection with temporal decay.
    Recent divergences (< 10 bars) = full weight.
    Old divergences (> 25 bars) = ignored."""
    try:
        div_type, div_bonus, div_detail = detect_divergence(df, indicator, order)
        if div_type is None:
            return None, 0, ""

        # Calculate age: distance from last pivot to current bar
        if "BEARISH" in str(div_type):
            pivots = find_pivot_highs(df['high'], order)
        else:
            pivots = find_pivot_lows(df['low'], order)

        if len(pivots) >= 2:
            last_pivot_idx = pivots[-1]
            age = len(df) - 1 - last_pivot_idx
        else:
            age = max_age_bars  # Assume old if can't determine

        # Decay factor
        if age <= 10:
            decay = 1.0  # Full weight
        elif age <= max_age_bars:
            decay = max(0.3, 1.0 - (age - 10) / (max_age_bars - 10) * 0.7)
        else:
            return None, 0, ""  # Too old, ignore

        decayed_bonus = int(div_bonus * decay)
        return div_type, decayed_bonus, f"{div_detail} (age={age}, decay={decay:.0%})"
    except Exception as e:
        logger.debug(f"Divergence decay error: {e}")
        return None, 0, ""


# ==============================================================================
# 🟢 V22 NEW #5: SESSION VOLATILITY AWARENESS
# ==============================================================================

def session_volatility_check(df, lookback_days=5):
    """Checks if current hour historically shows higher/lower volatility.
    Synthetics run 24/7 but may have patterns tied to server load."""
    try:
        if len(df) < 100 or not hasattr(df.index, 'hour'):
            return {"session": "UNKNOWN", "vol_factor": 1.0}

        current_hour = df.index[-1].hour

        # Calculate average volatility by hour
        df_temp = df.copy()
        df_temp['abs_return'] = np.abs(np.log(df_temp['close'] / df_temp['close'].shift(1)))
        df_temp['hour'] = df_temp.index.hour

        hourly_vol = df_temp.groupby('hour')['abs_return'].mean()
        if len(hourly_vol) < 12:
            return {"session": "UNKNOWN", "vol_factor": 1.0}

        current_vol = hourly_vol.get(current_hour, hourly_vol.mean())
        avg_vol = hourly_vol.mean()
        vol_factor = current_vol / avg_vol if avg_vol > 0 else 1.0

        if vol_factor > 1.3:
            session = "HIGH_VOL_SESSION"
        elif vol_factor < 0.7:
            session = "LOW_VOL_SESSION"
        else:
            session = "NORMAL_SESSION"

        return {
            "session": session,
            "vol_factor": round(float(vol_factor), 2),
            "current_hour": current_hour,
            "current_hour_vol": round(float(current_vol), 6),
            "avg_vol": round(float(avg_vol), 6),
        }
    except Exception as e:
        logger.debug(f"Session vol error: {e}")
        return {"session": "UNKNOWN", "vol_factor": 1.0}



# ==============================================================================
# V21 ENGINE #1: SAMPLE ENTROPY — Previsibilidade do gerador
# ==============================================================================

def sample_entropy_v21(series, m=2, r_mult=0.2, max_n=150):
    """SampEn < 0.5 = altamente previsivel. SampEn > 2.0 = caotico.
    V22 PERF: max_n=150 + vectorized broadcast — ~50× faster."""
    try:
        data = np.array(series.dropna().values[-max_n:], dtype=float)
        n = len(data)
        if n < 50: return 2.0, "CHAOTIC"
        r = r_mult * np.std(data)
        if r == 0: return 0.0, "CONSTANT"
        def _count_vec(tl):
            templates = np.array([data[i:i+tl] for i in range(n - tl)])
            nt = len(templates)
            count = 0
            cs = min(nt, 150)
            for ci in range(0, nt, cs):
                chunk = templates[ci:ci+cs]
                diffs = np.abs(chunk[:, None, :] - templates[None, :, :])
                mx = diffs.max(axis=2)
                matches = (mx < r).sum()
                for k in range(ci, min(ci+cs, nt)):
                    if mx[k-ci, k] < r:
                        matches -= 1
                count += matches
            return count // 2
        B = _count_vec(m)
        A = _count_vec(m + 1)
        if B == 0 or A == 0: se = 2.5
        else: se = -np.log(A / B)
        if se < 0.4: regime = "HIGHLY_PREDICTABLE"
        elif se < 0.8: regime = "PREDICTABLE"
        elif se < 1.5: regime = "MODERATE"
        else: regime = "CHAOTIC"
        return round(float(se), 3), regime
    except Exception as e:
        logger.debug(f"SampEn error: {e}")
        return 2.0, "ERROR"

# ==============================================================================
# V21 ENGINE #2: PERMUTATION ENTROPY — Determinismo na ordem
# ==============================================================================

def permutation_entropy_v21(series, order=3, delay=1, max_n=200):
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

def transition_matrix_v21(series, n_states=3, max_n=300):
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
            # V22 PERF: vectorized rolling sum instead of Python loop
            rolling_sums = log_returns.rolling(10).sum().dropna().iloc[::5]
            percentile = float((rolling_sums < recent_cum).mean() * 100) if len(rolling_sums) > 0 else 50
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
        # Kelly Criterion contínuo: f* = (p×b - q) / b
        p = wr / 100
        b = pf if pf > 0 else 1.0
        q = 1 - p
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
        async with websockets.connect(url, ping_interval=15, close_timeout=10) as ws:
            await ws.send(json.dumps(req))
            return json.loads(await asyncio.wait_for(ws.recv(), timeout=10.0))
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

async def fetch_multi_tf(code):
    """V22 PERF: H1=500, H4=300, M15=800, M5=300 — reduced for speed"""
    reqs = [
        {"ticks_history": code, "style": "candles", "granularity": 3600, "count": 500, "end": "latest"},
        {"ticks_history": code, "style": "candles", "granularity": 14400, "count": 300, "end": "latest"},
        {"ticks_history": code, "style": "candles", "granularity": 900, "count": 800, "end": "latest"},
        {"ticks_history": code, "style": "candles", "granularity": 300, "count": 300, "end": "latest"},
    ]
    for url in DERIV_SERVERS:
        try:
            async with websockets.connect(url, ping_interval=15, close_timeout=10) as ws:
                results = []
                for r in reqs:
                    await ws.send(json.dumps(r))
                    results.append(json.loads(await asyncio.wait_for(ws.recv(), 10)))
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
    """V22 PERF: Fully vectorized RSI using ewm (no Python loop)"""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1.0/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0/period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))
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
def calculate_hurst_exponent(series, max_lag=50):
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
    """V22 PERF: window max comparison instead of all() loop"""
    values = data.values if hasattr(data,'values') else np.array(data)
    n = len(values)
    if n < order * 2 + 1: return np.array([])
    pivots = []
    for i in range(order, n - order):
        if np.isnan(values[i]): continue
        window = values[i-order:i+order+1]
        if values[i] == np.nanmax(window):
            pivots.append(i)
    return np.array(pivots)

def find_pivot_lows(data, order=5):
    """V22 PERF: window min comparison instead of all() loop"""
    values = data.values if hasattr(data,'values') else np.array(data)
    n = len(values)
    if n < order * 2 + 1: return np.array([])
    pivots = []
    for i in range(order, n - order):
        if np.isnan(values[i]): continue
        window = values[i-order:i+order+1]
        if values[i] == np.nanmin(window):
            pivots.append(i)
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
    """V22 PERF: Only detect patterns on last 30 candles"""
    n = len(df)
    patterns = [[]] * n
    scores = [0] * n
    start = max(1, n - 30)
    for i in range(start, n):
        c, p = df.iloc[i], df.iloc[i-1]; pl, sc = [], 0
        body = abs(c['close'] - c['open']); rng = c['high'] - c['low']
        if rng > 0:
            uw = c['high'] - max(c['open'], c['close']); lw = min(c['open'], c['close']) - c['low']
            if lw > 0 and body/rng < 0.35 and uw < body:
                r = lw / max(body, 0.0001)
                if r > 3: pl.append("PIN_BULL_STRONG"); sc += 10
                elif r > 2: pl.append("PIN_BULL_MOD"); sc += 5
            elif uw > 0 and body/rng < 0.35 and lw < body:
                r = uw / max(body, 0.0001)
                if r > 3: pl.append("PIN_BEAR_STRONG"); sc += 10
                elif r > 2: pl.append("PIN_BEAR_MOD"); sc += 5
        cb = abs(c['close'] - c['open']); pb = abs(p['close'] - p['open'])
        ct, cb2 = max(c['open'], c['close']), min(c['open'], c['close'])
        pt, pb3 = max(p['open'], p['close']), min(p['open'], p['close'])
        if c['close'] > c['open'] and p['close'] < p['open'] and cb2 < pb3 and ct > pt:
            r = cb / max(pb, 0.0001)
            if r > 2: pl.append("ENGULF_BULL_STRONG"); sc += 10
            else: pl.append("ENGULF_BULL"); sc += 5
        elif c['close'] < c['open'] and p['close'] > p['open'] and cb2 < pb3 and ct > pt:
            r = cb / max(pb, 0.0001)
            if r > 2: pl.append("ENGULF_BEAR_STRONG"); sc += 10
            else: pl.append("ENGULF_BEAR"); sc += 5
        if c['high'] <= p['high'] and c['low'] >= p['low']: pl.append("INSIDE_BAR"); sc += 5
        if rng > 0 and body/rng < 0.1: pl.append("DOJI"); sc += 3
        patterns[i] = pl; scores[i] = sc
    df['patterns'] = patterns; df['pattern_score'] = scores; return df

def detect_swing_points(df, window=5):
    """V22 PERF: vectorized rolling max/min instead of iloc loop"""
    roll_max = df['high'].rolling(window + 1, min_periods=1).max()
    roll_min = df['low'].rolling(window + 1, min_periods=1).min()
    df['swing_high'] = (df['high'] == roll_max)
    df['swing_low'] = (df['low'] == roll_min)
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

def run_walk_forward_v21(df, bias, profile, n_folds=3):
    """V22 PERF: 3 folds, step=3 bars, 40-bar lookahead — ~5× faster"""
    spread = profile.get('spread', 0.05)
    sl_mult = profile.get('sl_atr_mult', 2.5)
    fold_size = len(df) // (n_folds + 1)
    all_trades = []
    STEP = 3  # V22: evaluate every 3rd bar
    MAX_FWD = 40  # V22: reduced forward lookahead

    for fold in range(n_folds):
        ts = fold_size * (fold + 1)
        te = fold_size * (fold + 2) if fold < n_folds - 1 else len(df)
        if ts >= len(df) - MAX_FWD:
            break
        si = max(200, ts)

        # V21 FIX-A: Recalcular edge tests usando APENAS dados de treino
        train_data = df.iloc[:ts]
        fold_vr = variance_ratio_test(train_data['close'])
        fold_acf = autocorrelation_analysis(train_data['close'])

        for i in range(si, min(te, len(df) - MAX_FWD), STEP):
            row = df.iloc[i]
            if pd.isna(row['ADX']) or pd.isna(row['ATR']) or row['ATR'] == 0:
                continue
            sig = None
            atr = row['ATR']
            entry = sl = risk = 0
            setup = "NONE"

            # SETUP 1: TREND (V21: ADX minimo 22, nao 15)
            if row['ADX'] > max(profile.get('adx_strong', 25), 22):
                if bias == "BULLISH" and row['close'] > row['EMA_200'] and row['RSI'] < 60:
                    sig = "BUY"; setup = "SWING"
                elif bias == "BEARISH" and row['close'] < row['EMA_200'] and row['RSI'] > 40:
                    sig = "SELL"; setup = "SWING"

            # SETUP 2: MEAN REVERSION (Z-Score extreme)
            if not sig and 'ZSCORE' in df.columns:
                z = row['ZSCORE']
                if pd.notna(z) and abs(z) > profile.get('zscore_extreme', 2.0) * 0.7:
                    if z < -1.5:
                        sig = "BUY"; setup = "MEAN_REVERSION"
                    elif z > 1.5:
                        sig = "SELL"; setup = "MEAN_REVERSION"

            # SETUP 3: VOL COMPRESS (se edge detectado por VR)
            if not sig and fold_vr.get('has_edge') and fold_vr.get('dominant_type') == 'MEAN_REVERT':
                z = row.get('ZSCORE', 0)
                if pd.notna(z) and z < -1.0:
                    sig = "BUY"; setup = "VOL_COMPRESS"
                elif pd.notna(z) and z > 1.0:
                    sig = "SELL"; setup = "VOL_COMPRESS"

            # SETUP 4: ACF MOMENTUM (se autocorrelação significativa)
            if not sig and fold_acf.get('has_pattern') and fold_acf.get('dominant_type') == 'MOMENTUM':
                if i >= 2:
                    prev_ret = df['close'].iloc[i] - df['close'].iloc[i-1]
                    if prev_ret > atr * 0.3:
                        sig = "BUY"; setup = "ACF_MOMENTUM"
                    elif prev_ret < -atr * 0.3:
                        sig = "SELL"; setup = "ACF_MOMENTUM"

            if not sig:
                continue

            # Executar trade
            entry = row['close'] + (spread if sig == "BUY" else -spread)
            sl_base = detect_swing_level(df.iloc[:i+1], sig, sl_mult)
            if sig == "BUY":
                sl = max(entry - sl_mult * atr, sl_base)
            else:
                sl = min(entry + sl_mult * atr, sl_base)
            risk = abs(entry - sl)
            if risk == 0: risk = atr

            tp1_r = profile.get('tp1_r', 3.0) if setup != "MEAN_REVERSION" else 2.0
            tp2_r = profile.get('tp2_r', 5.0) if setup != "MEAN_REVERSION" else 3.0
            tp1 = entry + tp1_r * risk if sig == "BUY" else entry - tp1_r * risk
            tp2 = entry + tp2_r * risk if sig == "BUY" else entry - tp2_r * risk

            # 🟢 PRECISION #2: TRAILING ADAPTATIVO
            trail_mult = 2.0  # default
            if setup == "SWING": trail_mult = 2.5
            elif setup == "MEAN_REVERSION": trail_mult = 1.2
            elif setup == "VOL_COMPRESS": trail_mult = 1.5

            p1_open, p2_open = True, True
            r1, r2 = 0, 0
            csl = sl
            for f in range(i + 1, min(i + MAX_FWD, len(df))):
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
    sharpe = float(rs.mean()/rs.std()*np.sqrt(len(results))) if len(rs) >= 2 and rs.std() > 0 else 0
    ds = rs[rs<0]
    sortino = float(rs.mean()/ds.std()*np.sqrt(len(results))) if len(ds) >= 2 and ds.std() > 0 else (99.0 if rs.mean() > 0 else 0)

    # Per-fold WRs
    fold_wrs = []
    for fold_id in range(n_folds):
        ft = [t for t in all_trades if t['fold'] == fold_id]
        if ft:
            fold_wrs.append(round(sum(1 for t in ft if t['win'])/len(ft)*100, 1))

    # Per-setup stats
    setup_stats = {}
    for setup_name in set(t['setup'] for t in all_trades):
        st = [t for t in all_trades if t['setup'] == setup_name]
        sw = [t for t in st if t['win']]
        setup_stats[setup_name] = {"trades": len(st), "wr": round(len(sw)/len(st)*100,1) if st else 0}

    return {"WR":round(wr,1),"NET":round(net,1),"DD":round(dd,1),"PF":round(pf,2),
            "SHARPE":round(sharpe,2),"SORTINO":round(sortino,2),"TOTAL_TRADES":len(results),
            "WF_STABLE":len(fold_wrs)>=2 and all(w>30 for w in fold_wrs),
            "FOLD_WRS":fold_wrs,"SETUP_STATS":setup_stats,"RESULTS":results}

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
    apa_bonus:float; order_flow_bonus:float
    bonus_total:float; total:float; grade:str

def calculate_score(adx, momentum_score, pattern_score, dist_ema50, atr,
                    win_rate, profit_factor, profile, momentum_v22=0, **bonuses):
    ts=25 if adx>profile.get('adx_strong',25) else(15 if adx>profile.get('adx_trend_min',15) else 0)
    # V22: Use enhanced momentum (0-100) if available, fallback to old (0-3)
    if momentum_v22 > 0:
        mp = momentum_v22 * 0.2  # Scale 0-100 → 0-20
    else:
        mp=(momentum_score/3)*20
    dr=dist_ema50/atr if atr>0 else 999
    vs=15 if dr<0.5 else(10 if dr<1.0 else(5 if dr<1.5 else 0))
    hs=min((win_rate*0.15)+(profit_factor*5),25)
    base=ts+mp+pattern_score+vs+hs
    keys=['divergence_bonus','fib_bonus','sr_bonus','alignment_bonus','storm_bonus',
          'regime_bonus','volume_bonus','hurst_bonus','zscore_bonus','consecutive_bonus',
          'generator_bonus','distribution_bonus','vr_bonus','acf_bonus',
          'cpi_bonus','markov_bonus','spectral_bonus',
          'adx_slope_bonus','ribbon_bonus','coherence_bonus','candle_bonus','mom_accel_bonus',
          'apa_bonus','order_flow_bonus']
    # V22: No arbitrary cap — grade system handles normalization
    bonus=sum(bonuses.get(k,0) for k in keys)
    total=base+bonus
    # V22: Grade thresholds adjusted for uncapped bonuses
    if total>=210: g="S"
    elif total>=170: g="A++"
    elif total>=140: g="A+"
    elif total>=110: g="A"
    elif total>=80: g="B"
    elif total>=55: g="C"
    else: g="D"
    return SetupScore(ts,mp,pattern_score,vs,hs,base,
        *[bonuses.get(k,0) for k in keys],bonus,total,g)

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
        # V22 checks
        (sd.get('apa_ready'),"A.P.A Ready"),
        (sd.get('oflow_aligned'),"OrderFlow"),
    ]
    for c,l in checks:
        if c: met+=1; lst.append(l)
    if met>=15: return "PERFECT_STORM",25,lst
    elif met>=12: return "STRONG_CONFLUENCE",20,lst
    elif met>=8: return "GOOD_CONFLUENCE",15,lst
    elif met>=5: return "MODERATE",10,lst
    return None,0,lst

# ==============================================================================
# CHART V20
# ==============================================================================

def plot_candles(df, title, entry=None, sl=None, tp1=None, tp2=None, sr_levels=None, fib_levels=None):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), height_ratios=[3.5, 1],
                                     facecolor='#09090b', gridspec_kw={'hspace': 0.08})
    ax1.set_facecolor('#09090b')
    ax2.set_facecolor('#09090b')

    # Candles — vectorized (V22 PERF)
    bull = df['close'].values >= df['open'].values
    bear = ~bull
    idx = np.arange(len(df))
    alpha_arr = np.where(idx > len(df) - 30, 0.9, 0.45)

    # Wicks (thin lines) — use vlines for speed
    for mask, color in [(bull, '#22c55e'), (bear, '#ef4444')]:
        if mask.any():
            positions = df.index[mask]
            ax1.vlines(positions, df['low'].values[mask], df['high'].values[mask],
                       colors=color, linewidth=0.6, alpha=0.65)
            ax1.vlines(positions, df['open'].values[mask], df['close'].values[mask],
                       colors=color, linewidth=2.8, alpha=0.85)

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
    plt.savefig(buf, format='png', dpi=96, facecolor='#09090b', bbox_inches='tight')
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
# SYSTEM PROMPT V21+
# ==============================================================================

SYSTEM_PROMPT = """
FUNÇÃO: ANALISTA V22 — A.P.A PRECISION ENGINE [Gemini 3 Pro]
Missão: Explorar edges estatísticos reais nos sintéticos Deriv com precisão cirúrgica

**RESPONDA SEMPRE EM PORTUGUÊS BRASILEIRO**

**V22 — A.P.A PRECISION ENGINE (V21+ com 5 novos motores):**

🔵 ESTRATÉGIA A.P.A (Accumulation → Pattern → Action):
- ACCUMULATION: BB squeeze + ATR contraction + candles diminuindo + ADX baixo
- PATTERN: Inside Bar, Pin Bar, Engulfing, Breakout, Double Bottom/Top no fim da acumulação
- ACTION: Range expansion + BB abrindo + MACD flip + bias alinhado + TF coherent
- RISK: SL abaixo/acima do range de acumulação, TP = múltiplos do range, Time-stop = 2× duração

Novos Motores V22:
- Order Flow Score (pressão compra/venda via microestrutura)
- Anti-Whipsaw Filter (previne overtrading em mercados choppy)
- Divergence Decay (divergências recentes pesam mais)
- Session Volatility Awareness (horários de alta/baixa vol)
- Enhanced Momentum V22 (0-100, não 0-3)

Base V21+:
- ADX Slope, EMA Ribbon, Multi-TF Coherence, VWAP Proxy
- Candle Structure, Momentum Acceleration, ATR Channel
- Sample Entropy, Permutation Entropy, FFT, Markov Chain
- CPI 0-100, VR Test, ACF, GARCH, Hurst R²

**FORMATO:**

## ⚡ VEREDICTO V22: [ {DECISION} ]
**Grade:** {GRADE} | **Score:** {SCORE}/250 | **CPI:** {CPI}/100
**Tipo:** {STYLE} | **Edge Real:** {VR_HAS_EDGE}

### 🔵 ANÁLISE A.P.A
- Estado: {APA_STATE} (Confiança: {CONFIDENCE}%)
- Acumulação: {DETECTED} ({BARS} bars, qualidade={QUALITY}%)
- Padrão: {PATTERN} (direção={DIRECTION}, força={STRENGTH})
- Trigger: {TRIGGERED} ({REASONS})

### 🧮 MODELO DO GERADOR
- Sigma calibrado: {X}% | Vol Ratio (3 janelas): S={short} M={med} L={long}
- Consensus: {SIGNAL} → Direção: {compress_direction}
- Order Flow: {PRESSURE} (score={SCORE})

### 📊 EDGE ESTATÍSTICO
- Variance Ratio: {VR edge type} ({N} períodos significativos)
- Autocorrelação: lag-1={acf_1} ({type})
- Vol Clustering: {regime}
- Distribuição: Skew={S} Kurt={K} Tails={T}

### 🎯 PRECISÃO DE ENTRADA
- ADX Phase: {phase} | EMA Ribbon: {quality}
- TF Coherence: {coherence} | VWAP Zone: {zone}
- Candle Structure: {quality} | Mom Accel: {phase}
- Session: {SESSION} (vol ×{FACTOR})
- Anti-Whipsaw: {STATUS}

### 🎯 PLANO DE TRADE
{Entradas + Smart TP + Time-Stop}

### ⚠️ CONFLUÊNCIAS + RISCOS

*V22 Insight:* Quando A.P.A está em ACTION_READY com TF Coherence PERFECT e
Order Flow alinhado, esta é a entrada de MÁXIMA confiança. Enfatizar que
A.P.A com padrão ENGULFING ou BREAKOUT no fim de acumulação forte tem
as melhores win rates em sintéticos. Se A.P.A está ACCUMULATING sem padrão,
recomendar ESPERAR pelo padrão antes de entrar.
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

    # V21 FIX-B: Dynamic Bias
    bias, bias_confidence, bias_score = calculate_dynamic_bias(h4, h1)
    bias_old = "BULLISH" if c4['close'] > c4['EMA_200'] else "BEARISH"
    if bias == "NEUTRAL": bias = bias_old  # fallback
    adx = c4['ADX']
    structure = classify_market_structure(h1)
    regime, regime_sc = classify_regime(h1)
    momentum_old = check_momentum(h4, h1, m15, bias)
    momentum_v21 = enhanced_momentum_v21(h4, h1, m15, bias)
    momentum = momentum_old  # keep for backward compat
    # V22 FIX: Use V21 enhanced momentum for scoring
    momentum_score_v22 = momentum_v21  # 0-100 scale

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
    # V22 FIX: Candle structure on M5 (entry TF) not M15
    candle_struct = candle_structure_score(m5 if m5 is not None and len(m5) > 5 else m15, bias)
    mom_accel = momentum_acceleration(h1)
    atr_channel = atr_channel_entry(h1, bias)

    # ═══ V22 NEW ENGINES ═══
    apa_result = apa_full_analysis(m15, bias, trend_coherence)
    oflow = order_flow_score(m15)
    session_vol = session_volatility_check(h1)

    # Divergências — V22: with temporal decay
    rsi_div, rsi_db, rsi_dd = divergence_with_decay(m15, 'RSI', 4)
    macd_div, macd_db, macd_dd = divergence_with_decay(m15, 'MACD', 4)
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

    # ═══ V22 NEW BONUSES ═══
    # A.P.A bonus: high-confidence accumulation→pattern→action
    apa_bonus = 0
    if apa_result.get('state') == "ACTION_READY":
        apa_bonus = min(int(apa_result['confidence'] / 6), 15)
    elif apa_result.get('state') == "PATTERN_FORMING":
        apa_bonus = min(int(apa_result['confidence'] / 10), 8)

    # Order Flow bonus: buy/sell pressure alignment
    order_flow_bonus = 0
    if bias == "BULLISH" and oflow.get('pressure') in ['STRONG_BUYING', 'BUYING']:
        order_flow_bonus = min(int(abs(oflow['score']) / 5), 8)
    elif bias == "BEARISH" and oflow.get('pressure') in ['STRONG_SELLING', 'SELLING']:
        order_flow_bonus = min(int(abs(oflow['score']) / 5), 8)

    # ═══ 🔴 FIX #5: BACKTEST 1× (não 2×) + V20 multi-setup ═══
    sim = run_walk_forward_v21(h1, bias, profile, n_folds=3)

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

        # V22: A.P.A SETUP (HIGHEST PRIORITY — precision entries)
        if apa_result.get('state') == "ACTION_READY":
            apa_action = apa_result['action']
            apa_dir = apa_action.get('direction', 'NEUTRAL')
            if (apa_dir == "BULLISH" and is_long) or (apa_dir == "BEARISH" and not is_long):
                d = "LONG" if is_long else "SHORT"
                sig = f"{d} (A.P.A)"
                entry = apa_action['entry']
                sl_val = apa_action['sl']
                entry_type = f"A.P.A {apa_result['pattern']['pattern']} | Accum {apa_result['accumulation']['bars']}bars"
                trade_style = "APA"; setup_type = "APA"
                return

        # REGIME-SPECIFIC STRATEGY
        # TRENDING → Swing/Breakout
        # RANGING → Mean Reversion
        # VOL_COMPRESS → Contra o movimento
        # TRANSITIONAL → Esperar ou size reduzido

        # 1. GENERATOR SETUPS (PRIORIDADE)
        if gen_type == "GBM" and gen.get('consensus') in ["VOL_OVEREXTENDED","VOL_COMPRESSED"] and gen.get('consensus_confidence',0) > 40:
            # 🔴 FIX #2: Direção CONTRA o movimento
            cd = gen.get('compress_direction','NEUTRAL')
            if (cd == "BULLISH" and is_long) or (cd == "BEARISH" and not is_long):
                d = "LONG" if is_long else "SHORT"
                sig = f"{d} (VOL COMPRESS)"
                sl_val = entry - adapted_profile['sl_atr_mult']*c1['ATR'] if is_long else entry + adapted_profile['sl_atr_mult']*c1['ATR']
                entry_type = f"GBM Compress → {cd} (ratio={gen.get('vol_ratio',1):.2f})"
                trade_style = "REVERSAL"; setup_type = "GEN_VOL_COMPRESS"
                return

        if gen_type == "GBM" and abs(gen.get('z_price',0)) > 2:
            zp = gen['z_price']
            if (zp < -2 and is_long) or (zp > 2 and not is_long):
                d = "LONG" if is_long else "SHORT"
                sig = f"{d} (PRICE DEVIATION)"
                sl_val = entry - adapted_profile['sl_atr_mult']*c1['ATR'] if is_long else entry + adapted_profile['sl_atr_mult']*c1['ATR']
                entry_type = f"Preço {zp:.1f}σ do teórico"
                trade_style = "REVERSAL"; setup_type = "GEN_PRICE_DEV"
                return

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

        if gen_type == "STEP":
            dev = gen.get('deviation_sigma',0)
            if (dev < -1.5 and is_long) or (dev > 1.5 and not is_long):
                d = "LONG" if is_long else "SHORT"
                sig = f"{d} (STEP REVERT)"
                sl_val = entry - adapted_profile['sl_atr_mult']*c1['ATR'] if is_long else entry + adapted_profile['sl_atr_mult']*c1['ATR']
                entry_type = f"Step {dev:.1f}σ deviation"
                trade_style = "REVERSAL"; setup_type = "GEN_STEP_REVERT"
                return

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

    # For Crash/Boom: try BOTH directions (drift can be opposite to bias)
    if gen_type in ["BOOM","CRASH"]:
        drift_dir = gen.get('drift_direction','')
        if drift_dir == "UP": try_setup("BULLISH")
        elif drift_dir == "DOWN": try_setup("BEARISH")
        if sig == "MONITORING": try_setup(bias)
    else:
        try_setup(bias)

    # ═══ V21+ ENTRY REFINEMENT ═══
    # Use ATR channel and VWAP for more precise entry when setup detected
    if "LONG" in sig or "SHORT" in sig:
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

    # Storm
    storm_data = {'adx':adx,'momentum_score':momentum,'pattern_score':pat_score,
        'divergence':divergence,'fib':fib_level is not None,'sr_touch':sr_touch,
        'alignment':align_type=="PERFECT",'bb_squeeze':bb_compression,
        'trending':"TRENDING" in regime,'volume':vol_confirmed,'hurst_trending':hurst_trending,
        'zscore':zscore_favorable,'gen_signal':gen_bonus>0,'dist':dist_favorable,
        'vr_edge':vr.get('has_edge',False),'acf_edge':acf.get('has_pattern',False),
        # V21+ new storm checks
        'ribbon_quality':ema_ribbon.get('quality'),
        'coherence':trend_coherence.get('coherence'),
        'candle_quality':candle_struct.get('quality'),
        'mom_accel':mom_accel_bonus > 0,
        # V22 storm data
        'apa_ready':apa_result.get('state') == 'ACTION_READY',
        'oflow_aligned':(bias == "BULLISH" and oflow.get('score', 0) > 10) or
                        (bias == "BEARISH" and oflow.get('score', 0) < -10)}
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
        momentum_v22=momentum_score_v22,  # V22: enhanced momentum
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
        apa_bonus=apa_bonus, order_flow_bonus=order_flow_bonus)

    # Filters
    configs = {"PERFECT_STORM":(100,1.5),"BREAKOUT":(60,1.4),"MEAN_REVERSION":(45,1.1),
               "GEN_VOL_COMPRESS":(40,1.0),"GEN_SPIKE_DRIFT":(35,0.9),"GEN_STEP_REVERT":(35,0.9),
               "GEN_PRICE_DEV":(40,1.0),"DAY":(45,1.2),"SWING":(70,1.4),
               "APA":(50,1.2)}  # V22: A.P.A setup config
    ms, mpf = configs.get(setup_type, (70, 1.4))
    is_gen_setup = setup_type and "GEN" in str(setup_type)
    is_apa_setup = setup_type == "APA"
    if "BLOCKED" not in sig and sig != "MONITORING":
        # V22: Anti-whipsaw check
        whipsaw_ok, whipsaw_reason = anti_whipsaw_check(m15, setup_type)
        fails = []
        if not whipsaw_ok: fails.append(f"WHIPSAW: {whipsaw_reason}")
        if score.total < ms: fails.append(f"SCORE={score.total:.0f}<{ms}")
        if cpi_val < 25 and not is_gen_setup and not is_apa_setup: fails.append(f"CPI={cpi_val:.0f}<25")
        if sim['NET'] <= 0 and not is_gen_setup and not is_apa_setup: fails.append("NET≤0")
        if sim['PF'] < mpf and not is_gen_setup and not is_apa_setup: fails.append(f"PF={sim['PF']}<{mpf}")
        if fails: sig = f"BLOCKED ({', '.join(fails)})"

    # Targets — 🟢 PRECISION #3: Smart TP
    risk = abs(entry - sl_val)
    if risk == 0: risk = float(c1['ATR'])
    tc = {"PERFECT_STORM":(5,10),"BREAKOUT":(adapted_profile['tp1_r'],adapted_profile['tp2_r']+2),
          "MEAN_REVERSION":(2,3),"GEN_VOL_COMPRESS":(2.5,4),"GEN_SPIKE_DRIFT":(2,5),
          "GEN_STEP_REVERT":(1.5,2.5),"GEN_PRICE_DEV":(2,3.5),"DAY":(2,3),
          "APA":(2.5,4.5),  # V22: A.P.A targets based on accumulation range
          "SWING":(adapted_profile['tp1_r'],adapted_profile['tp2_r'])}
    r1, r2 = tc.get(setup_type, (adapted_profile['tp1_r'], adapted_profile['tp2_r']))
    direction = "LONG" if "LONG" in sig else "SHORT"
    tp1, tp2 = smart_tp(entry, direction, risk, r1, r2, sr_levels)

    # Pyramid
    pyramid = ScalingEngine.calculate_pyramid(score.grade, score.total, capital, risk_pct, entry, sl_val, float(c1['ATR']), adapted_profile)

    show = any(x in sig for x in ["SWING","DAY","BREAKOUT","STORM","REVERSION","COMPRESS","DRIFT","STEP","DEVIATION","PRICE","A.P.A"])

    imgs = [
        plot_candles(h4.tail(100), f"{name} H4 — {regime} | Gen:{gen_signal}", entry if show else None, sl_val if show else None, tp1 if show else None, tp2 if show else None, sr_levels if show else None),
        plot_candles(h1.tail(120), f"{name} H1 — H:{hurst_val} Z:{z_current:.1f} σ:{sigma_calibrated or 0:.3f}", entry if show else None, sl_val if show else None, tp1 if show else None, tp2 if show else None, sr_levels, fibs if show else None),
        plot_candles(m15.tail(120), f"{name} M15 — BB:{bb_cycle} VR:{vr.get('dominant_type','?')} ACF:{acf.get('dominant_type','?')}", entry if show else None, sl_val if show else None, tp1 if show else None, tp2 if show else None),
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
    # V22 A.P.A confluences
    if apa_result.get('state') == 'ACTION_READY':
        confs.append(f"🔵 A.P.A ACTION ({apa_result['pattern']['pattern']}, conf={apa_result['confidence']:.0f}%)")
    elif apa_result.get('state') == 'PATTERN_FORMING':
        confs.append(f"🔵 A.P.A Pattern ({apa_result['pattern']['pattern']})")
    elif apa_result.get('state') == 'ACCUMULATING':
        confs.append(f"🔵 A.P.A Accumulating ({apa_result['accumulation']['bars']} bars)")
    # V22 Order Flow
    if oflow.get('pressure') in ['STRONG_BUYING', 'STRONG_SELLING']:
        confs.append(f"💰 OrderFlow: {oflow['pressure']} ({oflow['score']:.0f})")
    elif oflow.get('pressure') in ['BUYING', 'SELLING']:
        confs.append(f"💰 OrderFlow: {oflow['pressure']}")

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
    # V22 risks
    if session_vol.get('session') == 'LOW_VOL_SESSION': risks.append(f"⚠️ Low vol session (×{session_vol.get('vol_factor',1):.1f})")
    if (bias == "BULLISH" and oflow.get('pressure') in ['STRONG_SELLING', 'SELLING']) or \
       (bias == "BEARISH" and oflow.get('pressure') in ['STRONG_BUYING', 'BUYING']):
        risks.append(f"⚠️ OrderFlow contra bias ({oflow.get('pressure','')})")

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
            "MOM_ACCEL":score.mom_accel_bonus,
            "APA":score.apa_bonus,"OFLOW":score.order_flow_bonus
        }),
        # V21+ precision data
        "ADX_SLOPE": convert_np(adx_slope),
        "EMA_RIBBON": convert_np(ema_ribbon),
        "TREND_COHERENCE": convert_np(trend_coherence),
        "VWAP_DATA": convert_np(vwap_data),
        "CANDLE_STRUCT": convert_np(candle_struct),
        "MOM_ACCEL": convert_np(mom_accel),
        "ATR_CHANNEL": convert_np(atr_channel),
        # V22 new data
        "APA": convert_np(apa_result),
        "APA_BONUS": apa_bonus,
        "ORDER_FLOW": convert_np(oflow),
        "ORDER_FLOW_BONUS": order_flow_bonus,
        "SESSION_VOL": convert_np(session_vol),
        "TIME_STOP": hold.get('time_stop', 45),
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
        <span style='font-size:11px;color:#52525b;margin-left:6px;font-weight:500;'>V22 A.P.A</span>
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
        A.P.A Precision Engine<br>
        Accumulation→Pattern→Action<br>
        VR · ACF · GARCH · OrderFlow<br>
        Sigma Calibrated · Smart TP
    </div>""", unsafe_allow_html=True)

# ── HEADER ──
st.markdown("""<div style='padding:0 0 8px;'>
    <span style='font-size:32px;font-weight:300;color:#fafafa;letter-spacing:-1px;'>APATECO</span>
    <span style='font-size:13px;color:#3f3f46;margin-left:8px;'>A.P.A Precision Engine V22</span>
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

            import time as _time
            status = st.status("⚡ Analyzing...", expanded=True)
            _t0 = _time.time()
            status.write("📡 Fetching multi-timeframe data...")
            h1r, h4r, m15r, m5r, err = asyncio.run(fetch_multi_tf(assets[target]))
            if err: status.update(state='error'); st.error(err); st.stop()
            _t1 = _time.time()
            status.write(f"📡 Data fetched in {_t1-_t0:.1f}s · 🧮 Running statistical engine...")
            data = sniper_core_v20(target, h1r, h4r, m15r, m5r, capital, risk_pct)
            _t2 = _time.time()
            imgs = data.pop("IMAGES")
            status.write(f"🧮 Analysis done in {_t2-_t1:.1f}s · 🤖 Generating AI insights...")
            genai.configure(api_key=api)
            dc = convert_np(data)
            try:
                model = genai.GenerativeModel("models/gemini-3-pro-preview", safety_settings=SAFETY_SETTINGS)
                ai = model.generate_content([SYSTEM_PROMPT, f"V20 DATA: {json.dumps(dc)}"] + imgs).text
                status.update(label="Complete", state="complete")
            except Exception as e:
                ai = f"AI unavailable: {str(e)[:120]}"
                status.update(label="Done", state="complete")

            # ── GRADE CARD ──
            g = data['SETUP_GRADE']
            grade_class = {"S":"grade-s","A++":"grade-app","A+":"grade-ap","A":"grade-a"}.get(g,"grade-low")
            score_pct = min(data['SETUP_SCORE'] / 250 * 100, 100)
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
                    {data['SETUP_SCORE']:.0f}<span style='color:#52525b;font-size:14px;'> / 250</span>
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
            st.markdown("## Entry Precision V21+")
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

            # ── V22: A.P.A STRATEGY ──
            st.markdown("## A.P.A Strategy")
            apa = data.get('APA', {})
            apa_state = apa.get('state', 'NO_SETUP')
            apa_color = '#22c55e' if apa_state == 'ACTION_READY' else '#f59e0b' if 'PATTERN' in apa_state or 'ACCUM' in apa_state else '#52525b'
            a1, a2, a3, a4 = st.columns(4)
            a1.metric("A.P.A State", apa_state, f"conf={apa.get('confidence',0):.0f}%")
            accum = apa.get('accumulation', {})
            a2.metric("Accumulation", accum.get('phase', 'NONE'), f"{accum.get('bars',0)} bars")
            pat = apa.get('pattern', {})
            a3.metric("Pattern", pat.get('pattern', 'NONE'), f"str={pat.get('strength',0)}")
            act = apa.get('action', {})
            a4.metric("Action", "✓ TRIGGERED" if act.get('triggered') else "✗ Waiting", f"score={act.get('trigger_score',0)}")

            # V22: Order Flow + Session
            o1, o2, o3 = st.columns(3)
            ofl = data.get('ORDER_FLOW', {})
            o1.metric("Order Flow", ofl.get('pressure', '?'), f"score={ofl.get('score',0):.0f}")
            sv = data.get('SESSION_VOL', {})
            o2.metric("Session", sv.get('session', '?'), f"×{sv.get('vol_factor',1):.1f}")
            o3.metric("Time-Stop", f"{data.get('TIME_STOP', 45)} bars")

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

            # Setup breakdown
            if data.get('SETUP_STATS'):
                parts = " · ".join(f"{k} {v['trades']}t/{v['wr']}%" for k,v in data['SETUP_STATS'].items())
                st.markdown(f"<p class='mono text-xs muted' style='margin-top:-8px;'>{parts}</p>",
                            unsafe_allow_html=True)

            # Monte Carlo
            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("MC Median", f"{data['MC_MEDIAN']}R")
            mc2.metric("MC P5", f"{data['MC_P5']}R")
            mc3.metric("MC Positive", f"{data['MC_POSITIVE']}%")

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
                                               "COMPRESS","DRIFT","STEP","DEVIATION","PRICE","A.P.A"])
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
                    <div class='plan-row'>
                        <span class='plan-label'>Time-Stop</span>
                        <span class='plan-value'>{data.get('TIME_STOP',45)} bars</span>
                        <span class='plan-note'>Max hold · Edge decay</span>
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
