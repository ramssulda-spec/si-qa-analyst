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
# 🟢 PRECISION #3: Dynamic ATR-based TP
# 🟢 PRECISION #4: Scanner para TODOS gen types
# 🟢 PRECISION #5: Adaptive Kelly Criterion (não if/elif)
# 🟢 PRECISION #6: M5 entry timing
# ==============================================================================

st.set_page_config(
    page_title="APATECO V25",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=JetBrains+Mono:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

    /* ═══════════════════════════════════════════
       KEYFRAME ANIMATIONS
       ═══════════════════════════════════════════ */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(24px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    @keyframes slideInLeft {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    @keyframes slideInRight {
        from { opacity: 0; transform: translateX(20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    @keyframes fillBar {
        from { width: 0%; }
    }
    @keyframes gradientRotate {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    @keyframes pulseGlow {
        0%, 100% { box-shadow: 0 0 12px rgba(99,102,241,0.15); }
        50% { box-shadow: 0 0 36px rgba(99,102,241,0.35); }
    }
    @keyframes livePulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.35; transform: scale(0.8); }
    }
    @keyframes popIn {
        0% { opacity: 0; transform: scale(0.75); }
        60% { transform: scale(1.06); }
        100% { opacity: 1; transform: scale(1); }
    }
    @keyframes shimmer {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }
    @keyframes borderGlow {
        0%, 100% { border-color: rgba(99,102,241,0.15); }
        50% { border-color: rgba(99,102,241,0.45); }
    }
    @keyframes scanSlide {
        from { opacity: 0; transform: translateX(-16px); }
        to { opacity: 1; transform: translateX(0); }
    }
    @keyframes textReveal {
        from { opacity: 0; letter-spacing: 8px; filter: blur(4px); }
        to { opacity: 1; letter-spacing: -1.5px; filter: blur(0); }
    }
    @keyframes gradientBorder {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    @keyframes breathe {
        0%, 100% { opacity: 0.04; }
        50% { opacity: 0.08; }
    }
    @keyframes orbFloat {
        0%, 100% { transform: translate(0, 0) scale(1); }
        25% { transform: translate(30px, -20px) scale(1.1); }
        50% { transform: translate(-10px, 15px) scale(0.95); }
        75% { transform: translate(20px, 10px) scale(1.05); }
    }
    @keyframes countUp {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes lineExpand {
        from { width: 0; opacity: 0; }
        to { width: 100%; opacity: 1; }
    }
    @keyframes cardEnter {
        from { opacity: 0; transform: translateY(16px) scale(0.98); }
        to { opacity: 1; transform: translateY(0) scale(1); }
    }
    @keyframes ringPulse {
        0% { box-shadow: 0 0 0 0 rgba(99,102,241,0.4); }
        70% { box-shadow: 0 0 0 12px rgba(99,102,241,0); }
        100% { box-shadow: 0 0 0 0 rgba(99,102,241,0); }
    }

    /* ═══════════════════════════════════════════
       BASE THEME — Obsidian Command Center
       ═══════════════════════════════════════════ */
    :root {
        --bg-void: #050508;
        --bg-base: #08080e;
        --bg-surface: #0d0d16;
        --bg-elevated: #12121e;
        --bg-card: #0f0f1a;
        --bg-hover: #181830;
        --border: #1c1c35;
        --border-subtle: #141428;
        --border-hover: #2d2d55;
        --border-accent: rgba(99,102,241,0.25);
        --text-primary: #f0f0f5;
        --text-secondary: #9090a8;
        --text-muted: #555570;
        --text-dim: #3a3a50;
        --accent: #6366f1;
        --accent-light: #818cf8;
        --accent-dim: #4f46e5;
        --accent-glow: rgba(99,102,241,0.10);
        --accent-glow-strong: rgba(99,102,241,0.20);
        --success: #10b981;
        --success-soft: rgba(16,185,129,0.08);
        --danger: #ef4444;
        --danger-soft: rgba(239,68,68,0.08);
        --warning: #f59e0b;
        --warning-soft: rgba(245,158,11,0.08);
        --info: #3b82f6;
        --purple: #a855f7;
        --purple-soft: rgba(168,85,247,0.08);
        --cyan: #06b6d4;
        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 16px;
        --radius-xl: 20px;
        --shadow-sm: 0 2px 8px rgba(0,0,0,0.3);
        --shadow-md: 0 4px 24px rgba(0,0,0,0.4);
        --shadow-lg: 0 8px 48px rgba(0,0,0,0.5);
        --shadow-glow: 0 0 32px rgba(99,102,241,0.12);
    }

    .stApp {
        background: var(--bg-void);
        color: var(--text-secondary);
        font-family: 'DM Sans', -apple-system, sans-serif;
    }

    /* Subtle animated dot grid */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background-image: radial-gradient(circle, rgba(99,102,241,0.025) 1px, transparent 1px);
        background-size: 28px 28px;
        pointer-events: none;
        z-index: 0;
        animation: breathe 8s ease-in-out infinite;
    }

    /* Ambient orb glow — top left */
    .stApp::after {
        content: '';
        position: fixed;
        top: -20%; left: -15%;
        width: 600px; height: 600px;
        background: radial-gradient(ellipse, rgba(99,102,241,0.04) 0%, rgba(168,85,247,0.02) 40%, transparent 70%);
        pointer-events: none;
        z-index: 0;
        animation: orbFloat 20s ease-in-out infinite;
    }

    /* ── SIDEBAR ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--bg-base) 0%, var(--bg-void) 100%);
        border-right: 1px solid var(--border-subtle);
    }
    section[data-testid="stSidebar"]::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 160px;
        background: linear-gradient(180deg, rgba(99,102,241,0.05) 0%, transparent 100%);
        pointer-events: none;
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown span {
        color: var(--text-muted);
        font-size: 13px;
    }

    /* ═══════════════════════════════════════════
       TYPOGRAPHY — Refined
       ═══════════════════════════════════════════ */
    h1 {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 300 !important;
        color: var(--text-primary) !important;
        letter-spacing: -0.5px !important;
        font-size: 28px !important;
        text-shadow: none !important;
        border: none !important;
    }
    h2 {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important;
        color: var(--text-primary) !important;
        font-size: 13px !important;
        letter-spacing: 1.8px !important;
        text-transform: uppercase !important;
        text-shadow: none !important;
        border: none !important;
        margin-top: 36px !important;
        padding-bottom: 12px !important;
        position: relative;
        animation: slideInLeft 0.5s ease-out;
    }
    h2::after {
        content: '';
        position: absolute;
        bottom: 0; left: 0;
        width: 40px; height: 2px;
        background: linear-gradient(90deg, var(--accent), var(--purple), transparent);
        border-radius: 2px;
        animation: lineExpand 0.8s ease-out;
    }
    h3 {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 500 !important;
        color: var(--text-secondary) !important;
        font-size: 12px !important;
        letter-spacing: 1px !important;
        text-transform: uppercase !important;
        text-shadow: none !important;
        border: none !important;
    }
    p, li, span { font-family: 'DM Sans', sans-serif; }

    /* ═══════════════════════════════════════════
       METRIC CARDS — Elevated Glass
       ═══════════════════════════════════════════ */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, var(--bg-surface) 0%, var(--bg-card) 100%);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        padding: 16px 18px;
        transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
        animation: cardEnter 0.5s ease-out backwards;
        position: relative;
        overflow: hidden;
    }
    div[data-testid="stMetric"]::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent 10%, rgba(99,102,241,0.15) 50%, transparent 90%);
    }
    div[data-testid="stMetric"]:hover {
        border-color: var(--border-accent);
        background: linear-gradient(135deg, var(--bg-elevated) 0%, var(--bg-surface) 100%);
        transform: translateY(-3px);
        box-shadow: var(--shadow-md), var(--shadow-glow);
    }
    div[data-testid="stMetric"] label {
        color: var(--text-muted) !important;
        font-size: 10px !important;
        letter-spacing: 1.2px;
        text-transform: uppercase;
        font-weight: 600 !important;
        font-family: 'Outfit', sans-serif !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: var(--text-primary) !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 17px !important;
        font-weight: 600 !important;
        animation: countUp 0.6s ease-out;
    }
    div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 10.5px !important;
    }

    /* Stagger metric animations */
    div[data-testid="column"]:nth-child(1) div[data-testid="stMetric"] { animation-delay: 0.05s; }
    div[data-testid="column"]:nth-child(2) div[data-testid="stMetric"] { animation-delay: 0.10s; }
    div[data-testid="column"]:nth-child(3) div[data-testid="stMetric"] { animation-delay: 0.15s; }
    div[data-testid="column"]:nth-child(4) div[data-testid="stMetric"] { animation-delay: 0.20s; }
    div[data-testid="column"]:nth-child(5) div[data-testid="stMetric"] { animation-delay: 0.25s; }
    div[data-testid="column"]:nth-child(6) div[data-testid="stMetric"] { animation-delay: 0.30s; }

    /* ═══════════════════════════════════════════
       BUTTONS — Luminous Accent
       ═══════════════════════════════════════════ */
    .stButton > button {
        background: linear-gradient(135deg, var(--accent) 0%, #7c3aed 50%, var(--accent-dim) 100%);
        background-size: 200% 200%;
        color: #ffffff;
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
        font-size: 12.5px;
        letter-spacing: 1.2px;
        padding: 13px 28px;
        border-radius: var(--radius-md);
        border: none;
        width: 100%;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        text-transform: uppercase;
        position: relative;
        overflow: hidden;
        box-shadow: 0 2px 12px rgba(99,102,241,0.2);
    }
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0; left: -100%; width: 100%; height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.12), transparent);
        transition: left 0.6s ease;
    }
    .stButton > button:hover {
        background-position: 100% 50%;
        box-shadow: 0 6px 32px rgba(99,102,241,0.35), 0 0 0 1px rgba(99,102,241,0.3);
        transform: translateY(-2px);
    }
    .stButton > button:hover::before { left: 100%; }
    .stButton > button:active {
        transform: translateY(0);
        box-shadow: 0 2px 8px rgba(99,102,241,0.2);
    }

    /* ═══════════════════════════════════════════
       CARDS — Layered Depth System
       ═══════════════════════════════════════════ */
    .card {
        background: linear-gradient(145deg, var(--bg-surface) 0%, var(--bg-card) 100%);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 24px;
        margin: 8px 0;
        animation: cardEnter 0.5s ease-out;
        position: relative;
    }
    .card::before {
        content: '';
        position: absolute;
        top: 0; left: 20px; right: 20px;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(99,102,241,0.12), transparent);
    }
    .card-accent {
        background: linear-gradient(145deg, var(--bg-surface) 0%, var(--bg-elevated) 100%);
        border: 1px solid var(--border-hover);
        border-radius: var(--radius-xl);
        padding: 28px;
        margin: 16px 0;
        box-shadow: var(--shadow-md);
        animation: cardEnter 0.6s ease-out;
        position: relative;
    }
    .card-accent::before {
        content: '';
        position: absolute;
        top: -1px; left: 30px; right: 30px;
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--accent), var(--purple), transparent);
        border-radius: 2px;
        opacity: 0.5;
    }
    .card-glow {
        background: var(--bg-surface);
        border: 1px solid var(--border);
        border-radius: var(--radius-xl);
        padding: 28px;
        margin: 12px 0;
        position: relative;
        overflow: hidden;
        animation: cardEnter 0.5s ease-out;
    }
    .card-glow::before {
        content: '';
        position: absolute;
        top: -1px; left: -1px; right: -1px; bottom: -1px;
        border-radius: calc(var(--radius-xl) + 1px);
        background: linear-gradient(135deg, var(--accent), var(--accent-dim), #a855f7, var(--cyan), var(--accent));
        background-size: 400% 400%;
        animation: gradientBorder 6s ease infinite;
        z-index: -1;
        opacity: 0.45;
    }
    .card-glow::after {
        content: '';
        position: absolute;
        top: 1px; left: 1px; right: 1px; bottom: 1px;
        border-radius: calc(var(--radius-xl) - 1px);
        background: var(--bg-surface);
        z-index: -1;
    }

    /* Section Wrapper Card — groups related metrics */
    .section-wrap {
        background: linear-gradient(180deg, rgba(12,12,22,0.6) 0%, rgba(8,8,14,0.4) 100%);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        padding: 20px 16px 12px;
        margin: 12px 0 20px;
        position: relative;
        animation: cardEnter 0.5s ease-out;
    }
    .section-wrap::before {
        content: '';
        position: absolute;
        top: 0; left: 24px; right: 24px;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--border), transparent);
    }
    .section-wrap-accent {
        background: linear-gradient(180deg, rgba(99,102,241,0.03) 0%, rgba(8,8,14,0.4) 100%);
        border: 1px solid rgba(99,102,241,0.12);
        border-radius: var(--radius-lg);
        padding: 20px 16px 12px;
        margin: 12px 0 20px;
        position: relative;
        animation: cardEnter 0.6s ease-out;
    }
    .section-wrap-accent::before {
        content: '';
        position: absolute;
        top: -1px; left: 20px; right: 20px;
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--accent), transparent);
        border-radius: 2px;
        opacity: 0.4;
    }
    /* M5 Scalp section — extra highlight */
    .section-wrap-m5 {
        background: linear-gradient(180deg, rgba(99,102,241,0.05) 0%, rgba(168,85,247,0.02) 50%, rgba(8,8,14,0.4) 100%);
        border: 1px solid rgba(99,102,241,0.18);
        border-radius: var(--radius-lg);
        padding: 20px 16px 12px;
        margin: 12px 0 20px;
        position: relative;
        animation: cardEnter 0.6s ease-out;
        box-shadow: 0 4px 24px rgba(99,102,241,0.06);
    }
    .section-wrap-m5::before {
        content: '';
        position: absolute;
        top: -1px; left: 16px; right: 16px;
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--accent), var(--purple), transparent);
        border-radius: 2px;
        opacity: 0.5;
    }
    /* BC Engine section */
    .section-wrap-bc {
        background: linear-gradient(180deg, rgba(239,68,68,0.02) 0%, rgba(8,8,14,0.4) 100%);
        border: 1px solid rgba(239,68,68,0.08);
        border-radius: var(--radius-lg);
        padding: 20px 16px 12px;
        margin: 12px 0 20px;
        position: relative;
        animation: cardEnter 0.5s ease-out;
    }

    /* ═══════════════════════════════════════════
       GRADE BADGES — Animated Premium
       ═══════════════════════════════════════════ */
    .grade-s {
        background: linear-gradient(135deg, rgba(124,58,237,0.06) 0%, rgba(168,85,247,0.03) 100%);
        border: 1px solid rgba(124,58,237,0.2);
        color: #c4b5fd;
        border-radius: var(--radius-xl); padding: 32px; text-align: center;
        animation: pulseGlow 3s ease infinite, cardEnter 0.6s ease-out;
        position: relative; overflow: hidden;
    }
    .grade-s::before {
        content: '';
        position: absolute; top: 0; left: 0; right: 0; bottom: 0;
        background: radial-gradient(ellipse at 50% 0%, rgba(139,92,246,0.1) 0%, transparent 60%);
        pointer-events: none;
    }
    .grade-s .grade-letter { font-size: 64px; font-weight: 800; color: #a78bfa;
        font-family: 'Outfit', sans-serif; text-shadow: 0 0 60px rgba(167,139,250,0.35);
        animation: textReveal 0.8s ease-out; }

    .grade-app {
        background: linear-gradient(135deg, rgba(5,150,105,0.06) 0%, rgba(16,185,129,0.03) 100%);
        border: 1px solid rgba(16,185,129,0.2);
        color: #6ee7b7;
        border-radius: var(--radius-xl); padding: 32px; text-align: center;
        animation: cardEnter 0.6s ease-out;
        position: relative; overflow: hidden;
    }
    .grade-app::before {
        content: '';
        position: absolute; top: 0; left: 0; right: 0; bottom: 0;
        background: radial-gradient(ellipse at 50% 0%, rgba(16,185,129,0.08) 0%, transparent 60%);
        pointer-events: none;
    }
    .grade-app .grade-letter { font-size: 64px; font-weight: 800; color: #34d399;
        font-family: 'Outfit', sans-serif; text-shadow: 0 0 50px rgba(52,211,153,0.25);
        animation: textReveal 0.8s ease-out; }

    .grade-ap {
        background: linear-gradient(135deg, rgba(37,99,235,0.06) 0%, rgba(59,130,246,0.03) 100%);
        border: 1px solid rgba(59,130,246,0.2);
        color: #93c5fd;
        border-radius: var(--radius-xl); padding: 32px; text-align: center;
        animation: cardEnter 0.6s ease-out;
        position: relative; overflow: hidden;
    }
    .grade-ap::before {
        content: '';
        position: absolute; top: 0; left: 0; right: 0; bottom: 0;
        background: radial-gradient(ellipse at 50% 0%, rgba(59,130,246,0.08) 0%, transparent 60%);
        pointer-events: none;
    }
    .grade-ap .grade-letter { font-size: 64px; font-weight: 800; color: #60a5fa;
        font-family: 'Outfit', sans-serif; text-shadow: 0 0 50px rgba(96,165,250,0.25);
        animation: textReveal 0.8s ease-out; }

    .grade-a {
        background: linear-gradient(135deg, rgba(6,182,212,0.06) 0%, rgba(34,211,238,0.03) 100%);
        border: 1px solid rgba(34,211,238,0.15);
        color: #a5f3fc;
        border-radius: var(--radius-xl); padding: 32px; text-align: center;
        animation: cardEnter 0.6s ease-out;
        position: relative; overflow: hidden;
    }
    .grade-a::before {
        content: '';
        position: absolute; top: 0; left: 0; right: 0; bottom: 0;
        background: radial-gradient(ellipse at 50% 0%, rgba(34,211,238,0.06) 0%, transparent 60%);
        pointer-events: none;
    }
    .grade-a .grade-letter { font-size: 64px; font-weight: 800; color: #67e8f9;
        font-family: 'Outfit', sans-serif; animation: textReveal 0.8s ease-out; }

    .grade-low {
        background: var(--bg-surface);
        border: 1px solid var(--border);
        color: var(--text-muted);
        border-radius: var(--radius-xl); padding: 32px; text-align: center;
        animation: cardEnter 0.6s ease-out;
    }
    .grade-low .grade-letter { font-size: 64px; font-weight: 800; color: var(--text-muted);
        font-family: 'Outfit', sans-serif; }

    /* ═══════════════════════════════════════════
       SCORE BAR — Animated Fill with Glow
       ═══════════════════════════════════════════ */
    .score-bar-outer {
        background: rgba(255,255,255,0.03);
        border-radius: 10px;
        height: 6px;
        margin: 12px 0 8px;
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.03);
    }
    .score-bar-inner {
        height: 100%;
        border-radius: 10px;
        transition: width 1.8s cubic-bezier(0.4, 0, 0.2, 1);
        animation: fillBar 1.8s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        box-shadow: 0 0 12px rgba(99,102,241,0.3);
    }
    .score-bar-inner::after {
        content: '';
        position: absolute;
        top: 0; right: 0;
        width: 32px; height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.35));
        border-radius: 10px;
    }

    /* ═══════════════════════════════════════════
       SIGNAL TAGS — Premium Badges
       ═══════════════════════════════════════════ */
    .tag-long {
        display: inline-flex; align-items: center; gap: 5px;
        background: linear-gradient(135deg, rgba(16,185,129,0.12), rgba(16,185,129,0.04));
        color: #34d399;
        border: 1px solid rgba(16,185,129,0.3);
        padding: 7px 18px;
        border-radius: 10px;
        font-size: 12px;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: 1.5px;
        animation: popIn 0.4s ease-out;
        box-shadow: 0 0 16px rgba(16,185,129,0.12);
    }
    .tag-short {
        display: inline-flex; align-items: center; gap: 5px;
        background: linear-gradient(135deg, rgba(239,68,68,0.12), rgba(239,68,68,0.04));
        color: #f87171;
        border: 1px solid rgba(239,68,68,0.3);
        padding: 7px 18px;
        border-radius: 10px;
        font-size: 12px;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: 1.5px;
        animation: popIn 0.4s ease-out;
        box-shadow: 0 0 16px rgba(239,68,68,0.12);
    }
    .tag-blocked {
        display: inline-flex; align-items: center; gap: 5px;
        background: rgba(255,255,255,0.02);
        color: var(--text-muted);
        border: 1px solid var(--border);
        padding: 7px 18px;
        border-radius: 10px;
        font-size: 12px;
        font-weight: 500;
        letter-spacing: 0.8px;
    }
    .tag-monitoring {
        display: inline-flex; align-items: center; gap: 5px;
        background: linear-gradient(135deg, rgba(245,158,11,0.1), rgba(245,158,11,0.03));
        color: #fbbf24;
        border: 1px solid rgba(245,158,11,0.25);
        padding: 7px 18px;
        border-radius: 10px;
        font-size: 12px;
        font-weight: 500;
        letter-spacing: 0.8px;
    }
    .tag-scalp {
        display: inline-flex; align-items: center; gap: 4px;
        background: linear-gradient(135deg, rgba(99,102,241,0.14), rgba(168,85,247,0.06));
        color: var(--accent-light);
        border: 1px solid rgba(99,102,241,0.3);
        padding: 4px 12px;
        border-radius: 8px;
        font-size: 10px;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: 1px;
        margin-left: 6px;
        animation: popIn 0.5s ease-out 0.2s backwards;
    }

    /* ═══════════════════════════════════════════
       CONFLUENCE PILLS — Animated
       ═══════════════════════════════════════════ */
    .pill {
        display: inline-flex;
        align-items: center;
        background: var(--bg-elevated);
        border: 1px solid var(--border);
        color: var(--text-secondary);
        padding: 8px 16px;
        border-radius: 24px;
        font-size: 11.5px;
        margin: 4px 4px;
        font-weight: 400;
        transition: all 0.3s ease;
        animation: popIn 0.4s ease-out backwards;
    }
    .pill:nth-child(1) { animation-delay: 0.05s; }
    .pill:nth-child(2) { animation-delay: 0.10s; }
    .pill:nth-child(3) { animation-delay: 0.12s; }
    .pill:nth-child(4) { animation-delay: 0.15s; }
    .pill:nth-child(5) { animation-delay: 0.18s; }
    .pill:nth-child(6) { animation-delay: 0.21s; }
    .pill:nth-child(7) { animation-delay: 0.24s; }
    .pill:nth-child(8) { animation-delay: 0.27s; }
    .pill:nth-child(9) { animation-delay: 0.30s; }
    .pill:nth-child(10) { animation-delay: 0.33s; }
    .pill-green { border-color: rgba(16,185,129,0.2); color: #6ee7b7; background: rgba(16,185,129,0.05); }
    .pill-green:hover { border-color: rgba(16,185,129,0.45); background: rgba(16,185,129,0.1); transform: translateY(-1px); }
    .pill-red { border-color: rgba(239,68,68,0.2); color: #fca5a5; background: rgba(239,68,68,0.05); }
    .pill-red:hover { border-color: rgba(239,68,68,0.45); background: rgba(239,68,68,0.1); transform: translateY(-1px); }
    .pill-purple { border-color: rgba(124,58,237,0.2); color: #c4b5fd; background: rgba(124,58,237,0.05); }
    .pill-blue { border-color: rgba(59,130,246,0.2); color: #93c5fd; background: rgba(59,130,246,0.05); }

    /* ═══════════════════════════════════════════
       SCANNER ROWS — Animated Slide
       ═══════════════════════════════════════════ */
    .scan-row {
        background: linear-gradient(135deg, var(--bg-surface), var(--bg-card));
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        padding: 16px 20px;
        margin: 6px 0;
        display: flex;
        align-items: center;
        justify-content: space-between;
        transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
        animation: scanSlide 0.5s ease-out backwards;
    }
    .scan-row:hover {
        border-color: var(--accent);
        background: linear-gradient(135deg, var(--bg-elevated), var(--bg-surface));
        transform: translateX(6px);
        box-shadow: var(--shadow-md), -3px 0 0 var(--accent);
    }
    .scan-rank {
        color: var(--text-dim);
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        width: 28px;
        font-weight: 600;
    }
    .scan-name {
        color: var(--text-primary);
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
        font-size: 14px;
        flex: 1;
        margin-left: 8px;
    }
    .scan-score {
        font-family: 'JetBrains Mono', monospace;
        font-size: 22px;
        font-weight: 700;
        margin: 0 16px;
    }
    .scan-meta {
        color: var(--text-muted);
        font-size: 10.5px;
        font-family: 'JetBrains Mono', monospace;
    }

    /* ═══════════════════════════════════════════
       TRADE PLAN TABLE — Enhanced
       ═══════════════════════════════════════════ */
    .plan-row {
        display: flex;
        align-items: center;
        padding: 14px 20px;
        border-bottom: 1px solid var(--border-subtle);
        transition: background 0.25s ease;
    }
    .plan-row:last-child { border-bottom: none; }
    .plan-row:hover { background: rgba(99,102,241,0.02); }
    .plan-label {
        color: var(--text-muted);
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        width: 72px;
        font-weight: 600;
        font-family: 'Outfit', sans-serif;
    }
    .plan-value {
        color: var(--text-primary);
        font-family: 'JetBrains Mono', monospace;
        font-size: 15px;
        font-weight: 600;
        flex: 1;
    }
    .plan-note {
        color: var(--text-muted);
        font-size: 11px;
    }

    /* ═══════════════════════════════════════════
       SECTION HEADER — Enhanced
       ═══════════════════════════════════════════ */
    .section-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 8px 0 14px;
        animation: slideInLeft 0.5s ease-out;
    }
    .section-icon {
        width: 30px; height: 30px;
        border-radius: 8px;
        display: flex; align-items: center; justify-content: center;
        font-size: 13px;
        background: var(--accent-glow);
        border: 1px solid rgba(99,102,241,0.12);
    }
    .section-title {
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
        font-size: 12px;
        color: var(--text-secondary);
        letter-spacing: 1.5px;
        text-transform: uppercase;
    }
    .section-line {
        flex: 1;
        height: 1px;
        background: linear-gradient(90deg, var(--border), transparent);
    }

    /* ═══════════════════════════════════════════
       DIVIDER — Gradient
       ═══════════════════════════════════════════ */
    .divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--border), transparent);
        margin: 28px 0;
        border: none;
    }

    /* ═══════════════════════════════════════════
       UTILITY CLASSES
       ═══════════════════════════════════════════ */
    .mono { font-family: 'JetBrains Mono', monospace; }
    .muted { color: var(--text-muted); }
    .text-sm { font-size: 12px; }
    .text-xs { font-size: 11px; }

    /* ═══════════════════════════════════════════
       HEADER BAR — Animated Logo
       ═══════════════════════════════════════════ */
    .header-bar {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 8px 0 20px;
        animation: fadeIn 1s ease-out;
    }
    .header-logo {
        font-family: 'Outfit', sans-serif;
        font-size: 36px;
        font-weight: 800;
        letter-spacing: -2px;
        background: linear-gradient(135deg, var(--text-primary) 0%, var(--accent-light) 60%, var(--purple) 100%);
        background-size: 200% 200%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: textReveal 1s ease-out, gradientRotate 6s ease infinite;
    }
    .header-diamond {
        width: 38px; height: 38px;
        border-radius: 10px;
        background: linear-gradient(135deg, var(--accent), var(--accent-dim));
        display: flex; align-items: center; justify-content: center;
        font-size: 16px; color: #fff; font-weight: 800;
        box-shadow: 0 4px 20px rgba(99,102,241,0.3);
        animation: ringPulse 3s ease-in-out infinite, fadeIn 0.5s ease-out;
    }
    .header-version {
        font-family: 'JetBrains Mono', monospace;
        font-size: 10px;
        color: var(--accent-light);
        background: rgba(99,102,241,0.08);
        padding: 4px 10px;
        border-radius: 6px;
        border: 1px solid rgba(99,102,241,0.18);
        font-weight: 600;
        letter-spacing: 0.8px;
        animation: popIn 0.6s ease-out 0.3s backwards;
    }
    .header-sub {
        font-family: 'DM Sans', sans-serif;
        font-size: 13px;
        color: var(--text-dim);
        animation: fadeIn 1s ease-out 0.4s backwards;
    }

    /* ═══════════════════════════════════════════
       LIVE PULSE
       ═══════════════════════════════════════════ */
    .live-dot {
        display: inline-block;
        width: 7px; height: 7px;
        border-radius: 50%;
        background: var(--success);
        animation: livePulse 2s ease-in-out infinite;
        margin-right: 6px;
        box-shadow: 0 0 8px rgba(16,185,129,0.4);
    }

    /* ═══════════════════════════════════════════
       SIDEBAR INFO BOX
       ═══════════════════════════════════════════ */
    .sidebar-info {
        margin-top: 16px;
        padding: 16px;
        background: linear-gradient(145deg, var(--bg-surface), var(--bg-card));
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        font-size: 11px;
        color: var(--text-muted);
        line-height: 1.9;
    }
    .sidebar-info strong {
        color: var(--text-secondary);
        font-weight: 500;
    }

    /* ═══════════════════════════════════════════
       TABS — Modern Underlined
       ═══════════════════════════════════════════ */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        border-bottom: 1px solid var(--border);
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: var(--text-muted);
        font-family: 'Outfit', sans-serif;
        font-weight: 500;
        font-size: 13px;
        padding: 12px 28px;
        border-bottom: 2px solid transparent;
        transition: all 0.3s ease;
    }
    .stTabs [aria-selected="true"] {
        color: var(--text-primary);
        border-bottom-color: var(--accent);
        background: transparent;
    }

    /* ═══════════════════════════════════════════
       STATUS WIDGET + SELECTBOX + INPUTS
       ═══════════════════════════════════════════ */
    div[data-testid="stStatusWidget"] {
        background: var(--bg-surface);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
    }
    div[data-testid="stSelectbox"] > div > div {
        background: var(--bg-surface);
        border-color: var(--border);
        border-radius: var(--radius-md);
    }

    /* Loading bar custom */
    .loading-stage {
        display: flex; align-items: center; gap: 10px;
        padding: 10px 16px; margin: 4px 0;
        border-radius: 8px;
        font-size: 12px; font-family: 'DM Sans', sans-serif;
        animation: slideInLeft 0.4s ease-out backwards;
    }
    .loading-stage .stage-dot {
        width: 8px; height: 8px; border-radius: 50%;
        animation: livePulse 1.5s ease-in-out infinite;
    }
    .loading-complete { color: var(--success); }
    .loading-active { color: var(--accent-light); }

    /* ═══════════════════════════════════════════
       HIDE STREAMLIT EXTRAS
       ═══════════════════════════════════════════ */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    header[data-testid="stHeader"] { background: transparent; }
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
        "post_spike_fade_pct": 0.32,  # FIX #13: Crash spikes cascade → less retrace
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
        "post_spike_fade_pct": 0.30,  # FIX #13: Crash = less retrace
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
        "post_spike_fade_pct": 0.28,  # FIX #13: Crash = less retrace
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
        "post_spike_fade_pct": 0.28,  # FIX #13: Crash = less retrace
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
        "post_spike_fade_pct": 0.24,  # FIX #13: Crash 1000 = least retrace
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

# [V25] Removed: analyze_gbm, analyze_step (BC-only system)

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

# [V25] Removed: volatility_clustering_test (not used for BC synthetics)

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
# V24-F FIX #7: M5 PRE-SPIKE COMPRESSION PROXY
# ==============================================================================

def bc_m5_compression(m5_df, atr_m15_clean, lookback_candles=10):
    """Detecta compressão pré-spike usando dados M5.
    Antes do spike, os últimos 5-10 candles M5 mostram ranges cada vez menores.
    micro_range = soma(ranges últimos candles M5) / ATR_M15_clean
    Se < 0.25: COMPRESSÃO EXTREMA (spike provável)
    Se < 0.35: COMPRESSÃO ALTA (alerta)"""
    try:
        if m5_df is None or len(m5_df) < lookback_candles or atr_m15_clean <= 0:
            return {"compression": "NONE", "score": 0, "micro_range_ratio": 1.0,
                    "block_scalp": False, "boost_spike": 0}
        d = m5_df.tail(lookback_candles)
        ranges = (d['high'] - d['low']).values
        if len(ranges) < 5:
            return {"compression": "NONE", "score": 0, "micro_range_ratio": 1.0,
                    "block_scalp": False, "boost_spike": 0}
        # Sum of M5 ranges vs M15 clean ATR
        total_range = float(np.sum(ranges))
        micro_ratio = total_range / (atr_m15_clean * (lookback_candles / 3))  # normalize to ~3 M15 candles

        # Compressão progressiva: últimos 3 ranges < primeiros 3 ranges
        if len(ranges) >= 6:
            recent_avg = float(np.mean(ranges[-3:]))
            early_avg = float(np.mean(ranges[:3]))
            progressive = recent_avg < early_avg * 0.7 if early_avg > 0 else False
        else:
            progressive = False

        # Classificar
        if micro_ratio < 0.20:
            level = "EXTREME"
            score = 25
            block_scalp = True
            boost_spike = 20
        elif micro_ratio < 0.30:
            level = "HIGH"
            score = 15
            block_scalp = progressive  # Only block if progressive compression
            boost_spike = 12
        elif micro_ratio < 0.45:
            level = "MODERATE"
            score = 8
            block_scalp = False
            boost_spike = 5
        else:
            level = "NONE"
            score = 0
            block_scalp = False
            boost_spike = 0

        # Progressive bonus
        if progressive and level != "NONE":
            score += 5
            boost_spike += 3

        return {"compression": level, "score": score, "micro_range_ratio": round(micro_ratio, 3),
                "block_scalp": block_scalp, "boost_spike": boost_spike,
                "progressive": progressive}
    except:
        return {"compression": "NONE", "score": 0, "micro_range_ratio": 1.0,
                "block_scalp": False, "boost_spike": 0}

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
# V24-F FIX #8: DEDICATED BC SCORE — 10 BC-SPECIFIC FACTORS
# ==============================================================================

def calculate_bc_score(setup_type, bc_spike, bc_drift, bc_regime, bc_kurt,
                       bc_freq, bc_absorb, bc_compress, bc_conflicts,
                       bc_stoch, sim_results=None,
                       bc_ema_stack=None, bc_gradient=None, bc_recovery=None,
                       bc_consec=None, bc_channel=None,
                       bc_m5_pulse=None, bc_m5_struct=None, bc_m5_wicks=None):
    """V25: Scoring dedicado BC com 12+ factores.
    SCALP_DRIFT uses M5-specific factors (pulse, structure, wicks).
    Factores: timing, drift_health, regime, kurtosis, recovery, compression,
    consecutive, conflicts, backtest, stochastic, channel, stack, m5_scalp."""
    try:
        total = 0
        breakdown = {}
        bc_ema_stack = bc_ema_stack or {}
        bc_gradient = bc_gradient or {}
        bc_recovery = bc_recovery or {}
        bc_consec = bc_consec or {}
        bc_channel = bc_channel or {}
        bc_m5_pulse = bc_m5_pulse or {}
        bc_m5_struct = bc_m5_struct or {}
        bc_m5_wicks = bc_m5_wicks or {}

        # ═══ SCALP_DRIFT FAST PATH — M5-specific scoring ═══
        if setup_type == "SCALP_DRIFT":
            # M5 Pulse (max 18pts) — PRIMARY factor
            if bc_m5_pulse.get('optimal_entry'):
                m5_pulse_pts = 18
            elif bc_m5_pulse.get('pulse_active'):
                m5_pulse_pts = 10
            else:
                m5_pulse_pts = 0
            total += m5_pulse_pts
            breakdown['m5_pulse'] = m5_pulse_pts

            # M5 Structure (max 14pts)
            if bc_m5_struct.get('entry_window') and bc_m5_struct.get('quality') == 'EXCELLENT':
                m5_struct_pts = 14
            elif bc_m5_struct.get('entry_window'):
                m5_struct_pts = 10
            elif bc_m5_struct.get('pattern') not in ['NONE', None]:
                m5_struct_pts = 5
            else:
                m5_struct_pts = 0
            total += m5_struct_pts
            breakdown['m5_structure'] = m5_struct_pts

            # M5 Wicks (max 10pts)
            wick_sig = bc_m5_wicks.get('signal', 'NEUTRAL')
            if wick_sig == 'STRONG_REJECTION':
                m5_wick_pts = 10
            elif wick_sig == 'MODERATE_REJECTION':
                m5_wick_pts = 6
            elif wick_sig in ['EXHAUSTION', 'WEAK_EXHAUSTION']:
                m5_wick_pts = -8  # Penalty: drift exhausting
            else:
                m5_wick_pts = 2
            total += m5_wick_pts
            breakdown['m5_wicks'] = m5_wick_pts

            # Gradient (max 12pts)
            grad = bc_gradient.get('gradient', 1.0)
            grad_safe = bc_gradient.get('safe_to_enter', True)
            if grad > 1.1 and grad_safe:
                grad_pts = 12
            elif grad > 0.9 and grad_safe:
                grad_pts = 8
            elif grad > 0.8:
                grad_pts = 4
            else:
                grad_pts = 0
            total += grad_pts
            breakdown['gradient'] = grad_pts

            # Stack (max 8pts)
            stack_pts = min(8, bc_ema_stack.get('stack_score', 0) // 2)
            total += stack_pts
            breakdown['stack'] = stack_pts

            # Spike proximity penalty (max -15pts)
            spike_risk = bc_consec.get('spike_risk', 0)
            spike_pen = 0
            if spike_risk > 70: spike_pen = -15
            elif spike_risk > 50: spike_pen = -8
            elif spike_risk > 30: spike_pen = -3
            total += spike_pen
            breakdown['spike_penalty'] = spike_pen

            # Drift quality (max 8pts)
            drift_qual = bc_drift.get('quality', 'CHOPPY')
            drift_pts = 8 if drift_qual == 'SMOOTH' else 5 if drift_qual == 'MODERATE' else 1
            total += drift_pts
            breakdown['drift_quality'] = drift_pts

            # Conflict penalty
            conflict_pen = min(10, bc_conflicts.get('conflict_penalty', 0))
            total -= conflict_pen
            breakdown['conflict_penalty'] = -conflict_pen

            # GRADE (max ~85pts, threshold: 30 for PASS)
            total = max(0, min(90, total))
            if total >= 70: grade = "S"
            elif total >= 55: grade = "A+"
            elif total >= 40: grade = "A"
            elif total >= 30: grade = "B"
            elif total >= 20: grade = "C"
            else: grade = "D"

            if total >= 30: status = "PASS"    # Lower threshold for scalp
            elif total >= 20: status = "MONITOR"
            else: status = "FAIL"

            return {"score": total, "grade": grade, "status": status,
                    "breakdown": breakdown, "setup_type": setup_type}

        # ═══ STANDARD BC SCORING (non-scalp setups) ═══

        # 1. SPIKE TIMING — Weibull + consecutive (max 25pts)
        weibull = bc_spike.get('weibull_prob', 0)
        consec_risk = bc_consec.get('spike_risk', 0)
        if setup_type in ["SPIKE_CATCH"]:
            timing_score = min(25, int(weibull * 20) + int(consec_risk * 0.08))
        elif setup_type in ["DRIFT_RIDE"]:
            timing_score = min(25, int((1.0 - weibull) * 15) + max(0, int((100 - consec_risk) * 0.10)))
        elif setup_type in ["POST_SPIKE"]:
            csl = bc_spike.get('candles_since_last', 999)
            timing_score = 25 if csl <= 2 else 15 if csl <= 4 else 5 if csl <= 6 else 0
        else:
            timing_score = min(20, int(bc_spike.get('prob_discounted', 0) * 0.25))
        total += timing_score
        breakdown['spike_timing'] = timing_score

        # 2. DRIFT HEALTH — Stack + Gradient + Drift analyzer (max 22pts)
        drift_str = bc_drift.get('strength', 0)
        drift_qual = bc_drift.get('quality', 'CHOPPY')
        stack_score = bc_ema_stack.get('stack_score', 0)
        gradient_val = bc_gradient.get('gradient', 1.0)
        gradient_safe = bc_gradient.get('safe_to_enter', True)

        if setup_type in ["DRIFT_RIDE"]:
            qual_mult = {"SMOOTH": 1.0, "MODERATE": 0.7, "CHOPPY": 0.3}.get(drift_qual, 0.5)
            drift_base = int(drift_str * 0.12 * qual_mult)
            stack_pts = min(8, stack_score // 2)
            grad_pts = 6 if gradient_val > 1.1 else 3 if gradient_val > 0.8 else 0
            if not gradient_safe: grad_pts = 0  # Gradient says DYING
            drift_score = min(22, drift_base + stack_pts + grad_pts)
        elif setup_type in ["SPIKE_CATCH"]:
            drift_count = bc_spike.get('drift_count', 0)
            destack = 5 if bc_ema_stack.get('destack_warning') else 0
            drift_score = min(22, drift_count * 2 + destack)
        elif setup_type in ["POST_SPIKE"]:
            recovery_pts = 12 if bc_recovery.get('fade_safe') else 0
            drift_score = min(22, recovery_pts + min(8, stack_score // 3))
        else:
            drift_score = min(15, int(drift_str * 0.15))
        total += drift_score
        breakdown['drift_health'] = drift_score

        # 3. REGIME (max 15pts) — unchanged
        regime = bc_regime.get('regime', 'UNKNOWN')
        regime_scores = {
            "DRIFT_SMOOTH": {"DRIFT_RIDE": 15, "SPIKE_CATCH": 3, "POST_SPIKE": 5, "REVERSAL": 8},
            "PRE_SPIKE":    {"DRIFT_RIDE": 2, "SPIKE_CATCH": 15, "POST_SPIKE": 3, "REVERSAL": 5},
            "POST_SPIKE":   {"DRIFT_RIDE": 5, "SPIKE_CATCH": 3, "POST_SPIKE": 15, "REVERSAL": 12},
            "SPIKE_CLUSTER":{"DRIFT_RIDE": 0, "SPIKE_CATCH": 12, "POST_SPIKE": 10, "REVERSAL": 5},
            "CHOPPY":       {"DRIFT_RIDE": 3, "SPIKE_CATCH": 5, "POST_SPIKE": 5, "REVERSAL": 3},
        }
        regime_score = regime_scores.get(regime, {}).get(setup_type, 5)
        total += regime_score
        breakdown['regime'] = regime_score

        # 4. KURTOSIS (max 10pts) — unchanged
        kurt_val = bc_kurt.get('kurtosis', 3.0)
        if setup_type in ["SPIKE_CATCH"]:
            kurt_score = min(10, int(max(0, kurt_val - 3) * 2))
        elif setup_type in ["DRIFT_RIDE"]:
            kurt_score = min(10, int(max(0, 8 - kurt_val) * 2))
        else:
            kurt_score = 5
        total += kurt_score
        breakdown['kurtosis'] = kurt_score

        # 5. RECOVERY + ABSORPTION (max 12pts) — ENHANCED with recovery speed
        has_absorb = bc_absorb.get('absorption', False)
        absorb_str = bc_absorb.get('strength', 0)
        recovery_safe = bc_recovery.get('fade_safe', False)
        recovery_phase = bc_recovery.get('recovery_phase', 'NONE')

        if setup_type in ["POST_SPIKE"]:
            absorb_pts = min(6, int(absorb_str * 0.1)) if has_absorb else 0
            recovery_pts = 6 if recovery_safe else (3 if recovery_phase == "MODERATE_RECOVERY" else 0)
            absorb_score = min(12, absorb_pts + recovery_pts)
        elif setup_type in ["REVERSAL"]:
            absorb_score = min(12, int(absorb_str * 0.15)) if has_absorb else 0
        elif setup_type in ["DRIFT_RIDE"]:
            absorb_score = 6  # Neutral
        else:
            absorb_score = 3 if has_absorb else 0
        total += absorb_score
        breakdown['recovery_absorb'] = absorb_score

        # 6. CHANNEL POSITION (max 10pts) — NEW
        channel_zone = bc_channel.get('entry_zone', 'NONE')
        zone_scores = {
            "DRIFT_RIDE": {"DRIFT_RIDE": 10, "SPIKE_CATCH": 2, "POST_SPIKE": 3},
            "SPIKE_CATCH": {"DRIFT_RIDE": 0, "SPIKE_CATCH": 10, "POST_SPIKE": 5},
            "POST_SPIKE": {"DRIFT_RIDE": 3, "SPIKE_CATCH": 2, "POST_SPIKE": 10},
            "FADE_ZONE": {"DRIFT_RIDE": 2, "SPIKE_CATCH": 3, "POST_SPIKE": 8},
            "NEUTRAL": {"DRIFT_RIDE": 5, "SPIKE_CATCH": 5, "POST_SPIKE": 5},
        }
        channel_score = zone_scores.get(channel_zone, {}).get(setup_type, 3)
        total += channel_score
        breakdown['channel'] = channel_score

        # 7. M5 COMPRESSION (max 10pts)
        compress_score_raw = bc_compress.get('score', 0)
        if setup_type in ["SPIKE_CATCH"]:
            compress_score = min(10, compress_score_raw)
        elif setup_type in ["DRIFT_RIDE"]:
            compress_score = max(0, 10 - compress_score_raw)
        else:
            compress_score = min(5, compress_score_raw // 2)
        total += compress_score
        breakdown['m5_compression'] = compress_score

        # 8. CONFLICT PENALTY (max -15pts)
        conflict_pen = min(15, bc_conflicts.get('conflict_penalty', 0))
        if setup_type == "DRIFT_RIDE" and not bc_conflicts.get('allow_drift_ride', True):
            conflict_pen = max(conflict_pen, 12)
        elif setup_type == "SPIKE_CATCH" and not bc_conflicts.get('allow_spike_catch', True):
            conflict_pen = max(conflict_pen, 10)
        total -= conflict_pen
        breakdown['conflict_penalty'] = -conflict_pen

        # 9. BACKTEST (max 10pts)
        bt_score = 0
        if sim_results:
            wr = sim_results.get('WR', 50)
            pf = sim_results.get('PF', 1.0)
            if wr > 60 and pf > 1.5: bt_score = 10
            elif wr > 55 and pf > 1.2: bt_score = 7
            elif wr > 50 and pf > 1.0: bt_score = 4
        total += bt_score
        breakdown['backtest'] = bt_score

        # 10. STOCHASTIC TIMER (max 10pts)
        stoch_ready = bc_stoch.get('ready', False)
        stoch_score = 10 if stoch_ready else 3
        if setup_type in ["SPIKE_CATCH"] and bc_stoch.get('signal', '') in ["SPIKE_BUY", "SPIKE_SELL"]:
            stoch_score = 10
        elif setup_type in ["DRIFT_RIDE"] and bc_stoch.get('signal', '') in ["DRIFT_BUY", "DRIFT_SELL"]:
            stoch_score = 10
        total += stoch_score
        breakdown['stochastic'] = stoch_score

        # GRADE (max ~146pts theoretical, ~100 typical)
        total = max(0, min(146, total))
        if total >= 100: grade = "S"
        elif total >= 85: grade = "A++"
        elif total >= 70: grade = "A+"
        elif total >= 55: grade = "A"
        elif total >= 40: grade = "B"
        elif total >= 25: grade = "C"
        else: grade = "D"

        if total >= 55: status = "PASS"
        elif total >= 40: status = "MONITOR"
        else: status = "FAIL"

        return {"score": total, "grade": grade, "status": status,
                "breakdown": breakdown, "setup_type": setup_type}
    except:
        return {"score": 0, "grade": "D", "status": "FAIL",
                "breakdown": {}, "setup_type": setup_type}

# ==============================================================================
# V24-F O5: ANTI-MELTDOWN KILL-SWITCH (FUNCTIONAL)
# ==============================================================================

def bc_meltdown_check(session_state_key='bc_loss_streak'):
    """V24-F FIX #5: Kill-switch FUNCIONAL.
    Antes: lia session_state mas nada escrevia nela → código morto.
    Agora: inicializa se não existe + função de registo abaixo."""
    try:
        if session_state_key not in st.session_state:
            st.session_state[session_state_key] = 0
        streak = st.session_state.get(session_state_key, 0)
        if streak >= 5:
            return {"blocked": True, "reason": f"KILL-SWITCH: {streak} consecutive losses — manual reset required",
                    "score_boost": 0, "streak": streak}
        elif streak >= 3:
            return {"blocked": False, "reason": f"CAUTION: {streak} consecutive losses — score +50%",
                    "score_boost": 50, "streak": streak}
        return {"blocked": False, "reason": None, "score_boost": 0, "streak": streak}
    except:
        return {"blocked": False, "reason": None, "score_boost": 0, "streak": 0}

def bc_record_trade_result(won, session_state_key='bc_loss_streak'):
    """FIX #5: Regista resultado de trade para kill-switch.
    won=True → reset streak, won=False → increment streak."""
    if session_state_key not in st.session_state:
        st.session_state[session_state_key] = 0
    if won:
        st.session_state[session_state_key] = 0
    else:
        st.session_state[session_state_key] = st.session_state.get(session_state_key, 0) + 1

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

def bc_poisson_spike_probability(candles_since_last, avg_interval, spike_count=0, kurtosis=3.0):
    """V24-F: Weibull CDF CORRIGIDA para timing de spike.
    ANTES: usava hazard rate como probabilidade — ERRADO (6× subestimação).
    CORRECTO: P(T ≤ t) = 1 - exp(-(t/scale)^shape)
    FIX #14: Shape dinâmico baseado na kurtosis."""
    try:
        if avg_interval <= 0 or candles_since_last <= 0:
            return 0.0
        scale = avg_interval  # scale = avg_interval (NÃO 1/avg_interval)
        # FIX #14: Shape dinâmico — kurtosis alta = hazard mais íngreme
        if kurtosis > 8:
            shape = 1.5   # EXTREME_SPIKE: hazard sobe rápido
        elif kurtosis > 5:
            shape = 1.35  # SPIKE_PRONE: hazard moderado
        else:
            shape = 1.2   # NORMAL: hazard suave
        # CDF Weibull: P(spike até t candles)
        prob = 1.0 - np.exp(-((candles_since_last / scale) ** shape))
        return round(min(0.95, max(0.0, float(prob))), 3)
    except:
        return 0.0

def bc_spike_detector(df, profile, lookback=30, bc_kurt_data=None):
    """V24-F: Detecta condições de spike iminente em Boom/Crash.
    FIX #1: Weibull CDF corrigida | FIX #2: Clean ATR universal
    FIX #14: Shape dinâmico via kurtosis | FIX #15: Volume acceleration"""
    try:
        if len(df) < lookback + 5:
            return {"spike_imminent": False, "probability": 0, "type": "NONE",
                    "candles_since_last": 999, "rsi_zone": "NEUTRAL",
                    "prob_discounted": 0, "weibull_prob": 0, "vol_ratio": 0.0,
                    "active_factors": 0}
        is_boom = profile.get('gen_type') == 'BOOM'
        d = df.tail(lookback)
        rsi = d['RSI'].iloc[-1] if pd.notna(d['RSI'].iloc[-1]) else 50
        # FIX #2: Use CLEAN ATR everywhere
        clean_atr = bc_clean_atr(df, profile, lookback=50)
        if clean_atr == 0:
            clean_atr = d['ATR'].iloc[-1] if pd.notna(d['ATR'].iloc[-1]) else 1.0
        spike_min = profile.get('spike_size_min_atr', 2.0)
        candles_since = 0
        for i in range(len(d)-1, 0, -1):
            move = abs(d['close'].iloc[i] - d['close'].iloc[i-1])
            if clean_atr > 0 and move > spike_min * clean_atr:
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

        # Empirical spike timing using CLEAN ATR
        empirical_intervals = []
        spike_positions = []
        for i in range(1, len(d)):
            move = d['close'].iloc[i] - d['close'].iloc[i-1]
            if is_boom and move > spike_min * clean_atr and clean_atr > 0:
                spike_positions.append(i)
            elif not is_boom and move < -spike_min * clean_atr and clean_atr > 0:
                spike_positions.append(i)
        if len(spike_positions) >= 2:
            empirical_intervals = [spike_positions[j+1] - spike_positions[j]
                                   for j in range(len(spike_positions)-1)]
            avg_m15_interval = np.mean(empirical_intervals)
        else:
            freq_map = {"HIGH": 4, "MEDIUM": 8, "LOW": 15}
            avg_m15_interval = freq_map.get(profile.get('spike_freq', 'MEDIUM'), 8)

        # FIX #1+#14: Weibull CORRIGIDA com shape dinâmico
        kurt_val = bc_kurt_data.get('kurtosis', 3.0) if bc_kurt_data else 3.0
        poisson_prob = bc_poisson_spike_probability(candles_since, avg_m15_interval,
                                                     kurtosis=kurt_val)
        time_bonus = int(poisson_prob * 25)
        prob += time_bonus

        # BB squeeze = compression before spike
        bb_active = False
        if 'BB_width' in d.columns and pd.notna(d['BB_width'].iloc[-1]):
            bb_mean = d['BB_width'].rolling(20).mean().iloc[-1]
            if pd.notna(bb_mean) and bb_mean > 0:
                if d['BB_width'].iloc[-1] < bb_mean * 0.7:
                    prob += 10; bb_active = True

        # FIX #15: TICK VOLUME ACCELERATION
        vol_ratio = 0.0
        vol_bonus = 0
        if 'volume' in d.columns:
            recent_vol = d['volume'].tail(5).mean()
            avg_vol = d['volume'].tail(20).mean()
            if avg_vol > 0:
                vol_ratio = float(recent_vol / avg_vol)
                if vol_ratio > 2.5: vol_bonus = 20
                elif vol_ratio > 1.8: vol_bonus = 12
                elif vol_ratio > 1.3: vol_bonus = 5
        prob += vol_bonus

        # Multi-factor correlation discount (factors are correlated)
        active_factors = sum([rsi_active, drift_active, time_bonus > 10,
                             vol_bonus > 5, bb_active])
        if active_factors >= 4:
            prob = int(prob * 0.55)
        elif active_factors >= 3:
            prob = int(prob * 0.70)
        elif active_factors >= 2:
            prob = int(prob * 0.85)

        prob_discounted = min(95, prob)
        spike_type = "SPIKE_UP" if is_boom else "CRASH_DOWN"
        return {"spike_imminent": prob_discounted >= 45, "probability": prob_discounted,
                "prob_discounted": prob_discounted,
                "type": spike_type, "candles_since_last": candles_since,
                "rsi_zone": rsi_zone, "drift_count": drift_count,
                "rsi_value": round(float(rsi), 1),
                "vol_ratio": round(vol_ratio, 2),
                "active_factors": active_factors,
                "weibull_prob": round(float(poisson_prob), 3),
                "avg_interval": round(float(avg_m15_interval), 1)}
    except:
        return {"spike_imminent": False, "probability": 0, "type": "NONE",
                "candles_since_last": 999, "rsi_zone": "NEUTRAL",
                "prob_discounted": 0, "weibull_prob": 0, "vol_ratio": 0.0,
                "active_factors": 0}

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
    """V24-F: Analisa frequência de spikes usando clean ATR."""
    try:
        if len(df) < lookback:
            return {"avg_interval": 0, "last_spike_ago": 999, "overdue": False,
                    "spike_count": 0, "next_spike_window": "UNKNOWN"}
        d = df.tail(lookback)
        atr = bc_clean_atr(df, profile, lookback=lookback)
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
# V24-F NEW TOOL #1: EMA DRIFT STACK — Stacking detection
# ==============================================================================

def bc_ema_drift_stack(df, profile, lookback=20):
    """Detecta se EMAs 5/10/15/20 estão empilhadas na direcção do drift.
    Stack perfeito = drift saudável. Destack = spike proximity.
    Boom: EMA5 < EMA10 < EMA15 < EMA20 (bearish stack)
    Crash: EMA5 > EMA10 > EMA15 > EMA20 (bullish stack)"""
    try:
        if len(df) < lookback + 25:
            return {"stacked": False, "stack_score": 0, "destack_warning": False,
                    "direction": "NONE", "stack_quality": "NONE"}
        d = df.tail(lookback)
        close = d['close'].values
        ema5 = float(pd.Series(close).ewm(span=5).mean().iloc[-1])
        ema10 = float(pd.Series(close).ewm(span=10).mean().iloc[-1])
        ema15 = float(pd.Series(close).ewm(span=15).mean().iloc[-1])
        ema20 = float(pd.Series(close).ewm(span=20).mean().iloc[-1])
        is_boom = profile.get('gen_type') == 'BOOM'

        if is_boom:
            # Boom drift DOWN: EMA5 < EMA10 < EMA15 < EMA20
            pairs_ok = int(ema5 < ema10) + int(ema10 < ema15) + int(ema15 < ema20)
            direction = "BEARISH"
            # Destack warning: EMA5 crossed ABOVE EMA10 (drift weakening)
            destack = ema5 > ema10
        else:
            # Crash drift UP: EMA5 > EMA10 > EMA15 > EMA20
            pairs_ok = int(ema5 > ema10) + int(ema10 > ema15) + int(ema15 > ema20)
            direction = "BULLISH"
            destack = ema5 < ema10

        stacked = pairs_ok == 3
        # Stack quality by EMA separation uniformity
        separations = [abs(ema5-ema10), abs(ema10-ema15), abs(ema15-ema20)]
        if min(separations) > 0:
            uniformity = min(separations) / max(separations) if max(separations) > 0 else 0
        else:
            uniformity = 0

        if stacked and uniformity > 0.5:
            quality = "PERFECT"
            score = 20
        elif stacked:
            quality = "GOOD"
            score = 15
        elif pairs_ok >= 2:
            quality = "PARTIAL"
            score = 8
        else:
            quality = "BROKEN"
            score = 0

        return {"stacked": stacked, "stack_score": score, "destack_warning": destack,
                "direction": direction, "stack_quality": quality,
                "pairs_ok": pairs_ok, "uniformity": round(uniformity, 2),
                "emas": {"e5": round(ema5,5), "e10": round(ema10,5),
                         "e15": round(ema15,5), "e20": round(ema20,5)}}
    except:
        return {"stacked": False, "stack_score": 0, "destack_warning": False,
                "direction": "NONE", "stack_quality": "NONE"}

# ==============================================================================
# V24-F NEW TOOL #2: DRIFT MOMENTUM GRADIENT — Drift acceleration
# ==============================================================================

def bc_drift_momentum_gradient(df, profile, lookback=15):
    """Mede se o drift está a ACELERAR ou DESACELERAR.
    gradient > 1.2: drift acelerando → safe to ride
    gradient 0.8-1.2: drift estável
    gradient < 0.8: drift desacelerando → spike approaching
    gradient < 0.5: drift morto → spike iminente"""
    try:
        if len(df) < lookback + 5:
            return {"gradient": 1.0, "phase": "STABLE", "safe_to_enter": True,
                    "spike_proximity": 0}
        d = df.tail(lookback)
        is_boom = profile.get('gen_type') == 'BOOM'
        # Measure directional candle bodies (drift direction only)
        bodies = abs(d['close'] - d['open']).values
        if len(bodies) < 6:
            return {"gradient": 1.0, "phase": "STABLE", "safe_to_enter": True,
                    "spike_proximity": 0}

        recent_bodies = float(np.mean(bodies[-3:]))
        earlier_bodies = float(np.mean(bodies[-10:-5])) if len(bodies) >= 10 else float(np.mean(bodies[:3]))

        gradient = recent_bodies / earlier_bodies if earlier_bodies > 0 else 1.0

        # Also check directional consistency
        if is_boom:
            recent_drift = sum(1 for i in range(-3, 0) if d['close'].iloc[i] < d['open'].iloc[i])
            earlier_drift = sum(1 for i in range(-8, -5) if d['close'].iloc[i] < d['open'].iloc[i])
        else:
            recent_drift = sum(1 for i in range(-3, 0) if d['close'].iloc[i] > d['open'].iloc[i])
            earlier_drift = sum(1 for i in range(-8, -5) if d['close'].iloc[i] > d['open'].iloc[i])

        drift_consistency = (recent_drift + earlier_drift) / 6.0  # 0 to 1

        if gradient > 1.2 and drift_consistency > 0.6:
            phase = "ACCELERATING"
            safe = True
            spike_prox = 0
        elif gradient >= 0.8:
            phase = "STABLE"
            safe = True
            spike_prox = 20
        elif gradient >= 0.5:
            phase = "DECELERATING"
            safe = False  # Drift weakening
            spike_prox = 50
        else:
            phase = "DYING"
            safe = False
            spike_prox = 80

        return {"gradient": round(gradient, 3), "phase": phase,
                "safe_to_enter": safe, "spike_proximity": spike_prox,
                "drift_consistency": round(drift_consistency, 2)}
    except:
        return {"gradient": 1.0, "phase": "STABLE", "safe_to_enter": True,
                "spike_proximity": 0}

# ==============================================================================
# V24-F NEW TOOL #3: SPIKE RECOVERY SPEED — Post-spike analysis
# ==============================================================================

def bc_spike_recovery_speed(df, profile, lookback=15):
    """Após spike, mede velocidade de retorno ao drift.
    Recovery rápido = drift retoma, fade safe.
    Recovery lento = regime change possível, não entrar."""
    try:
        if len(df) < lookback + 3:
            return {"has_recent_spike": False, "recovery_speed": 0,
                    "recovery_phase": "NONE", "fade_safe": False}
        d = df.tail(lookback)
        is_boom = profile.get('gen_type') == 'BOOM'
        atr = bc_clean_atr(df, profile, lookback=50)
        spike_min = profile.get('spike_size_min_atr', 2.0)

        # Find most recent spike
        spike_idx = -1
        spike_size = 0
        for i in range(len(d)-1, max(0, len(d)-8), -1):
            move = d['close'].iloc[i] - d['close'].iloc[i-1] if i > 0 else 0
            if atr > 0 and abs(move) > spike_min * atr:
                spike_idx = i
                spike_size = move
                break

        if spike_idx < 0 or spike_idx >= len(d) - 2:
            return {"has_recent_spike": False, "recovery_speed": 0,
                    "recovery_phase": "NONE", "fade_safe": False}

        candles_after = len(d) - 1 - spike_idx
        if candles_after < 1:
            return {"has_recent_spike": True, "recovery_speed": 0,
                    "recovery_phase": "JUST_SPIKED", "fade_safe": False}

        # Recovery = how much price moved BACK after spike
        price_at_spike = float(d['close'].iloc[spike_idx])
        price_now = float(d['close'].iloc[-1])
        recovery = (price_now - price_at_spike)

        # Normalize by spike size
        recovery_ratio = abs(recovery / spike_size) if spike_size != 0 else 0

        # Direction check
        if is_boom and spike_size > 0:
            # Boom spike UP → recovery should be DOWN (negative)
            recovering = recovery < 0
        elif not is_boom and spike_size < 0:
            # Crash spike DOWN → recovery should be UP (positive)
            recovering = recovery > 0
        else:
            recovering = False

        # Classify
        if recovering and recovery_ratio > 0.3:
            phase = "FAST_RECOVERY"
            fade_safe = True
        elif recovering and recovery_ratio > 0.15:
            phase = "MODERATE_RECOVERY"
            fade_safe = candles_after >= 2
        elif recovery_ratio < 0.1:
            phase = "STALLED"
            fade_safe = False  # Not recovering, don't fade
        else:
            phase = "SLOW_RECOVERY"
            fade_safe = False

        return {"has_recent_spike": True, "recovery_speed": round(recovery_ratio, 3),
                "recovery_phase": phase, "fade_safe": fade_safe,
                "candles_after_spike": candles_after,
                "spike_size": round(abs(spike_size), 5)}
    except:
        return {"has_recent_spike": False, "recovery_speed": 0,
                "recovery_phase": "NONE", "fade_safe": False}

# ==============================================================================
# V24-F NEW TOOL #4: CONSECUTIVE DIRECTION COUNTER (Enhanced)
# ==============================================================================

def bc_consecutive_drift_counter(df, profile, lookback=20):
    """Conta candles consecutivos na direcção do drift com zonas claras.
    3-5: drift normal | 5-8: prolongado, spike approach | 8+: spike overdue"""
    try:
        if len(df) < lookback:
            return {"count": 0, "zone": "NONE", "entry_quality": "NONE",
                    "spike_risk": 0}
        d = df.tail(lookback)
        is_boom = profile.get('gen_type') == 'BOOM'
        count = 0
        for i in range(len(d)-1, 0, -1):
            if is_boom and d['close'].iloc[i] < d['open'].iloc[i]:
                count += 1  # Bearish candle = drift direction for Boom
            elif not is_boom and d['close'].iloc[i] > d['open'].iloc[i]:
                count += 1  # Bullish candle = drift direction for Crash
            else:
                break

        # Also count "mostly drift" with 1 neutral candle allowed
        relaxed_count = 0
        neutral_used = False
        for i in range(len(d)-1, 0, -1):
            if is_boom:
                is_drift = d['close'].iloc[i] < d['open'].iloc[i]
            else:
                is_drift = d['close'].iloc[i] > d['open'].iloc[i]
            is_neutral = abs(d['close'].iloc[i] - d['open'].iloc[i]) < (d['high'].iloc[i] - d['low'].iloc[i]) * 0.2
            if is_drift:
                relaxed_count += 1
            elif is_neutral and not neutral_used:
                relaxed_count += 1
                neutral_used = True
            else:
                break

        effective_count = max(count, relaxed_count)

        if effective_count >= 10:
            zone = "EXTREME_OVERDUE"
            entry_q = "SPIKE_ONLY"  # Only spike catch, no drift
            spike_risk = 95
        elif effective_count >= 8:
            zone = "OVERDUE"
            entry_q = "SPIKE_PREFERRED"
            spike_risk = 80
        elif effective_count >= 5:
            zone = "PROLONGED"
            entry_q = "DRIFT_CAUTION"
            spike_risk = 50
        elif effective_count >= 3:
            zone = "NORMAL"
            entry_q = "DRIFT_SAFE"
            spike_risk = 20
        else:
            zone = "FRESH"
            entry_q = "DRIFT_OPTIMAL"
            spike_risk = 5

        return {"count": effective_count, "strict_count": count,
                "zone": zone, "entry_quality": entry_q,
                "spike_risk": spike_risk}
    except:
        return {"count": 0, "zone": "NONE", "entry_quality": "NONE",
                "spike_risk": 0}

# ==============================================================================
# V24-F NEW TOOL #5: PRICE CHANNEL POSITION (BC-Aware)
# ==============================================================================

def bc_price_channel_position(df, profile, lookback=20):
    """Posição do preço no canal EMA20 ± 1.5×ATR_clean.
    Near drift band: drift maduro → spike zone
    Mid channel: drift fresco → safe zone
    Near counter band: pós-spike → fade zone"""
    try:
        if len(df) < lookback + 5:
            return {"position": "UNKNOWN", "position_pct": 50,
                    "band_distance": 0, "entry_zone": "NONE"}
        d = df.tail(lookback)
        is_boom = profile.get('gen_type') == 'BOOM'
        clean_atr = bc_clean_atr(df, profile, lookback=50)
        ema20 = float(d['close'].ewm(span=20).mean().iloc[-1])
        price = float(d['close'].iloc[-1])

        upper = ema20 + 1.5 * clean_atr
        lower = ema20 - 1.5 * clean_atr
        channel_width = upper - lower
        if channel_width <= 0:
            return {"position": "UNKNOWN", "position_pct": 50,
                    "band_distance": 0, "entry_zone": "NONE"}

        # Position as percentage (0=lower, 100=upper)
        position_pct = ((price - lower) / channel_width) * 100
        position_pct = max(0, min(100, position_pct))

        if is_boom:
            # Boom drifts DOWN: price near LOWER band = drift mature = spike zone
            if position_pct < 20:
                position = "DRIFT_MATURE"
                entry_zone = "SPIKE_CATCH"  # Near bottom = spike coming
            elif position_pct < 40:
                position = "DRIFT_ACTIVE"
                entry_zone = "DRIFT_RIDE"  # Mid-lower = safe drift
            elif position_pct < 60:
                position = "MID_CHANNEL"
                entry_zone = "NEUTRAL"
            elif position_pct < 80:
                position = "COUNTER_DRIFT"
                entry_zone = "FADE_ZONE"  # Near top after spike UP
            else:
                position = "SPIKE_PEAK"
                entry_zone = "POST_SPIKE"
        else:
            # Crash drifts UP: price near UPPER band = drift mature = spike zone
            if position_pct > 80:
                position = "DRIFT_MATURE"
                entry_zone = "SPIKE_CATCH"
            elif position_pct > 60:
                position = "DRIFT_ACTIVE"
                entry_zone = "DRIFT_RIDE"
            elif position_pct > 40:
                position = "MID_CHANNEL"
                entry_zone = "NEUTRAL"
            elif position_pct > 20:
                position = "COUNTER_DRIFT"
                entry_zone = "FADE_ZONE"
            else:
                position = "SPIKE_PEAK"
                entry_zone = "POST_SPIKE"

        return {"position": position, "position_pct": round(position_pct, 1),
                "band_distance": round(abs(price - ema20) / clean_atr, 2) if clean_atr > 0 else 0,
                "entry_zone": entry_zone, "ema20": round(ema20, 5),
                "upper": round(upper, 5), "lower": round(lower, 5)}
    except:
        return {"position": "UNKNOWN", "position_pct": 50,
                "band_distance": 0, "entry_zone": "NONE"}

# ==============================================================================
# V25-SCALP ENGINE #1: M5 MOMENTUM PULSE — Scalp entry timing
# ==============================================================================

def bc_m5_momentum_pulse(m5_df, profile, lookback=15):
    """Detecta pulsos de momentum M5 para scalp timing.
    O drift BC vem em PULSOS de 5-15min seguidos de micro-pausa.
    O scalp ideal entra no INÍCIO do pulso e sai antes da pausa.
    Boom drift DOWN: pulso = candles M5 bearish consecutivos com corpo > 40% range
    Crash drift UP: pulso = candles M5 bullish consecutivos com corpo > 40% range"""
    try:
        if m5_df is None or len(m5_df) < lookback + 3:
            return {"pulse_active": False, "pulse_strength": 0, "pulse_candles": 0,
                    "pulse_phase": "NO_DATA", "optimal_entry": False}
        d = m5_df.tail(lookback)
        is_boom = profile.get('gen_type') == 'BOOM'

        # Count consecutive drift-direction candles with body > 40% range
        pulse_candles = 0
        pulse_bodies = []
        for i in range(len(d)-1, 0, -1):
            rng = float(d['high'].iloc[i] - d['low'].iloc[i])
            body = float(abs(d['close'].iloc[i] - d['open'].iloc[i]))
            body_pct = body / rng if rng > 0 else 0

            if is_boom:
                is_drift_candle = d['close'].iloc[i] < d['open'].iloc[i]  # Bearish
            else:
                is_drift_candle = d['close'].iloc[i] > d['open'].iloc[i]  # Bullish

            # Allow 1 weak candle (doji) within pulse
            is_neutral = body_pct < 0.25
            if is_drift_candle and body_pct > 0.30:
                pulse_candles += 1
                pulse_bodies.append(body)
            elif is_neutral and pulse_candles > 0 and pulse_candles < 6:
                pulse_candles += 1  # Allow 1 doji mid-pulse
                pulse_bodies.append(body * 0.5)
            else:
                break

        # Pulse strength: avg body size relative to range
        if pulse_bodies:
            avg_body = float(np.mean(pulse_bodies))
            avg_range = float((d['high'] - d['low']).tail(lookback).mean())
            pulse_strength = min(100, int(avg_body / avg_range * 150)) if avg_range > 0 else 0
        else:
            pulse_strength = 0

        # Check if bodies are GROWING (acceleration) or SHRINKING (fading)
        if len(pulse_bodies) >= 3:
            recent = float(np.mean(pulse_bodies[:2]))  # Most recent 2
            earlier = float(np.mean(pulse_bodies[-2:]))  # Earliest 2
            body_trend = recent / earlier if earlier > 0 else 1.0
        else:
            body_trend = 1.0

        # Classify phase
        if pulse_candles == 0:
            phase = "PAUSED"
            optimal = False
        elif pulse_candles <= 2 and pulse_strength > 40:
            phase = "STARTING"
            optimal = True  # ← BEST entry point
        elif pulse_candles <= 5 and body_trend >= 0.9:
            phase = "STRONG"
            optimal = False  # Already running
        elif body_trend < 0.7:
            phase = "FADING"
            optimal = False
        else:
            phase = "EXTENDED"
            optimal = False

        # Also check: is there a pause before this pulse? (confirms fresh pulse)
        if pulse_candles >= 1 and pulse_candles <= 3:
            # Check if candle before pulse was against drift or doji
            pre_pulse_idx = len(d) - 1 - pulse_candles
            if pre_pulse_idx >= 0:
                pre_rng = float(d['high'].iloc[pre_pulse_idx] - d['low'].iloc[pre_pulse_idx])
                pre_body = float(abs(d['close'].iloc[pre_pulse_idx] - d['open'].iloc[pre_pulse_idx]))
                pre_body_pct = pre_body / pre_rng if pre_rng > 0 else 0
                if pre_body_pct < 0.35:  # Doji/small candle before pulse = fresh start
                    if phase == "STARTING":
                        pulse_strength = min(100, pulse_strength + 15)

        return {"pulse_active": pulse_candles >= 2, "pulse_strength": pulse_strength,
                "pulse_candles": pulse_candles, "pulse_phase": phase,
                "optimal_entry": optimal, "body_trend": round(body_trend, 2)}
    except:
        return {"pulse_active": False, "pulse_strength": 0, "pulse_candles": 0,
                "pulse_phase": "ERROR", "optimal_entry": False}

# ==============================================================================
# V25-SCALP ENGINE #2: M5 MICRO STRUCTURE — Pattern detection
# ==============================================================================

def bc_m5_micro_structure(m5_df, profile, lookback=20):
    """Detecta padrões M5: micro-pullback, micro-consolidação, micro-breakout.
    Antes de cada pulso, o preço faz micro-consolidação de 2-4 candles M5.
    Detectar isto permite entrar no INÍCIO do próximo pulso."""
    try:
        if m5_df is None or len(m5_df) < lookback:
            return {"pattern": "NONE", "quality": "WEAK", "entry_window": False,
                    "expected_move_atr": 0}
        d = m5_df.tail(lookback)
        is_boom = profile.get('gen_type') == 'BOOM'
        ranges = (d['high'] - d['low']).values
        avg_range = float(np.mean(ranges)) if len(ranges) > 0 else 1

        # Last 5 candles analysis
        last5 = d.tail(5)
        last5_ranges = (last5['high'] - last5['low']).values
        last5_avg_range = float(np.mean(last5_ranges)) if len(last5_ranges) > 0 else 1

        # MICRO CONSOLIDATION: last 3-5 candles have shrinking ranges
        shrinking = all(last5_ranges[i] <= last5_ranges[i-1] * 1.1 for i in range(max(1, len(last5_ranges)-3), len(last5_ranges)))
        tight_range = last5_avg_range < avg_range * 0.6

        # MICRO PULLBACK: 1-3 candles against drift direction, small range
        pullback_count = 0
        for i in range(len(last5)-1, max(0, len(last5)-4), -1):
            if is_boom:
                against_drift = last5['close'].iloc[i] > last5['open'].iloc[i]  # Bullish = against boom drift
            else:
                against_drift = last5['close'].iloc[i] < last5['open'].iloc[i]  # Bearish = against crash drift
            body = abs(float(last5['close'].iloc[i] - last5['open'].iloc[i]))
            small_body = body < avg_range * 0.5
            if against_drift and small_body:
                pullback_count += 1
            else:
                break

        # MICRO BREAKOUT: last candle breaks consolidation range in drift direction
        last_candle = d.iloc[-1]
        prev_high = float(d['high'].iloc[-4:-1].max())
        prev_low = float(d['low'].iloc[-4:-1].min())
        if is_boom:
            breakout = float(last_candle['close']) < prev_low  # Break below = drift breakout
        else:
            breakout = float(last_candle['close']) > prev_high  # Break above = drift breakout

        last_body_pct = abs(float(last_candle['close'] - last_candle['open'])) / float(last_candle['high'] - last_candle['low']) if float(last_candle['high'] - last_candle['low']) > 0 else 0

        # Classify pattern
        if breakout and last_body_pct > 0.55:
            pattern = "MICRO_BREAKOUT"
            quality = "EXCELLENT"
            entry_window = True
        elif pullback_count >= 1 and pullback_count <= 3:
            # Check if last candle is resuming drift direction
            if is_boom:
                resuming = float(last_candle['close']) < float(last_candle['open'])
            else:
                resuming = float(last_candle['close']) > float(last_candle['open'])
            if resuming:
                pattern = "MICRO_PULLBACK"
                quality = "EXCELLENT" if last_body_pct > 0.5 else "GOOD"
                entry_window = True
            else:
                pattern = "MICRO_PULLBACK"
                quality = "GOOD" if pullback_count <= 2 else "WEAK"
                entry_window = False  # Still pulling back
        elif shrinking and tight_range:
            pattern = "MICRO_CONSOLIDATION"
            quality = "GOOD"
            entry_window = False  # Wait for breakout
        else:
            pattern = "NONE"
            quality = "WEAK"
            entry_window = False

        # Expected move: based on previous pulse sizes
        prev_bodies = abs(d['close'] - d['open']).values
        expected_move = float(np.mean(sorted(prev_bodies, reverse=True)[:5])) if len(prev_bodies) >= 5 else avg_range

        return {"pattern": pattern, "quality": quality, "entry_window": entry_window,
                "expected_move_atr": round(expected_move / avg_range, 2) if avg_range > 0 else 0,
                "pullback_candles": pullback_count,
                "consolidation": shrinking and tight_range}
    except:
        return {"pattern": "NONE", "quality": "WEAK", "entry_window": False,
                "expected_move_atr": 0}

# ==============================================================================
# V25-SCALP ENGINE #3: M5 WICKS ANALYSIS — Rejection/exhaustion
# ==============================================================================

def bc_m5_wicks_analysis(m5_df, profile, lookback=10):
    """Analisa pavios M5: wicks contra drift = rejeição (drift continua).
    Wicks na direcção drift = absorção/exaustão (spike approach).
    Boom drift DOWN: pavio superior longo = rejection bull → safe
    Crash drift UP: pavio inferior longo = rejection bear → safe"""
    try:
        if m5_df is None or len(m5_df) < lookback:
            return {"rejection_wicks": 0, "exhaustion_wicks": 0,
                    "wick_ratio": 0.5, "signal": "NEUTRAL"}
        d = m5_df.tail(lookback)
        is_boom = profile.get('gen_type') == 'BOOM'
        rejection_count = 0
        exhaustion_count = 0
        total_significant = 0

        for i in range(len(d)):
            rng = float(d['high'].iloc[i] - d['low'].iloc[i])
            if rng == 0: continue
            upper_wick = float(d['high'].iloc[i] - max(d['close'].iloc[i], d['open'].iloc[i]))
            lower_wick = float(min(d['close'].iloc[i], d['open'].iloc[i]) - d['low'].iloc[i])
            upper_pct = upper_wick / rng
            lower_pct = lower_wick / rng

            # Significant wick = > 35% of range
            if is_boom:
                # Boom drifts DOWN. Upper wick = rejection of upward move = safe
                if upper_pct > 0.35:
                    rejection_count += 1
                    total_significant += 1
                # Lower wick = rejection of downward (drift) = exhaustion
                if lower_pct > 0.35:
                    exhaustion_count += 1
                    total_significant += 1
            else:
                # Crash drifts UP. Lower wick = rejection of downward move = safe
                if lower_pct > 0.35:
                    rejection_count += 1
                    total_significant += 1
                # Upper wick = rejection of upward (drift) = exhaustion
                if upper_pct > 0.35:
                    exhaustion_count += 1
                    total_significant += 1

        if total_significant == 0:
            ratio = 0.5
        else:
            ratio = rejection_count / total_significant

        if rejection_count >= 4:
            signal = "STRONG_REJECTION"
        elif rejection_count >= 2 and exhaustion_count <= 1:
            signal = "MODERATE_REJECTION"
        elif exhaustion_count >= 3:
            signal = "EXHAUSTION"
        elif exhaustion_count >= 2 and rejection_count <= 1:
            signal = "WEAK_EXHAUSTION"
        else:
            signal = "NEUTRAL"

        return {"rejection_wicks": rejection_count, "exhaustion_wicks": exhaustion_count,
                "wick_ratio": round(ratio, 2), "signal": signal,
                "total_significant": total_significant}
    except:
        return {"rejection_wicks": 0, "exhaustion_wicks": 0,
                "wick_ratio": 0.5, "signal": "NEUTRAL"}


# ==============================================================================
# V21 ENGINE #2: PERMUTATION ENTROPY — Determinismo na ordem
# ==============================================================================


# ==============================================================================
# V21 ENGINE #3: SPECTRAL ANALYSIS (FFT) — Ciclos ocultos no CSPRNG
# ==============================================================================

# [V25] Removed: spectral_analysis_v21 (not used for BC synthetics)

# ==============================================================================
# V21 ENGINE #4: TRANSITION MATRIX (Markov Chain)
# ==============================================================================

# [V25] Removed: transition_matrix_v21 (not used for BC synthetics)

# ==============================================================================
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

def calculate_independent_edges(vr, acf, hurst_val, gen_bonus, dist, zscore, align_type):
    """V25: BC-ONLY — Conta confluencias estatísticas independentes para spike+drift."""
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
        groups['ALIGNMENT'] = 1.0 if align_type not in ["NONE", None] else 0.0
        n_act = sum(1 for v in groups.values() if v >= 0.5)
        tot = sum(groups.values())
        ql = "ELITE" if n_act >= 4 else "STRONG" if n_act >= 3 else "MODERATE" if n_act >= 2 else "WEAK"
        return {"n_independent": n_act, "total_strength": round(tot, 1), "groups": groups, "quality": ql}
    except: return {"n_independent": 0, "total_strength": 0, "groups": {}, "quality": "WEAK"}

# ==============================================================================
# V21 PREC #3: OPTIMAL HOLDING PERIOD
# ==============================================================================

def optimal_holding_period(acf_result, setup_type):
    """Calcula tempo otimo de trade baseado no edge decay."""
    try:
        base = {
            "SPIKE_CATCH": 35, "DRIFT_RIDE": 60, "SCALP_DRIFT": 15,
            "POST_SPIKE": 20, "REVERSAL": 40, "STOCH_SPIKE": 30,
        }
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

        # V24-F FIX #6: STRESSED Kelly Criterion
        # Standard Kelly uses avg_loss from backtest, but BC spikes cause
        # catastrophic losses 2-5× the SL. Stress avg_loss by setup risk.
        p = wr / 100
        q = 1 - p
        results = bt_results.get('RESULTS', [])
        wins = [r for r in results if r > 0]
        losses = [abs(r) for r in results if r <= 0]
        avg_win = np.mean(wins) if wins else 1.0
        avg_loss = np.mean(losses) if losses else 1.0

        # FIX #6: Stress avg_loss based on worst-case spike scenario
        # BC_DRIFT: spike contra = 3× normal loss
        # BC_SPIKE: timing wrong = 1.5× normal loss
        # BC_FADE: double spike = 2× normal loss
        is_bc = profile.get('gen_type', 'GBM') in ["BOOM", "CRASH"]
        if is_bc:
            spike_min_atr = profile.get('spike_size_min_atr', 2.0)
            # Stressed avg_loss = max(backtest avg, catastrophic estimate)
            catastrophic_loss = avg_loss * 2.5  # Spike can cause 2.5× avg loss
            stressed_avg_loss = max(avg_loss, catastrophic_loss * 0.6)  # 60% weight to catastrophic
            b = avg_win / stressed_avg_loss if stressed_avg_loss > 0 else 1.0
        else:
            b = avg_win / avg_loss if avg_loss > 0 else 1.0

        kelly = (p * b - q) / b if b > 0 else 0
        kelly = max(0.0, min(kelly, 0.25))
        # DD penalty contínuo
        dd_penalty = max(0.3, 1.0 - dd / 20)
        # Risk multiplier — FIX #6: more conservative for BC
        risk_cap = 0.20 if is_bc else 0.25  # BC max kelly = 20% (not 25%)
        kelly = min(kelly, risk_cap)
        adjusted['risk_mult'] = round(profile['risk_mult'] * (0.5 + kelly * 2) * dd_penalty, 3)
        adjusted['risk_mult'] = max(0.2, min(adjusted['risk_mult'], 2.0 if is_bc else 2.5))
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
            for mult, rp, off, trig in [(1.5, risk_pct*1.5, 0, "MAX CONVICTION"),
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

def smart_tp(entry, direction, risk, base_r1, base_r2):
    """V25: ATR-based TPs — BC-specific."""
    raw_tp1 = entry + base_r1 * risk if direction=="LONG" else entry - base_r1 * risk
    raw_tp2 = entry + base_r2 * risk if direction=="LONG" else entry - base_r2 * risk
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

            # V25: BC-ONLY setups in backtest
            if not sig:
                continue

            # V25: BC-specific slippage (realistic for synthetics)
            slippage_map = {"BC_DRIFT": 0.15, "BC_FADE": 0.8, "BC_SPIKE": 1.5}
            slippage = atr * slippage_map.get(setup, 0.3)
            entry = row['close'] + (spread + slippage if sig == "BUY" else -(spread + slippage))

            # V23 FIX: SL sem look-ahead
            past_data = df.iloc[max(0,i-20):i+1]

            # V25: BC regime-aware SL
            if setup == "BC_DRIFT":
                sl_m = profile.get('sl_scalp_mult', 1.0) * 0.8  # Tight for drift
            elif setup == "BC_FADE":
                sl_m = profile.get('sl_scalp_mult', 1.0) * 1.2  # Wider post-spike
            elif setup == "BC_SPIKE":
                sl_m = profile.get('sl_atr_mult', 1.5) * 1.3  # Widest for spike catch
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

            # V25: BC-only TP configs
            tp_configs = {
                "BC_DRIFT": (1.5, 2.5, 1.0),   # Tight TP, tight trail
                "BC_FADE": (1.2, 2.0, 1.2),     # Conservative fade
                "BC_SPIKE": (3.0, 6.0, 2.5),    # Wide TP for spike catch
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
    bc_score_bonus:float; m5_precision_bonus:float; drift_quality_bonus:float
    alignment_bonus:float; spike_timing_bonus:float; regime_bonus:float
    volume_bonus:float; hurst_bonus:float; zscore_bonus:float
    consecutive_bonus:float; generator_bonus:float; distribution_bonus:float
    vr_bonus:float; acf_bonus:float
    markov_bonus:float; spectral_bonus:float
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

    # V25: BONUS GROUPS — BC-ONLY
    grp_trend = min(20, bonuses.get('ribbon_bonus',0) + bonuses.get('coherence_bonus',0) +
                    bonuses.get('alignment_bonus',0) + bonuses.get('adx_slope_bonus',0))
    grp_stat = min(20, bonuses.get('vr_bonus',0) + bonuses.get('acf_bonus',0) +
                   bonuses.get('hurst_bonus',0))
    # V25: BC-SPECIFIC GROUP (max 28)
    grp_bc = min(28, bonuses.get('bc_score_bonus',0) + bonuses.get('m5_precision_bonus',0) +
                  bonuses.get('drift_quality_bonus',0) + bonuses.get('spike_timing_bonus',0))
    grp_gen = min(12, bonuses.get('generator_bonus',0))
    grp_mom = min(18, bonuses.get('mom_accel_bonus',0) + bonuses.get('candle_bonus',0) +
                  bonuses.get('volume_bonus',0) + bonuses.get('zscore_bonus',0) +
                  bonuses.get('consecutive_bonus',0))
    grp_dist = min(10, bonuses.get('distribution_bonus',0))
    grp_market = min(10, bonuses.get('regime_bonus',0) + bonuses.get('markov_bonus',0) +
                     bonuses.get('spectral_bonus',0))
    # V25: cleaned v23 group
    grp_v23 = min(20, bonuses.get('market_structure_bonus',0) +
                  bonuses.get('sweep_bonus',0) + bonuses.get('entry_sync_bonus',0) +
                  bonuses.get('continuation_bonus',0) + bonuses.get('candle_mom_bonus',0))

    bonus = grp_trend + grp_stat + grp_bc + grp_gen + grp_mom + grp_dist + grp_market + grp_v23
    total=base+bonus
    if total>=190: g="S"
    elif total>=155: g="A++"
    elif total>=125: g="A+"
    elif total>=95: g="A"
    elif total>=65: g="B"
    elif total>=45: g="C"
    else: g="D"

    all_keys=['bc_score_bonus','m5_precision_bonus','drift_quality_bonus',
          'alignment_bonus','spike_timing_bonus','regime_bonus',
          'volume_bonus','hurst_bonus','zscore_bonus','consecutive_bonus',
          'generator_bonus','distribution_bonus','vr_bonus','acf_bonus',
          'markov_bonus','spectral_bonus',
          'adx_slope_bonus','ribbon_bonus','coherence_bonus','candle_bonus','mom_accel_bonus']
    return SetupScore(ts,mp,pattern_score,vs,hs,base,
        *[bonuses.get(k,0) for k in all_keys],bonus,total,g)

# ==============================================================================


# ==============================================================================
# CHART V20
# ==============================================================================

def plot_candles(df, title, entry=None, sl=None, tp1=None, tp2=None):
    """V25: BC-specific chart rendering."""
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

    # V25: BC-only chart rendering

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
        "REGIME_TRANSITION", "BIAS_CONFIDENCE", "BIAS_SCORE",
        "HOLDING_PERIOD", "SCORE_BREAKDOWN",
        "ADX_SLOPE", "EMA_RIBBON", "TREND_COHERENCE", "CANDLE_STRUCTURE",
        "MOM_ACCELERATION", "ATR_CHANNEL",
        # V23 sniper data
        "MKT_STRUCTURE", "CANDLE_MOMENTUM",
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
FUNÇÃO: ANALISTA V25-SCALP — BOOM/CRASH ZERO-ILLUSION SNIPER [Gemini + Fallback]
Missão: Sinais de alta precisão EXCLUSIVOS para Boom e Crash indices da Deriv
APENAS Day Trade + Scalp — SEM Swing Trade — ZERO ILUSÃO — M5 PRECISION

**RESPONDA SEMPRE EM PORTUGUÊS BRASILEIRO**

**REGRAS BOOM/CRASH:**
- BOOM: Preço faz DRIFT para BAIXO e SPIKE para CIMA
  → SELL = seguir o drift (mais seguro, WR 68-75%)
  → BUY = capturar o spike (maior R:R 3-6:1, WR 35-45%)
- CRASH: Preço faz DRIFT para CIMA e SPIKE para BAIXO
  → BUY = seguir o drift (mais seguro, WR 68-75%)
  → SELL = capturar o crash (maior R:R 3-6:1, WR 35-45%)

**ENGINES BC (12 especializados):**
- Spike Detection: Weibull CDF corrigida + kurtosis dinâmica + volume
- Drift Analyzer: força/qualidade drift — count + magnitude
- Post-Spike Fade: trade após spike com validação absorção + recovery speed
- Supply/Demand Zones: níveis institucionais com decay temporal
- Spike Frequency: timing empírico M15
- Stochastic Timer: Stoch + RSI — lookback paramétrico
- Absorption Detector: pressão institucional pós-spike
- Multi-Spike Pattern: clusters — gap tolerance
- BC Regime Classifier: DRIFT_SMOOTH/CHOPPY/PRE_SPIKE/POST_SPIKE/SPIKE_CLUSTER
- Engine Conflict Resolution: SPIKE vs DRIFT, FADE vs CLUSTER, etc.
- M5 Compression Proxy: compressão M5 pré-spike
- Returns Kurtosis: fat-tails = spike-prone regime

**NOVAS FERRAMENTAS TENDÊNCIA V24-F (5):**
- EMA Drift Stack: EMAs 5/10/15/20 empilhadas = drift saudável. Destack = spike proximity.
- Drift Momentum Gradient: aceleração/desaceleração do drift (gradient > 1.2 = seguro, < 0.5 = morto)
- Spike Recovery Speed: velocidade retorno pós-spike (rápido = fade safe, lento = regime change)
- Consecutive Direction Counter: candles consecutivos drift (3-5 = normal, 8+ = overdue)
- Price Channel Position: posição EMA20 ± 1.5×ATR (drift mature vs fresh vs fade zone)

**V25-SCALP: ENGINES M5 PRECISÃO (3):**
- M5 Momentum Pulse: detecta pulsos de drift M5 (STARTING=entry ideal, STRONG=já correu, FADING=sair)
- M5 Micro Structure: padrões M5 (MICRO_PULLBACK, MICRO_CONSOLIDATION, MICRO_BREAKOUT)
- M5 Wicks Analysis: pavios M5 (STRONG_REJECTION=safe, EXHAUSTION=drift exausto)

**BC SCORE:**
- Setups normais: 12 factores, max ~146pts, threshold ≥55
- SCALP_DRIFT: 8 factores M5-específicos, max ~85pts, threshold ≥30
Score factores: spike_timing, drift_health, regime, kurtosis, recovery_absorb,
channel, m5_compression, conflict_penalty, backtest, stochastic,
m5_pulse, m5_structure, m5_wicks (scalp only)

**FORMATO:**

## ⚡ VEREDICTO V24-F: [ {DECISION} ]
**Grade:** {GRADE} | **BC Score:** {BC_SCORE} [{BC_GRADE}] | **Tipo:** {BOOM/CRASH}
**Setup:** {SCALP_DRIFT / DRIFT_RIDE / SPIKE_CATCH / POST_SPIKE / REVERSAL / DAY}
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

### ⚡ M5 SCALP ANALYSIS (quando SCALP_DRIFT)
- M5 Pulse: {STARTING/STRONG/FADING/PAUSED} ({N} candles, str:{X}%)
- M5 Structure: {MICRO_PULLBACK/MICRO_CONSOLIDATION/MICRO_BREAKOUT} ({quality})
- M5 Wicks: {STRONG_REJECTION/EXHAUSTION/NEUTRAL} ({N}/{total})
- Max Hold: {N candles M15 (~Xh)}

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

*V25-BC Insight:* {Analisar especificamente o comportamento Boom/Crash.
Considerar BC Regime para adaptar recomendação.
Se regime PRE_SPIKE e prob > 60%, recomendar spike catch com SL adaptado.
Se DRIFT_SMOOTH e drift forte, recomendar drift ride com SL tight.
Se M5 pulse STARTING + drift active, recomendar SCALP_DRIFT (mais agressivo).
Se POST_SPIKE e absorção confirmada, recomendar fade com target calculado.
Se M5 wicks EXHAUSTION, alertar drift exausto e NÃO entrar scalp.
Se engine conflicts presentes, alertar e ajustar recomendação.
Se expectancy stressed < 0, alertar HIGH RISK.
NUNCA recomendar Swing Trade. Apenas Day Trade e Scalp.
SCALP = SL tighter (0.7×ATR), TP tighter (1.0-1.8R), max hold 10-15 candles M15.
Ser AGRESSIVO mas PRECISO — entrar com convicção.}
"""

# ==============================================================================
# EDGE DETECTION UTILITIES (restored — removed accidentally during V25 cleanup)
# ==============================================================================

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

def trigger_candle_confirmed(df, direction):
    """Verifica se último candle confirma a entrada."""
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

    # ═══ GENERATOR MODEL V20 ═══
    gen_type = profile.get('gen_type', 'GBM')

    # V24-F COHERENCE FIX D: For BC assets, override bias to match DRIFT direction
    # Multi-speed bias uses EMA/MACD which can contradict BC drift direction
    # (e.g. BOOM drifts DOWN but after spike UP, EMAs say BULLISH → wrong bias)
    # PROFILE drift_direction is ALWAYS correct for BC.
    if gen_type in ["BOOM", "CRASH"]:
        profile_drift = profile.get('drift_direction', '')
        if profile_drift == "UP":
            bias = "BULLISH"   # Crash drifts UP → bias must be BULLISH
        elif profile_drift == "DOWN":
            bias = "BEARISH"   # Boom drifts DOWN → bias must be BEARISH
        # Disable early reversal override for BC — drift direction doesn't reverse
        early_reversal = False
        reversal_dir = None
    else:
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

    # ═══ GENERATOR ANALYSIS — BC ONLY ═══
    gen = GeneratorModelV20.analyze_crash_boom(h1, profile, ppy)

    # ═══ EDGE TESTS V20 — BC OPTIMIZED ═══
    # BC assets: neutralize expensive tests that add near-zero value
    is_bc_asset = True  # System is 100% Boom/Crash

    vr = variance_ratio_test(h1['close'])
    acf = autocorrelation_analysis(h1['close'])

    # Neutral defaults — spike+drift process makes these unreliable
    vol_cluster = {"has_clustering": False, "garch_significant": False}
    dist = DistributionAnalyzer.analyze(h1)  # Keep: kurtosis useful for BC
    # V25: BC Predictability via regime + kurtosis + spike frequency
    spectral = {"has_cycle": False, "cycles": [], "spectral_edge": 0}
    markov = {"has_dependence": False, "transition_edge": 0, "matrix": {},
              "p_reversal_up": 0.33, "p_reversal_down": 0.33,
              "p_momentum_up": 0.33, "p_momentum_down": 0.33}
    regime_transition, rt_mult, rt_detail = detect_regime_transition(h1)

    # ═══ CLASSIC STATS ═══
    hurst_val, hurst_regime, hurst_r2 = calculate_hurst_exponent(h1['close'])
    z_current = float(cm['ZSCORE']) if pd.notna(cm.get('ZSCORE')) else 0
    bb_cycle, bb_ratio, bb_squeeze_count = detect_bb_cycle(h1, profile)
    consec_count, consec_dir = count_consecutive(m15)
    roc_status, roc_details = detect_roc_extreme(m15, profile)

    # ═══ V21+ PRECISION ENGINES — BC ADAPTED ═══
    adx_slope = adx_slope_analysis(h1)  # Keep: ADX still measures drift strength
    ema_ribbon = ema_ribbon_analysis(h1)  # Keep: EMA alignment useful for drift
    trend_coherence = multi_tf_trend_coherence(h4, h1, m15, m5)  # Keep: TF alignment

    candle_struct = candle_structure_score(m15, bias)
    mom_accel = momentum_acceleration(h1)
    atr_channel = atr_channel_entry(h1, bias)

    # ═══ V23 SNIPER ENGINES ═══
    mkt_struct = detect_market_structure(h1)
    candle_mom = candle_momentum_engine(m15, bias, lookback=10)

    liq_sweep = detect_liquidity_sweep(m15, c1['ATR'])
    entry_sync = entry_sync_score(h4, h1, m15, m5, bias)
    # V24-F: Skip continuation pattern for BC (redundant with drift_analyzer + gradient)
    if gen_type in ["BOOM", "CRASH"]:
        cont_pattern = {"pattern": "NONE", "confidence": 0}
    else:
        cont_pattern = detect_continuation_pattern(m15, bias, c1['ATR'])

    # ═══ V24-F BOOM/CRASH ENGINES ═══
    # FIX #2: Use clean ATR for all BC engines
    bc_atr_clean = bc_clean_atr(m15, profile, lookback=50)
    # FIX #14: Kurtosis calculated FIRST, fed to spike detector for dynamic shape
    bc_kurt = bc_returns_kurtosis(m15, lookback=50)
    # FIX #1+#14+#15: Spike detector with corrected Weibull + kurtosis + volume
    bc_spike = bc_spike_detector(m15, profile, lookback=30, bc_kurt_data=bc_kurt)
    bc_drift = bc_drift_analyzer(m15, profile, lookback=20)
    # V24 FIX #8: Pass absorption data to fade engine
    bc_absorb = bc_absorption_detector(m15, bias, lookback=10)
    bc_fade = bc_post_spike_fade(m15, profile, lookback=10, absorption_data=bc_absorb)
    bc_sd = bc_supply_demand_zones(h1, bc_atr_clean, lookback=50)
    bc_freq = bc_spike_frequency(m15, profile, lookback=100)
    bc_multi = bc_multi_spike_pattern(m15, profile, lookback=30)
    bc_stoch = bc_stochastic_timer(m15, profile)
    # V24-F FIX #7: M5 Compression Proxy
    bc_compress = bc_m5_compression(m5, bc_atr_clean, lookback_candles=10)
    # V24 M5: BC Regime classifier
    bc_regime = bc_regime_classifier(m15, profile, bc_spike, bc_drift, bc_freq)
    # V24 O3: Engine conflict resolution
    bc_conflicts = bc_resolve_engine_conflicts(bc_spike, bc_drift, bc_fade, bc_multi, bc_absorb)
    # V24-F NEW TOOLS: 5 BC-specific trend + timing tools
    bc_ema_stack = bc_ema_drift_stack(m15, profile, lookback=20)
    bc_gradient = bc_drift_momentum_gradient(m15, profile, lookback=15)
    bc_recovery = bc_spike_recovery_speed(m15, profile, lookback=15)
    bc_consec = bc_consecutive_drift_counter(m15, profile, lookback=20)
    bc_channel = bc_price_channel_position(m15, profile, lookback=20)
    # V25-SCALP: M5 precision engines for scalp timing
    bc_m5_pulse = bc_m5_momentum_pulse(m5, profile, lookback=15)
    bc_m5_struct = bc_m5_micro_structure(m5, profile, lookback=20)
    bc_m5_wicks = bc_m5_wicks_analysis(m5, profile, lookback=10)


    align_type, align_bonus = detect_alignment(c4, c1, cm, bias)
    vol_bonus = 0  # Synthetics have no real volume
    regime_bonus = 5 if "TRENDING" in regime else 0
    pat_score = min(cm.get('pattern_score', 0), 15)
    bb_compression = bb_cycle == "SQUEEZE"

    # ═══ V25: BC GENERATOR BONUS ═══
    gen_bonus = 0; gen_signal = gen.get('signal', 'NEUTRAL')
    if gen.get('spike_phase') in ["DRIFT_STRONG", "DRIFT_NORMAL"]:
        gen_bonus = min(int(gen.get('decay_strength', 0) * 8), 12)

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


    # V21: Markov bonus
    markov_bonus = 0
    if markov.get('has_dependence'): markov_bonus = min(int(markov.get('transition_edge',0) / 2), 8)

    # V21: Spectral bonus
    spectral_bonus = 0
    if spectral.get('has_cycle'): spectral_bonus = min(int(spectral.get('spectral_edge',0) * 2), 8)
    acf_bonus = 0
    if acf.get('has_pattern'): acf_bonus = min(len(acf.get('significant_lags',[]))*3, 10)

    # ═══ V25: BC-SPECIFIC BONUSES ═══
    # BC Score bonus: regime quality + kurtosis + recovery + stack health
    bc_score_bonus = 0
    if bc_regime.get('regime') in ['DRIFT_SMOOTH']:
        bc_score_bonus += 5  # Best regime for trading
    elif bc_regime.get('regime') in ['PRE_SPIKE']:
        bc_score_bonus += 3  # Good for spike catch
    if bc_kurt.get('regime') in ['SPIKE_PRONE', 'EXTREME_SPIKE']:
        bc_score_bonus += 2  # Fat tails = spike opportunity
    if bc_ema_stack.get('stack_quality') in ['PERFECT', 'GOOD']:
        bc_score_bonus += 3  # EMA alignment healthy
    if bc_recovery.get('fade_safe'):
        bc_score_bonus += 2  # Safe to trade after spike

    # M5 Precision bonus: M5 pulse + structure + wicks alignment
    m5_precision_bonus = 0
    if bc_m5_pulse.get('optimal_entry'):
        m5_precision_bonus += 5
    elif bc_m5_pulse.get('pulse_active'):
        m5_precision_bonus += 2
    if bc_m5_struct.get('entry_window'):
        m5_precision_bonus += 4
    if bc_m5_wicks.get('signal') in ['STRONG_REJECTION', 'MODERATE_REJECTION']:
        m5_precision_bonus += 3
    elif bc_m5_wicks.get('signal') in ['EXHAUSTION', 'WEAK_EXHAUSTION']:
        m5_precision_bonus -= 4  # Penalty: drift exhausted

    # Drift Quality bonus: drift strength + quality + gradient alignment
    drift_quality_bonus = 0
    if bc_drift.get('drift_active'):
        drift_str = bc_drift.get('strength', 0)
        drift_q = bc_drift.get('quality', 'CHOPPY')
        if drift_str >= 70 and drift_q == 'SMOOTH': drift_quality_bonus = 10
        elif drift_str >= 50 and drift_q in ['SMOOTH', 'MODERATE']: drift_quality_bonus = 7
        elif drift_str >= 30: drift_quality_bonus = 4
        # Gradient amplifier
        if bc_gradient.get('phase') == 'ACCELERATING': drift_quality_bonus += 3
        elif bc_gradient.get('phase') == 'DYING': drift_quality_bonus -= 3
        drift_quality_bonus = max(0, drift_quality_bonus)

    # Spike Timing bonus: spike probability + consecutive count + Weibull
    spike_timing_bonus = 0
    if bc_spike.get('spike_imminent') and bc_spike.get('probability', 0) >= 60:
        spike_timing_bonus = 8
    elif bc_spike.get('probability', 0) >= 40:
        spike_timing_bonus = 4
    # Consecutive count risk (overdue for spike = risky for drift, good for spike catch)
    if bc_consec.get('zone') == 'DANGER':
        spike_timing_bonus += 3  # Good for spike catch
    elif bc_consec.get('zone') == 'EXTENDED':
        spike_timing_bonus += 1

    # ═══ V21+ PRECISION BONUSES ═══
    # V25: Trend bonuses use BC engines
    adx_slope_bonus = 0
    ribbon_bonus = 0
    coherence_bonus = 0

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


    # V25: RANDOM WALK PENALTY (kept — valid for all stochastic processes)
    random_walk_penalty = 0
    if 0.47 <= hurst_val <= 0.53 and hurst_r2 >= 0.7:
        random_walk_penalty = -20  # Honest: no edge in random walk


    # ═══ 🔴 FIX #5: BACKTEST 1× (não 2×) + V20 multi-setup ═══
    sim = run_walk_forward_v21(h1, bias, profile, n_folds=4)

    # ADAPTIVE (usa resultado do único backtest)
    adapted_profile = AdaptiveLearnerV20.adjust_profile(profile, sim, dist)

    # 🔴 FIX #6: Monte Carlo REAL
    mc = monte_carlo_bootstrap(sim.get('RESULTS', []))

    # ═══ SETUP DETECTION V25 — BC-ONLY ═══
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
        is_bc = gen_type in ["BOOM", "CRASH"]

        # ═══ V25: BC PRIORITY SETUPS ═══
        # BC engines are the sole authority on BC assets.

        # V24 M5: Regime-aware SL multiplier
        regime_sl_mult = bc_regime.get('sl_mult', 1.0) if is_bc else 1.0

        # BC-0: POST-SPIKE FADE (highest priority — time sensitive)
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
        if is_bc and bc_spike.get('spike_imminent') and bc_spike.get('probability', 0) >= 50 \
                and bc_conflicts.get('allow_spike_catch', True):
            is_boom = gen_type == "BOOM"
            if is_boom and is_long:  # Boom spike UP → BUY
                sig = "LONG (SPIKE CATCH)"
                sl_val = entry - profile.get('sl_atr_mult', 1.5) * bc_atr_clean * regime_sl_mult
                entry_type = f"Spike UP {bc_spike['probability']}% | Weibull:{bc_spike.get('weibull_prob',0):.0%} | Consec:{bc_consec.get('count',0)} | Grad:{bc_gradient.get('gradient',1):.2f}"
                trade_style = "DAY"; setup_type = "SPIKE_CATCH"
                return
            elif not is_boom and not is_long:  # Crash spike DOWN → SELL
                sig = "SHORT (SPIKE CATCH)"
                sl_val = entry + profile.get('sl_atr_mult', 1.5) * bc_atr_clean * regime_sl_mult
                entry_type = f"Crash DOWN {bc_spike['probability']}% | Weibull:{bc_spike.get('weibull_prob',0):.0%} | Consec:{bc_consec.get('count',0)} | Grad:{bc_gradient.get('gradient',1):.2f}"
                trade_style = "DAY"; setup_type = "SPIKE_CATCH"
                return

        # BC-1.5: SCALP DRIFT (aggressive micro-drift — M5 timed, tight SL)
        # More aggressive than DRIFT_RIDE: lower strength threshold (25 vs 40)
        # BUT requires M5 pulse confirmation + stack + gradient + wick safety
        if is_bc and bc_drift.get('drift_active') and bc_drift.get('strength', 0) >= 25 \
                and bc_conflicts.get('allow_drift_ride', True):
            m5_pulse_ok = bc_m5_pulse.get('optimal_entry', False)
            m5_struct_ok = bc_m5_struct.get('entry_window', False)
            stack_ok = bc_ema_stack.get('pairs_ok', 0) >= 2
            gradient_ok = bc_gradient.get('gradient', 0) >= 0.8
            wick_safe = bc_m5_wicks.get('signal') not in ['EXHAUSTION', 'WEAK_EXHAUSTION']
            spike_safe = bc_consec.get('spike_risk', 0) < 70

            # Need at least: (M5 pulse OR M5 structure) + stack + gradient + wick + spike safety
            m5_confirmed = m5_pulse_ok or m5_struct_ok
            if m5_confirmed and stack_ok and gradient_ok and wick_safe and spike_safe:
                is_boom = gen_type == "BOOM"
                # Adaptive SL: tightens with spike proximity
                spike_proximity = bc_consec.get('spike_risk', 0) / 100.0
                scalp_sl_mult = profile.get('sl_scalp_mult', 1.0) * 0.7 * (1.0 - spike_proximity * 0.25)
                scalp_sl_mult = max(0.4, scalp_sl_mult)  # Floor: never less than 0.4× ATR

                if is_boom and not is_long:  # Boom drift DOWN → SELL scalp
                    sig = "SHORT (SCALP DRIFT)"
                    sl_val = entry + scalp_sl_mult * bc_atr_clean * regime_sl_mult
                    m5_info = f"Pulse:{bc_m5_pulse.get('pulse_phase','?')}" if m5_pulse_ok else f"Struct:{bc_m5_struct.get('pattern','?')}"
                    entry_type = f"M5 Scalp | {m5_info} | Str:{bc_drift['strength']}% Stack:{bc_ema_stack.get('stack_quality','?')} Grad:{bc_gradient.get('gradient',1):.2f} Wicks:{bc_m5_wicks.get('signal','?')}"
                    trade_style = "SCALP"; setup_type = "SCALP_DRIFT"
                    return
                elif not is_boom and is_long:  # Crash drift UP → BUY scalp
                    sig = "LONG (SCALP DRIFT)"
                    sl_val = entry - scalp_sl_mult * bc_atr_clean * regime_sl_mult
                    m5_info = f"Pulse:{bc_m5_pulse.get('pulse_phase','?')}" if m5_pulse_ok else f"Struct:{bc_m5_struct.get('pattern','?')}"
                    entry_type = f"M5 Scalp | {m5_info} | Str:{bc_drift['strength']}% Stack:{bc_ema_stack.get('stack_quality','?')} Grad:{bc_gradient.get('gradient',1):.2f} Wicks:{bc_m5_wicks.get('signal','?')}"
                    trade_style = "SCALP"; setup_type = "SCALP_DRIFT"
                    return

        # BC-2: DRIFT RIDE (follow the natural drift — safest)
        if is_bc and bc_drift.get('safe_to_ride') and bc_drift.get('strength', 0) >= 40 \
                and bc_conflicts.get('allow_drift_ride', True):
            is_boom = gen_type == "BOOM"
            if is_boom and not is_long:  # Boom drifts DOWN → SELL
                sig = "SHORT (DRIFT RIDE)"
                sl_val = entry + profile.get('sl_scalp_mult', 1.0) * bc_atr_clean * regime_sl_mult
                entry_type = f"Drift DOWN str={bc_drift['strength']}% q={bc_drift['quality']} Stack:{bc_ema_stack.get('stack_quality','?')} Grad:{bc_gradient.get('gradient',1):.2f}"
                trade_style = "SCALP" if bc_drift['strength'] < 60 else "DAY"
                setup_type = "DRIFT_RIDE"
                return
            elif not is_boom and is_long:  # Crash drifts UP → BUY
                sig = "LONG (DRIFT RIDE)"
                sl_val = entry - profile.get('sl_scalp_mult', 1.0) * bc_atr_clean * regime_sl_mult
                entry_type = f"Drift UP str={bc_drift['strength']}% q={bc_drift['quality']} Stack:{bc_ema_stack.get('stack_quality','?')} Grad:{bc_gradient.get('gradient',1):.2f}"
                trade_style = "SCALP" if bc_drift['strength'] < 60 else "DAY"
                setup_type = "DRIFT_RIDE"
                return

        # BC-3: STOCHASTIC SPIKE TIMER (confirmed signal)
        # FIX #2: Use bc_atr_clean instead of c1['ATR']
        if is_bc and bc_stoch.get('ready'):
            stoch_sig = bc_stoch['signal']
            if stoch_sig == "SPIKE_BUY" and is_long:
                sig = "LONG (STOCH SPIKE)"
                sl_val = entry - profile.get('sl_atr_mult', 1.5) * bc_atr_clean * regime_sl_mult
                entry_type = f"Stoch K={bc_stoch['stoch_k']:.0f} RSI={bc_stoch.get('rsi',50):.0f} → SPIKE BUY"
                trade_style = "DAY"; setup_type = "SPIKE_CATCH"
                return
            elif stoch_sig == "SPIKE_SELL" and not is_long:
                sig = "SHORT (STOCH CRASH)"
                sl_val = entry + profile.get('sl_atr_mult', 1.5) * bc_atr_clean * regime_sl_mult
                entry_type = f"Stoch K={bc_stoch['stoch_k']:.0f} RSI={bc_stoch.get('rsi',50):.0f} → CRASH SELL"
                trade_style = "DAY"; setup_type = "SPIKE_CATCH"
                return
            elif stoch_sig == "DRIFT_SELL" and not is_long:
                sig = "SHORT (STOCH DRIFT)"
                sl_val = entry + profile.get('sl_scalp_mult', 1.0) * bc_atr_clean * regime_sl_mult
                entry_type = f"Stoch K={bc_stoch['stoch_k']:.0f} RSI={bc_stoch.get('rsi',50):.0f} → DRIFT SELL"
                trade_style = "SCALP"; setup_type = "DRIFT_RIDE"
                return
            elif stoch_sig == "DRIFT_BUY" and is_long:
                sig = "LONG (STOCH DRIFT)"
                sl_val = entry - profile.get('sl_scalp_mult', 1.0) * bc_atr_clean * regime_sl_mult
                entry_type = f"Stoch K={bc_stoch['stoch_k']:.0f} RSI={bc_stoch.get('rsi',50):.0f} → DRIFT BUY"
                trade_style = "SCALP"; setup_type = "DRIFT_RIDE"
                return

        # BC-4: REVERSAL (CHoCH + absorption + supply/demand)
        if is_bc and mkt_struct.get('choch'):
            choch_bull = "BULL" in str(mkt_struct.get('last_event', ''))
            choch_bear = "BEAR" in str(mkt_struct.get('last_event', ''))
            if choch_bull and is_long and bc_absorb.get('absorption'):
                sig = "LONG (REVERSAL)"
                sl_val = entry - profile.get('sl_atr_mult', 1.5) * bc_atr_clean * regime_sl_mult
                entry_type = f"CHoCH Bull + Absorption ({bc_absorb.get('strength',0):.0f}%)"
                trade_style = "DAY"; setup_type = "REVERSAL"
                return
            elif choch_bear and not is_long and bc_absorb.get('absorption'):
                sig = "SHORT (REVERSAL)"
                sl_val = entry + profile.get('sl_atr_mult', 1.5) * bc_atr_clean * regime_sl_mult
                entry_type = f"CHoCH Bear + Absorption ({bc_absorb.get('strength',0):.0f}%)"
                trade_style = "DAY"; setup_type = "REVERSAL"
                return

        # ═══ V25: BC-ONLY SETUPS ═══
        # All BC setups handled above (POST_SPIKE, SPIKE_CATCH, SCALP_DRIFT,
        # DRIFT_RIDE, STOCH_SPIKE, REVERSAL). If none triggered → MONITORING.
        return  # sig remains "MONITORING" — honest and correct

    # V24 FIX #5: For Crash/Boom: try BOTH drift and spike directions
    # V24-F COHERENCE FIX: Use PROFILE directions (source of truth), not generator
    # Generator can give wrong drift_dir post-spike (e.g. "UP" for BOOM after strong spike)
    if gen_type in ["BOOM","CRASH"]:
        # PROFILE directions are ALWAYS correct: BOOM=drift DOWN/spike UP, CRASH=drift UP/spike DOWN
        profile_drift_dir = profile.get('drift_direction', '')
        profile_spike_dir = profile.get('spike_direction', '')

        # Primary: Try drift direction first (safest, highest WR)
        if profile_drift_dir == "UP": try_setup("BULLISH")
        elif profile_drift_dir == "DOWN": try_setup("BEARISH")

        # If no signal from drift, try spike direction
        if sig == "MONITORING":
            if profile_spike_dir == "UP": try_setup("BULLISH")
            elif profile_spike_dir == "DOWN": try_setup("BEARISH")

        # NO fallback to bias — bias can contradict BC directions
    else:
        try_setup(bias)

    # V24 O3: Apply conflict penalty to effective score
    conflict_penalty = bc_conflicts.get('conflict_penalty', 0) if gen_type in ["BOOM", "CRASH"] else 0

    # ═══ V21+ ENTRY REFINEMENT ═══
    # ═══ V25: BC ENTRY REFINEMENT ═══
    if "LONG" in sig or "SHORT" in sig:
        # BC entry refinement: use price channel position for better timing
        ch_pos = bc_channel.get('position_pct', 50)
        if setup_type == "DRIFT_RIDE":
            entry_type = f"{entry_type} | Ch:{bc_channel.get('position','?')}({ch_pos:.0f}%)"
        elif setup_type == "SPIKE_CATCH":
            entry_type = f"{entry_type} | Ch:{bc_channel.get('position','?')}({ch_pos:.0f}%)"
        elif setup_type == "POST_SPIKE":
            entry_type = f"{entry_type} | Rec:{bc_recovery.get('recovery_phase','?')}"
        elif setup_type == "SCALP_DRIFT":
            entry_type = f"{entry_type} | Pulse:{bc_m5_pulse.get('pulse_phase','?')}"

    # Spread
    if "LONG" in sig: entry += profile['spread']
    elif "SHORT" in sig: entry -= profile['spread']

    # Clamp SL — Always use clean ATR (spike-filtered) for BC synthetics
    if "LONG" in sig and (entry - sl_val) > adapted_profile['sl_atr_mult'] * bc_atr_clean:
        sl_val = entry - adapted_profile['sl_atr_mult'] * bc_atr_clean
    elif "SHORT" in sig and (sl_val - entry) > adapted_profile['sl_atr_mult'] * bc_atr_clean:
        sl_val = entry + adapted_profile['sl_atr_mult'] * bc_atr_clean

    # V25: Independent Edge Correlation
    indep_edges = calculate_independent_edges(
        vr, acf, hurst_val, gen_bonus, dist, z_current, align_type)

    score = calculate_score(
        adx=adx, momentum_score=momentum, pattern_score=pat_score,
        dist_ema50=abs(c1['close']-c1['EMA_50']), atr=c1['ATR'],
        win_rate=sim['WR'], profit_factor=sim['PF'], profile=adapted_profile,
        # V25: BC-specific bonuses
        bc_score_bonus=bc_score_bonus, m5_precision_bonus=m5_precision_bonus,
        drift_quality_bonus=drift_quality_bonus, spike_timing_bonus=spike_timing_bonus,
        alignment_bonus=align_bonus,
        regime_bonus=regime_bonus, volume_bonus=vol_bonus,
        hurst_bonus=hurst_bonus, zscore_bonus=zscore_bonus,
        consecutive_bonus=consecutive_bonus, generator_bonus=gen_bonus,
        distribution_bonus=dist_bonus, vr_bonus=vr_bonus, acf_bonus=acf_bonus,
        markov_bonus=markov_bonus, spectral_bonus=spectral_bonus,
        adx_slope_bonus=adx_slope_bonus, ribbon_bonus=ribbon_bonus,
        coherence_bonus=coherence_bonus, candle_bonus=candle_bonus,
        mom_accel_bonus=mom_accel_bonus,
        # V23 bonuses (cleaned)
        market_structure_bonus=market_structure_bonus,
        candle_mom_bonus=candle_mom_bonus,
        sweep_bonus=sweep_bonus, entry_sync_bonus=entry_sync_bonus,
        continuation_bonus=continuation_bonus)

    # Filters — V24-F: BC Score as PRIMARY gate for BC setups
    # ═══ V25: BC-ONLY FILTER CONFIGS (threshold, min_pf) ═══
    configs = {
        "SPIKE_CATCH": (30, 0.8),    # Aggressive — time-sensitive
        "DRIFT_RIDE": (25, 0.8),     # Moderate — steady drift
        "SCALP_DRIFT": (20, 0.7),    # Loose — tight SL compensates
        "POST_SPIKE": (20, 0.7),     # Loose — high R:R fade
        "REVERSAL": (40, 1.0),       # Strict — structural change
        "STOCH_SPIKE": (30, 0.8),    # Moderate — timer signal
    }
    ms, mpf = configs.get(setup_type, (30, 0.8))
    is_bc_setup = setup_type in configs

    # FIX #8: Calculate BC Score for BC setups
    bc_score_data = {"score": 0, "grade": "D", "status": "FAIL"}
    if is_bc_setup:
        bc_score_data = calculate_bc_score(
            setup_type, bc_spike, bc_drift, bc_regime, bc_kurt,
            bc_freq, bc_absorb, bc_compress, bc_conflicts,
            bc_stoch, sim_results=sim,
            bc_ema_stack=bc_ema_stack, bc_gradient=bc_gradient,
            bc_recovery=bc_recovery, bc_consec=bc_consec,
            bc_channel=bc_channel,
            bc_m5_pulse=bc_m5_pulse, bc_m5_struct=bc_m5_struct,
            bc_m5_wicks=bc_m5_wicks)

    # Score override — BC uses TF coherence + ribbon for quality boost
    if trend_coherence.get('coherence') == "PERFECT" and ema_ribbon.get('quality') == "EXCELLENT":
        ms = int(ms * 0.80)
    if sim['WR'] > 65 and sim['PF'] > 1.8:
        ms = int(ms * 0.85)

    # V24 FIX #11: Floor
    ms = max(ms, 15)

    # V24-F O5: Anti-Meltdown Kill-Switch (FUNCTIONAL)
    meltdown = bc_meltdown_check()
    if meltdown.get('blocked'):
        sig = f"BLOCKED ({meltdown['reason']})"
    elif meltdown.get('score_boost', 0) > 0:
        ms = int(ms * (1 + meltdown['score_boost'] / 100))

    # V24-F: Gradient DYING blocks drift ride AND scalp drift
    if is_bc_setup and setup_type in ["DRIFT_RIDE", "SCALP_DRIFT"]:
        if bc_gradient.get('phase') == "DYING":
            sig = f"BLOCKED (DRIFT DYING — gradient {bc_gradient.get('gradient',0):.2f} — spike iminente)"
        elif bc_consec.get('zone') in ["EXTREME_OVERDUE", "OVERDUE"]:
            sig = f"BLOCKED (DRIFT OVERDUE — {bc_consec.get('count',0)} candles consecutivos)"

    # V24-F: M5 compression blocks scalp drift (spike imminent)
    if is_bc_setup and bc_compress.get('block_scalp', False) and setup_type in ["DRIFT_RIDE", "SCALP_DRIFT"]:
        sig = f"BLOCKED (M5 COMPRESSION {bc_compress.get('compression','?')} — spike proximity)"

    # V25-SCALP: M5 exhaustion blocks scalp
    if is_bc_setup and setup_type == "SCALP_DRIFT":
        if bc_m5_wicks.get('signal') in ['EXHAUSTION', 'WEAK_EXHAUSTION']:
            sig = f"BLOCKED (M5 WICKS EXHAUSTION — drift exausto)"

    # V24-F: Recovery blocks unsafe fade
    if is_bc_setup and setup_type == "POST_SPIKE":
        if bc_recovery.get('has_recent_spike') and not bc_recovery.get('fade_safe', False):
            phase = bc_recovery.get('recovery_phase', 'NONE')
            if phase in ["STALLED", "JUST_SPIKED"]:
                sig = f"BLOCKED (RECOVERY {phase} — fade unsafe)"

    if "BLOCKED" not in sig and sig != "MONITORING":
        fails = []

        if is_bc_setup:
            # FIX #9 + COHERENCE FIX C: BC setups filtered ONLY by BC SCORE
            bc_score_val = bc_score_data.get('score', 0)
            # V25-SCALP: SCALP_DRIFT uses lower threshold (30) — compensated by tight SL
            if setup_type == "SCALP_DRIFT":
                bc_min = 30
            else:
                bc_min = 55  # Standard BC minimum
            if meltdown.get('score_boost', 0) > 0:
                bc_min = int(bc_min * 1.5)  # 50% higher during loss streak

            if bc_score_val < bc_min:
                fails.append(f"BC_SCORE={bc_score_val}<{bc_min}")

            # BC: NET relaxed (allow NET down to -5 instead of 0)
            if sim['NET'] < -5:
                fails.append(f"NET={sim['NET']:.0f}<-5")

            # FIX #10: Entry Sync bypass for SPIKE_CATCH, POST_SPIKE, and SCALP_DRIFT
            # SCALP_DRIFT uses M5 timing instead of TF alignment
            if setup_type in ["DRIFT_RIDE", "REVERSAL"]:
                if entry_sync.get('ready') == "WAIT":
                    if entry_sync.get('score', 0) < 40:
                        fails.append(f"SYNC={entry_sync.get('score',0)}<40")
            # SPIKE_CATCH, POST_SPIKE, SCALP_DRIFT: NO entry sync check

        if fails: sig = f"BLOCKED ({', '.join(fails)})"

    # ═══ V25 CROSS-VALIDATION: DIRECTION SANITY CHECK ═══
    # Verify signal direction is LOGICALLY POSSIBLE for this BC asset
    if "BLOCKED" not in sig and sig != "MONITORING":
        is_boom = gen_type == "BOOM"
        sig_is_long = "LONG" in sig

        # Define valid direction-setup combinations
        # BOOM: LONG only valid for SPIKE_CATCH, REVERSAL, STOCH_SPIKE
        # BOOM: SHORT valid for DRIFT_RIDE, SCALP_DRIFT, POST_SPIKE, STOCH_DRIFT
        # CRASH: SHORT only valid for SPIKE_CATCH, REVERSAL, STOCH_CRASH
        # CRASH: LONG valid for DRIFT_RIDE, SCALP_DRIFT, POST_SPIKE, STOCH_DRIFT
        valid = True
        reason = ""

        if is_boom:
            if sig_is_long and setup_type in ["DRIFT_RIDE", "SCALP_DRIFT"]:
                valid = False
                reason = f"BOOM LONG+{setup_type} impossível (Boom drift=DOWN→SHORT)"
            elif not sig_is_long and setup_type in ["SPIKE_CATCH"]:
                valid = False
                reason = f"BOOM SHORT+SPIKE_CATCH impossível (Boom spike=UP→LONG)"
        else:  # CRASH
            if not sig_is_long and setup_type in ["DRIFT_RIDE", "SCALP_DRIFT"]:
                valid = False
                reason = f"CRASH SHORT+{setup_type} impossível (Crash drift=UP→LONG)"
            elif sig_is_long and setup_type in ["SPIKE_CATCH"]:
                valid = False
                reason = f"CRASH LONG+SPIKE_CATCH impossível (Crash spike=DOWN→SHORT)"

        if not valid:
            sig = f"BLOCKED (INCOERÊNCIA: {reason})"

    # ═══ V25: BC-ONLY TP CONFIGS ═══
    risk = abs(entry - sl_val)
    if risk == 0: risk = float(c1['ATR'])
    tc = {
        # BC setup types only
        "SPIKE_CATCH": (3.0, 6.0),    # Wide — catching a spike
        "DRIFT_RIDE": (1.5, 2.5),     # Medium — riding steady drift
        "SCALP_DRIFT": (1.0, 1.8),    # Tight — M5 micro-drift
        "POST_SPIKE": (1.2, 2.0),     # Medium — fade after spike
        "REVERSAL": (2.5, 4.0),       # Wide — structural change
        "STOCH_SPIKE": (2.0, 3.5),    # Medium-wide — timer signal
    }
    r1, r2 = tc.get(setup_type, (adapted_profile['tp1_r'], adapted_profile['tp2_r']))

    # V25: BC Regime-Aware TP (matches SL regime multiplier)
    regime_tp_mults = {
        "DRIFT_SMOOTH": 0.9,   # Tight TP — predictable
        "CHOPPY": 0.8,         # Very tight — unreliable
        "PRE_SPIKE": 1.2,      # Wider — spike coming
        "POST_SPIKE": 1.3,     # Wider — high vol recovery
        "SPIKE_CLUSTER": 1.5,  # Widest — big moves
    }
    bc_regime_name = bc_regime.get('regime', 'UNKNOWN')
    regime_tp_mult = regime_tp_mults.get(bc_regime_name, 1.0)
    r1 *= regime_tp_mult
    r2 *= regime_tp_mult

    # V24-F: Gradient-aware TP adjustment for DRIFT_RIDE
    if setup_type == "DRIFT_RIDE":
        grad_phase = bc_gradient.get('phase', 'STABLE')
        if grad_phase == "ACCELERATING":
            r1 *= 1.15; r2 *= 1.2  # Drift strong → wider TP
        elif grad_phase == "DECELERATING":
            r1 *= 0.85; r2 *= 0.8  # Drift weakening → tighter TP

    # V25-SCALP: TP adjustment for SCALP_DRIFT based on M5 pulse + drift quality
    if setup_type == "SCALP_DRIFT":
        # Drift quality bonus
        if bc_drift.get('quality') == 'SMOOTH':
            r1 *= 1.15; r2 *= 1.2
        # M5 pulse strength bonus
        pulse_str = bc_m5_pulse.get('pulse_strength', 0)
        if pulse_str > 70:
            r1 *= 1.1; r2 *= 1.15  # Strong pulse → wider TP
        # Gradient bonus
        grad_phase = bc_gradient.get('phase', 'STABLE')
        if grad_phase == "ACCELERATING":
            r1 *= 1.1; r2 *= 1.15

    # V24-F: Consecutive-aware TP for SPIKE_CATCH
    if setup_type == "SPIKE_CATCH":
        consec_count = bc_consec.get('count', 0)
        if consec_count >= 10:
            r1 *= 1.3; r2 *= 1.4  # Very overdue → expect bigger spike
        elif consec_count >= 7:
            r1 *= 1.15; r2 *= 1.2  # Moderately overdue

    direction = "LONG" if "LONG" in sig else "SHORT"
    tp1, tp2 = smart_tp(entry, direction, risk, r1, r2)

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

    show = any(x in sig for x in ["DRIFT","SPIKE","SCALP","FADE","REVERSAL","STOCH"])

    imgs = [
        plot_candles(h4.tail(150), f"{name} H4 — {regime} | Gen:{gen_signal}", entry if show else None, sl_val if show else None, tp1 if show else None, tp2 if show else None),
        plot_candles(h1.tail(200), f"{name} H1 — H:{hurst_val} Z:{z_current:.1f} σ:{sigma_calibrated or 0:.3f}", entry if show else None, sl_val if show else None, tp1 if show else None, tp2 if show else None),
        plot_candles(m15.tail(200), f"{name} M15 — BB:{bb_cycle} VR:{vr.get('dominant_type','?')} ACF:{acf.get('dominant_type','?')}", entry if show else None, sl_val if show else None, tp1 if show else None, tp2 if show else None),
    ]

    # V21: Optimal holding
    hold = optimal_holding_period(acf, setup_type)

    confs = []
    if markov.get('has_dependence'): confs.append(f"\U0001f52e Markov: {markov['best_transition']}")
    if spectral.get('has_cycle'): confs.append(f"\U0001f4c8 Cycle: {spectral['dominant_period']:.0f} bars")
    if rt_detail: confs.append(f"\U0001f504 {regime_transition}: {rt_detail}")
    if gen_bonus>0: confs.append(f"🧮 Gen: {gen_signal} (+{gen_bonus})")
    if vr.get('has_edge'): confs.append(f"📐 VR: {vr['dominant_type']} ({vr.get('n_significant',0)} sig)")
    if acf.get('has_pattern'): confs.append(f"📊 ACF: {acf['dominant_type']} (lag-1={acf.get('acf_1',0):.3f})")
    if vol_cluster.get('has_clustering'): confs.append(f"🔥 VolCluster: {vol_cluster['vol_regime']}")
    if dist_favorable: confs.append(f"📊 Dist P{dist['percentile']:.0f}")
    if align_type!="NONE": confs.append(f"⭐ Align {align_type}")
    # Confluences — BC-specific
    if hurst_trending: confs.append(f"🧬 Hurst {hurst_val}")
    if zscore_favorable: confs.append(f"📊 Z {z_current:.1f}")
    if bb_compression: confs.append("💥 BB Squeeze")
    if trigger_ok and trigger_type!="N/A": confs.append(f"✅ Trigger: {trigger_type}")
    # V25: BC-specific confluences
    if drift_quality_bonus >= 7: confs.append(f"🌊 Drift Q: {bc_drift.get('quality','?')} ({bc_drift.get('strength',0)}%)")
    if spike_timing_bonus >= 4: confs.append(f"⚡ Spike Timing (prob:{bc_spike.get('probability',0)}%)")
    if m5_precision_bonus >= 5: confs.append(f"🎯 M5 Precision ({bc_m5_pulse.get('pulse_phase','?')})")
    if bc_score_bonus >= 8: confs.append(f"🏆 BC Health ({bc_regime.get('regime','?')})")
    # V21+ precision confluences
    if ema_ribbon.get('quality') in ['EXCELLENT','GOOD']:
        confs.append(f"🌈 Ribbon {ema_ribbon['quality']} ({ema_ribbon.get('direction','?')})")
    if trend_coherence.get('coherence') in ['PERFECT','STRONG']:
        confs.append(f"🎯 TF Coherence {trend_coherence['coherence']} ({trend_coherence.get('coherent_direction','?')})")
    if candle_struct.get('quality') in ['EXCELLENT','GOOD']:
        confs.append(f"🔥 Candle {candle_struct['quality']} ({candle_struct.get('pattern_type','?')})")
    if mom_accel_bonus > 0:
        confs.append(f"🚀 Mom Accel {mom_accel.get('phase','?')}")
    # V23 confluences
    if mkt_struct.get('bos'):
        confs.append(f"🔥 BOS ({mkt_struct.get('last_event','?')})")
    if mkt_struct.get('choch'):
        confs.append(f"⚡ CHoCH ({mkt_struct.get('last_event','?')})")
    if candle_mom.get('conviction') in ['STRONG', 'MODERATE']:
        confs.append(f"💪 CandleMom {candle_mom['conviction']} ({candle_mom.get('score',0):.0f})")

    if liq_sweep.get('sweep'):
        confs.append(f"💧 {liq_sweep['type']}")
    if entry_sync.get('ready') == 'READY':
        confs.append(f"✅ Entry Sync {entry_sync['score']}/100")
    if cont_pattern.get('pattern') != 'NONE':
        confs.append(f"🚩 {cont_pattern['pattern']} ({cont_pattern.get('confidence',0)}%)")
    if early_reversal:
        confs.append(f"⚡ EARLY REVERSAL → {reversal_dir}")

    if bc_score_data.get('score', 0) > 0 and is_bc_setup:
        bc_grade = bc_score_data.get('grade', 'D')
        bc_status = bc_score_data.get('status', 'FAIL')
        status_emoji = "✅" if bc_status == "PASS" else "⏳" if bc_status == "MONITOR" else "❌"
        confs.append(f"{status_emoji} BC Score: {bc_score_data['score']} [{bc_grade}]")
    if bc_spike.get('spike_imminent'):
        # Show discounted prob + Weibull + factors
        confs.append(f"⚡ SPIKE {bc_spike['probability']}% (Weibull:{bc_spike.get('weibull_prob',0):.0%} Vol:{bc_spike.get('vol_ratio',0):.1f}× Factors:{bc_spike.get('active_factors',0)})")
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
    # FIX #7: M5 Compression
    if bc_compress.get('compression', 'NONE') != 'NONE':
        compress_emoji = "🔴" if bc_compress['compression'] == "EXTREME" else "🟡" if bc_compress['compression'] == "HIGH" else "🟢"
        confs.append(f"{compress_emoji} M5 Compression: {bc_compress['compression']} (ratio:{bc_compress.get('micro_range_ratio',1):.2f})")
    if bc_sd.get('nearest_demand') and bias == "BULLISH":
        confs.append(f"📍 Demand Zone @ {bc_sd['nearest_demand']['price']:.2f}")
    if bc_sd.get('nearest_supply') and bias == "BEARISH":
        confs.append(f"📍 Supply Zone @ {bc_sd['nearest_supply']['price']:.2f}")
    # V24-F NEW TOOLS confluences
    if bc_ema_stack.get('stacked'):
        confs.append(f"📶 EMA Stack: {bc_ema_stack['stack_quality']} ({bc_ema_stack['direction']}) U:{bc_ema_stack.get('uniformity',0):.0%}")
    if bc_gradient.get('phase') in ["ACCELERATING"]:
        confs.append(f"🚀 Drift ACCELERATING (gradient:{bc_gradient['gradient']:.2f})")
    if bc_channel.get('entry_zone') not in ['NONE', 'NEUTRAL', 'UNKNOWN', None]:
        confs.append(f"📏 Channel: {bc_channel['position']} → {bc_channel['entry_zone']} ({bc_channel.get('position_pct',50):.0f}%)")
    if bc_recovery.get('has_recent_spike') and bc_recovery.get('fade_safe'):
        confs.append(f"✅ Recovery SAFE ({bc_recovery['recovery_phase']}, speed:{bc_recovery.get('recovery_speed',0):.0%})")
    if bc_consec.get('zone') in ['NORMAL', 'FRESH']:
        confs.append(f"🟢 Drift Fresh ({bc_consec['count']} candles — {bc_consec['entry_quality']})")
    # V25-SCALP: M5 precision confluences
    if bc_m5_pulse.get('optimal_entry'):
        confs.append(f"🔋 M5 Pulse: {bc_m5_pulse['pulse_phase']} ({bc_m5_pulse['pulse_candles']}c, str:{bc_m5_pulse['pulse_strength']}%)")
    elif bc_m5_pulse.get('pulse_active'):
        confs.append(f"⚡ M5 Pulse: {bc_m5_pulse['pulse_phase']} ({bc_m5_pulse['pulse_candles']}c)")
    if bc_m5_struct.get('entry_window'):
        confs.append(f"🔬 M5: {bc_m5_struct['pattern']} → Entry Window ({bc_m5_struct['quality']})")
    if bc_m5_wicks.get('signal') in ['STRONG_REJECTION', 'MODERATE_REJECTION']:
        confs.append(f"💪 M5 Wicks: {bc_m5_wicks['signal']} ({bc_m5_wicks['rejection_wicks']}/{bc_m5_wicks.get('total_significant',0)})")

    risks = []
    # V25: BC-relevant risks only
    if regime_transition == "EXHAUSTION": risks.append("⚠️ Regime EXHAUSTION")
    if "RANGING" in regime: risks.append("⚠️ RANGING")
    if not sim['WF_STABLE']: risks.append("⚠️ WF instável")
    if mc.get('positive_pct',0)<55: risks.append(f"⚠️ MC {mc['positive_pct']}%")
    if roc_status=="EXTREME": risks.append("⚠️ ROC EXTREMO")
    if hurst_regime=="RANDOM_WALK": risks.append("⚠️ Random Walk")
    if hurst_regime=="UNRELIABLE": risks.append(f"⚠️ Hurst unreliable R²={hurst_r2}")
    if gen.get('spike_phase')=="SPIKE_IMMINENT": risks.append("💥 SPIKE IMINENTE")
    if not trigger_ok and c5 is not None: risks.append(f"⚠️ M5 sem trigger ({trigger_type})")
    if candle_struct.get('quality') == 'WEAK': risks.append("⚠️ Candle structure WEAK")
    if trend_coherence.get('coherence') == 'WEAK': risks.append("⚠️ TF coherence WEAK")
    if atr_channel.get('quality') == 'OVEREXTENDED': risks.append("⚠️ Price overextended in ATR channel")
    if random_walk_penalty < 0: risks.append(f"🚫 RANDOM WALK (H:{hurst_val:.2f} R²:{hurst_r2:.2f}) — No statistical edge")
    if candle_mom.get('conviction') == 'NONE': risks.append("⚠️ Candle momentum NONE")
    if mkt_struct.get('choch') and mkt_struct.get('trend') != bias:
        risks.append(f"⚡ CHoCH AGAINST bias ({mkt_struct.get('last_event','?')})")
    if sim.get('TOTAL_TRADES', 0) < 20: risks.append(f"⚠️ Low trades ({sim.get('TOTAL_TRADES',0)})")
    if early_reversal: risks.append(f"⚡ EARLY REVERSAL active — H4 not confirmed")
    # V24-F: Enhanced Boom/Crash risks
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
    if bc_compress.get('block_scalp') and setup_type in ["DRIFT_RIDE", "SCALP_DRIFT"]:
        risks.append("🚫 M5 COMPRESSION — spike proximity")
    # V25-SCALP: M5 precision risks
    if bc_m5_wicks.get('signal') in ['EXHAUSTION', 'WEAK_EXHAUSTION']:
        risks.append(f"🚨 M5 Wicks EXHAUSTION ({bc_m5_wicks.get('exhaustion_wicks',0)} wicks) — drift exausto")
    if bc_m5_pulse.get('pulse_phase') == 'FADING':
        risks.append("⚠️ M5 Pulse FADING — momentum a enfraquecer")
    if bc_m5_pulse.get('pulse_phase') == 'EXTENDED':
        risks.append("⚠️ M5 Pulse EXTENDED — entrada tardia")
    if bc_m5_struct.get('pattern') == 'MICRO_CONSOLIDATION' and not bc_m5_struct.get('entry_window'):
        risks.append("⏳ M5 em consolidação — aguardar breakout")
    # V24-F NEW: Gradient + Stack + Recovery risks
    if bc_gradient.get('phase') == "DYING":
        risks.append(f"🚨 Drift MORTO (gradient:{bc_gradient.get('gradient',0):.2f}) — spike iminente")
    elif bc_gradient.get('phase') == "DECELERATING":
        risks.append(f"⚠️ Drift desacelerando (gradient:{bc_gradient.get('gradient',0):.2f})")
    if bc_ema_stack.get('destack_warning') and setup_type in ["DRIFT_RIDE", "SCALP_DRIFT"]:
        risks.append("⚠️ EMA DESTACK — drift direction enfraquecendo")
    if bc_consec.get('zone') in ["EXTREME_OVERDUE", "OVERDUE"]:
        risks.append(f"🚨 Drift {bc_consec['count']} candles — {bc_consec['zone']}")
    if bc_recovery.get('has_recent_spike') and bc_recovery.get('recovery_phase') == "STALLED":
        risks.append("⚠️ Recovery STALLED — regime change possível")
    if bc_channel.get('position') == "DRIFT_MATURE" and setup_type in ["DRIFT_RIDE", "SCALP_DRIFT"]:
        risks.append(f"⚠️ Channel DRIFT_MATURE — preço no limite do canal ({bc_channel.get('position_pct',0):.0f}%)")
    # Kill-switch
    meltdown_data = bc_meltdown_check()
    if meltdown_data.get('streak', 0) >= 3:
        risks.append(f"🚨 Loss Streak: {meltdown_data['streak']} ({'BLOCKED' if meltdown_data.get('blocked') else 'CAUTION'})")

    # V25-SCALP: Max hold time based on setup type
    if setup_type == "SCALP_DRIFT":
        max_hold = profile.get('max_hold_scalp', 15)
        max_hold_info = f"{max_hold} candles M15 (~{max_hold*15//60}h{max_hold*15%60}m)"
    elif trade_style == "SCALP":
        max_hold = profile.get('max_hold_scalp', 15)
        max_hold_info = f"{max_hold} candles M15 (~{max_hold*15//60}h{max_hold*15%60}m)"
    else:
        max_hold = profile.get('max_hold_day', 60)
        max_hold_info = f"{max_hold} candles M15 (~{max_hold*15//60}h)"

    return {
        "FINAL_DECISION": sig, "TRADE_STYLE": trade_style or "N/A", "SETUP_TYPE": setup_type or "N/A",
        "MAX_HOLD": max_hold_info,
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
        "SPECTRAL": convert_np(spectral), "MARKOV": convert_np(markov),
        "REGIME_TRANSITION": regime_transition, "RT_MULT": rt_mult, "RT_DETAIL": rt_detail,
        "BIAS_CONFIDENCE": bias_confidence, "BIAS_SCORE": bias_score,
        "MOMENTUM_V21": momentum_v21,
        "INDEPENDENT_EDGES": convert_np(indep_edges),
        "HOLDING_PERIOD": convert_np(hold),
        "SCORE_BREAKDOWN": convert_np({
            "ADX":score.trend_strength,"MOM":score.momentum_align,"PAT":score.patterns,
            "VAL":score.value_zone,"HIST":score.historical,
            "BC_SCORE":score.bc_score_bonus,"M5_PREC":score.m5_precision_bonus,"DRIFT_Q":score.drift_quality_bonus,
            "ALIGN":score.alignment_bonus,"SPIKE_T":score.spike_timing_bonus,"REGIME":score.regime_bonus,
            "VOL":score.volume_bonus,"HURST":score.hurst_bonus,"ZSCORE":score.zscore_bonus,
            "CONSEC":score.consecutive_bonus,"GEN":score.generator_bonus,"DIST":score.distribution_bonus,
            "VR":score.vr_bonus,"ACF":score.acf_bonus,
            "MARKOV":score.markov_bonus,"SPECTRAL":score.spectral_bonus,
            "ADX_SLOPE":score.adx_slope_bonus,"RIBBON":score.ribbon_bonus,
            "COHERENCE":score.coherence_bonus,"CANDLE":score.candle_bonus,
            "MOM_ACCEL":score.mom_accel_bonus
        }),
        # V21+ precision data
        "ADX_SLOPE": convert_np(adx_slope),
        "EMA_RIBBON": convert_np(ema_ribbon),
        "TREND_COHERENCE": convert_np(trend_coherence),
        "CANDLE_STRUCT": convert_np(candle_struct),
        "MOM_ACCEL": convert_np(mom_accel),
        "ATR_CHANNEL": convert_np(atr_channel),
        # V23 precision data
        "MKT_STRUCTURE": convert_np(mkt_struct),
        "CANDLE_MOMENTUM": convert_np(candle_mom),
        "LIQ_SWEEP": convert_np(liq_sweep),
        "ENTRY_SYNC": convert_np(entry_sync),
        "CONT_PATTERN": convert_np(cont_pattern),
        "EARLY_REVERSAL": early_reversal,
        "REVERSAL_DIR": reversal_dir,
        "RW_PENALTY": random_walk_penalty,
        # V23: Multi-entry levels
        "ENTRY_AGGRESSIVE": float(round(entry_aggressive, 5)),
        "ENTRY_IDEAL": float(round(entry_ideal, 5)),
        "ENTRY_SNIPER": float(round(entry_sniper, 5)),
        # V23: Trailing stop levels
        "TRAIL_BE": float(round(trail_be, 5)),
        "TRAIL_1R": float(round(trail_1, 5)),
        # V23: MC confidence
        "MC_CONFIDENCE": "HIGH" if sim.get('TOTAL_TRADES', 0) >= 30 else "LOW",
        # V24-F: Boom/Crash engine data
        "BC_SPIKE": convert_np(bc_spike),
        "BC_DRIFT": convert_np(bc_drift),
        "BC_FADE": convert_np(bc_fade),
        "BC_SD_ZONES": convert_np(bc_sd),
        "BC_FREQ": convert_np(bc_freq),
        "BC_ABSORB": convert_np(bc_absorb),
        "BC_MULTI": convert_np(bc_multi),
        "BC_STOCH": convert_np(bc_stoch),
        # V24-F: New data
        "BC_REGIME": convert_np(bc_regime),
        "BC_KURTOSIS": convert_np(bc_kurt),
        "BC_CONFLICTS": convert_np(bc_conflicts),
        "BC_CLEAN_ATR": round(float(bc_atr_clean), 5),
        "RAW_ATR": round(float(c1['ATR']), 5),
        # FIX #8: BC Score data
        "BC_SCORE": convert_np(bc_score_data),
        "BC_SCORE_VAL": bc_score_data.get('score', 0),
        "BC_GRADE": bc_score_data.get('grade', 'D'),
        # FIX #7: M5 Compression
        "BC_COMPRESS": convert_np(bc_compress),
        # V24-F NEW TOOLS
        "BC_EMA_STACK": convert_np(bc_ema_stack),
        "BC_GRADIENT": convert_np(bc_gradient),
        "BC_RECOVERY": convert_np(bc_recovery),
        "BC_CONSEC": convert_np(bc_consec),
        "BC_CHANNEL": convert_np(bc_channel),
        "BC_M5_PULSE": convert_np(bc_m5_pulse),
        "BC_M5_STRUCT": convert_np(bc_m5_struct),
        "BC_M5_WICKS": convert_np(bc_m5_wicks),
        # FIX #11: Regime TP mult
        "REGIME_SL_MULT": bc_regime.get('sl_mult', 1.0),
        "EXPECTANCY": sim.get('EXPECTANCY', 0),
        "EXPECTANCY_STRESSED": sim.get('EXPECTANCY_STRESSED', 0),
        "HIGH_RISK": sim.get('HIGH_RISK', False),
        "MELTDOWN": convert_np(bc_meltdown_check()),
        "VERSION": "V24-F",
    }

# ==============================================================================
# SCANNER V20 — 🟢 FIX #4: Todos os gen types
# ==============================================================================

async def quick_scan(code, name):
    """V25: BC-only scanner — scores based on spike/drift dynamics"""
    try:
        raw = await fetch_single(code, 3600, 300)
        if not raw: return None
        df = indicators(prep_df(raw)); profile = get_profile(name)
        if len(df) < 50: return None
        c = df.iloc[-1]; ppy = detect_periods_per_year(df)
        hurst_val, _, hr2 = calculate_hurst_exponent(df['close'])
        z = float(c['ZSCORE']) if pd.notna(c.get('ZSCORE')) else 0
        vr = variance_ratio_test(df['close'])

        # V25: Always BC generator
        gen = GeneratorModelV20.analyze_crash_boom(df, profile, ppy)
        regime, _ = classify_regime(df)

        # V25: BC-specific scoring
        qs = 0
        # Spike phase scoring (most important for BC)
        phase = gen.get('spike_phase', 'UNKNOWN')
        if phase in ["DRIFT_STRONG", "DRIFT_NORMAL"]: qs += 25
        elif phase == "SPIKE_IMMINENT": qs += 20
        elif phase == "DRIFT_WEAKENING": qs += 10
        # Drift strength
        drift_str = gen.get('drift_strength', 0)
        if drift_str > 2: qs += 15
        elif drift_str > 0.5: qs += 8
        # ADX (still useful for drift momentum)
        if c['ADX'] > profile.get('adx_strong', 25): qs += 12
        elif c['ADX'] > profile.get('adx_trend_min', 15): qs += 6
        # Statistical edge
        if hurst_val > profile.get('hurst_trend_min', 0.53) or hurst_val < 0.45: qs += 10
        if vr.get('has_edge'): qs += 10
        if "TRENDING" in regime: qs += 5
        # Z-score extremes
        if abs(z) > profile.get('zscore_extreme', 2) * 0.6: qs += 8

        bias = "BULLISH" if c['close'] > c['EMA_200'] else "BEARISH"
        return {"name": name, "code": code, "score": qs, "bias": bias,
                "adx": round(c['ADX'], 1), "hurst": round(hurst_val, 3),
                "zscore": round(z, 2), "regime": regime,
                "gen_signal": gen.get('signal', 'N/A'), "vr_edge": vr.get('has_edge', False),
                "spike_phase": phase, "drift_str": round(drift_str, 2),
                "profile": profile['vol_class']}
    except: return None

# ==============================================================================
# STREAMLIT UI V20 — MODERN MINIMAL
# ==============================================================================

# ── SIDEBAR ──
with st.sidebar:
    st.markdown("""<div style='padding:12px 0 20px;'>
        <div style='display:flex;align-items:center;gap:10px;'>
            <div style='width:36px;height:36px;border-radius:10px;
                background:linear-gradient(135deg,#6366f1,#4f46e5);
                display:flex;align-items:center;justify-content:center;
                font-size:16px;font-weight:800;color:#fff;font-family:Outfit,sans-serif;
                box-shadow:0 4px 16px rgba(99,102,241,0.3);'>◆</div>
            <div>
                <div style='font-family:Outfit,sans-serif;font-size:22px;font-weight:700;
                    color:#eeeef0;letter-spacing:-0.5px;'>APATECO</div>
                <div style='font-family:JetBrains Mono,monospace;font-size:10px;
                    color:#6366f1;letter-spacing:1px;'>V25-SCALP</div>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    if "GEMINI_API_KEY" in st.secrets:
        api = st.secrets["GEMINI_API_KEY"]
        st.markdown("""<div style='display:flex;align-items:center;gap:6px;padding:6px 12px;
            background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.2);
            border-radius:8px;margin-bottom:8px;'>
            <span class='live-dot'></span>
            <span style='font-size:11px;color:#6ee7b7;font-weight:500;font-family:Outfit,sans-serif;'>API Connected</span>
        </div>""", unsafe_allow_html=True)
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

    st.markdown("""<div class='sidebar-info'>
        <strong>APATECO V25-SCALP</strong><br>
        Zero-Illusion · M5 Precision<br>
        Weibull · Clean ATR · BC Score<br>
        <span style='color:#6366f1;'>◆</span> 15 BC Engines · 3 M5 Scalp
    </div>""", unsafe_allow_html=True)

    # FIX #5: Kill-Switch Trade Tracking (FUNCTIONAL)
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    st.markdown("<span style='font-size:11px;color:#71717a;font-weight:600;'>KILL-SWITCH</span>",
                unsafe_allow_html=True)
    ks_cols = st.columns(3)
    with ks_cols[0]:
        if st.button("✅ WIN", key="ks_win", use_container_width=True):
            bc_record_trade_result(True)
    with ks_cols[1]:
        if st.button("❌ LOSS", key="ks_loss", use_container_width=True):
            bc_record_trade_result(False)
    with ks_cols[2]:
        if st.button("🔄 RESET", key="ks_reset", use_container_width=True):
            st.session_state['bc_loss_streak'] = 0
    ks_streak = st.session_state.get('bc_loss_streak', 0)
    if ks_streak >= 5:
        st.error(f"🚫 BLOCKED: {ks_streak} losses consecutivos")
    elif ks_streak >= 3:
        st.warning(f"⚠️ CAUTION: {ks_streak} losses consecutivos")
    elif ks_streak > 0:
        st.info(f"📊 Streak: {ks_streak} loss(es)")

# ── HEADER ──
st.markdown("""<div class='header-bar'>
    <div class='header-diamond'>◆</div>
    <span class='header-logo'>APATECO</span>
    <span class='header-version'>V25 · SCALP</span>
    <span class='header-sub'>Boom/Crash · Zero-Illusion · M5 Precision Engine</span>
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
        st.markdown(f"""<div style='padding:12px 16px;background:var(--bg-surface);border:1px solid var(--border);
            border-radius:10px;margin:8px 0 16px;'>
            <div style='display:flex;align-items:center;justify-content:space-between;'>
                <div>
                    <span style='color:var(--text-primary);font-size:13px;font-weight:600;
                        font-family:Outfit,sans-serif;'>{prof['vol_class']}</span><br>
                    <span class='mono text-xs' style='color:var(--accent-light);'>{prof.get('gen_type','—')}</span>
                </div>
                <div style='width:8px;height:8px;border-radius:50%;
                    background:{"var(--success)" if prof.get("gen_type","") in ["BOOM","CRASH"] else "var(--text-muted)"};'></div>
            </div>
        </div>""", unsafe_allow_html=True)
        run = st.button("Analyze", use_container_width=True)

    with right:
        if run:
            if not api: st.error("API key required"); st.stop()

            status = st.status("◆ Analyzing...", expanded=True)
            status.markdown("""<div class='loading-stage'>
                <div class='stage-dot loading-active' style='background:#6366f1;'></div>
                <span style='color:#818cf8;font-size:12px;'>Connecting to Deriv — fetching H4 · H1 · M15 · M5 data...</span>
            </div>""", unsafe_allow_html=True)
            h1r, h4r, m15r, m5r, err = asyncio.run(fetch_multi_tf(assets[target]))
            if err: status.update(state='error'); st.error(err); st.stop()
            status.markdown("""<div class='loading-stage'>
                <div class='stage-dot' style='background:#10b981;'></div>
                <span style='color:#6ee7b7;font-size:12px;'>Data loaded ✓</span>
            </div><div class='loading-stage'>
                <div class='stage-dot loading-active' style='background:#6366f1;'></div>
                <span style='color:#818cf8;font-size:12px;'>Running 15 BC engines + 3 M5 scalp engines + statistical validation...</span>
            </div>""", unsafe_allow_html=True)
            data = sniper_core_v20(target, h1r, h4r, m15r, m5r, capital, risk_pct)
            status.markdown("""<div class='loading-stage'>
                <div class='stage-dot' style='background:#10b981;'></div>
                <span style='color:#6ee7b7;font-size:12px;'>Analysis complete · Monte Carlo done ✓</span>
            </div>""", unsafe_allow_html=True)
            imgs = data.pop("IMAGES")
            
            # ── GEMINI AI COM RETRY + FALLBACK ──
            status.markdown("""<div class='loading-stage'>
                <div class='stage-dot loading-active' style='background:#a855f7;'></div>
                <span style='color:#c4b5fd;font-size:12px;'>Generating AI insight with Gemini...</span>
            </div>""", unsafe_allow_html=True)
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
                status.update(label="◆ Analysis Complete", state="complete")
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

            # ── GRADE CARD ── (V25 Premium)
            g = data['SETUP_GRADE']
            grade_class = {"S":"grade-s","A++":"grade-app","A+":"grade-ap","A":"grade-a"}.get(g,"grade-low")
            score_pct = min(data['SETUP_SCORE'] / 220 * 100, 100)
            bar_color = {"S":"#a78bfa","A++":"#34d399","A+":"#60a5fa","A":"#67e8f9"}.get(g,"#505068")

            # Decision tag
            d = data['FINAL_DECISION']
            if "LONG" in d:
                tag = f"<span class='tag-long'>▲ LONG</span>"
            elif "SHORT" in d:
                tag = f"<span class='tag-short'>▼ SHORT</span>"
            elif "BLOCKED" in d:
                tag = f"<span class='tag-blocked'>⊘ BLOCKED</span>"
            else:
                tag = f"<span class='tag-monitoring'>◉ MONITORING</span>"

            # Style tag
            style_tag = ""
            if data.get('TRADE_STYLE') == "SCALP":
                style_tag = "<span class='tag-scalp'>⚡ SCALP</span>"
            elif data.get('TRADE_STYLE') == "DAY":
                style_tag = "<span class='tag-scalp' style='color:#3b82f6;border-color:rgba(59,130,246,0.25);background:rgba(59,130,246,0.08);'>◎ DAY</span>"

            # BC Score badge
            bc_s = data.get('BC_SCORE', {})
            bc_badge = ""
            if bc_s.get('score', 0) > 0:
                bc_grade = bc_s.get('grade', '?')
                bc_score_val = bc_s.get('score', 0)
                bc_color = "#a78bfa" if bc_grade == "S" else "#34d399" if bc_grade in ["A+","A++"] else "#60a5fa" if bc_grade in ["A","B"] else "#505068"
                bc_badge = f"""<span style='font-family:JetBrains Mono,monospace;font-size:11px;
                    color:{bc_color};background:rgba(99,102,241,0.06);
                    padding:3px 8px;border-radius:4px;margin-left:8px;'>
                    BC:{bc_score_val} [{bc_grade}]</span>"""

            st.markdown(f"""
            <div class='{grade_class}' style='margin:8px 0 24px;'>
                <div style='display:flex;align-items:center;justify-content:center;gap:8px;margin-bottom:8px;'>
                    <span style='font-family:Outfit,sans-serif;font-size:11px;letter-spacing:1.5px;
                        text-transform:uppercase;opacity:0.6;'>Setup Grade</span>
                </div>
                <div class='grade-letter'>{g}</div>
                <div style='font-family:JetBrains Mono,monospace;font-size:24px;margin:8px 0;color:var(--text-primary);'>
                    {data['SETUP_SCORE']:.0f}<span style='color:var(--text-muted);font-size:14px;'> / 220</span>
                    {bc_badge}
                </div>
                <div class='score-bar-outer'>
                    <div class='score-bar-inner' style='width:{score_pct}%;background:linear-gradient(90deg,{bar_color},{bar_color}dd);'></div>
                </div>
                <div style='margin-top:14px;display:flex;align-items:center;justify-content:center;gap:6px;'>
                    {tag}{style_tag}
                </div>
                <div style='color:var(--text-muted);font-size:12px;margin-top:8px;
                    font-family:JetBrains Mono,monospace;'>
                    {data.get('SETUP_TYPE','—')} · {data['GEN_TYPE']} · {data.get('MAX_HOLD','—')}
                </div>
            </div>""", unsafe_allow_html=True)

            # ── GENERATOR MODEL ──
            st.markdown("""<div class='section-header'>
                <div class='section-icon'>⚙️</div>
                <span class='section-title'>Generator</span>
                <div class='section-line'></div>
            </div>""", unsafe_allow_html=True)
            ga = data.get('GEN_ANALYSIS', {})
            g1, g2, g3, g4 = st.columns(4)
            g1.metric("Type", data['GEN_TYPE'])
            g2.metric("Spike Phase", ga.get('spike_phase', '?'))
            g3.metric("Decay Strength", f"{ga.get('decay_strength',0):.2f}")
            g4.metric("Last Spike", f"{ga.get('last_spike_bars',0)} bars")

            # ── STATISTICAL EDGE ──
            st.markdown("""<div class='section-header'>
                <div class='section-icon'>📊</div>
                <span class='section-title'>Edge Analysis</span>
                <div class='section-line'></div>
            </div>""", unsafe_allow_html=True)
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
            # ═══ V25: BC PREDICTABILITY ═══
            st.markdown("""<div class='section-header'>
                <div class='section-icon'>🔮</div>
                <span class='section-title'>BC Predictability</span>
                <div class='section-line'></div>
            </div>""", unsafe_allow_html=True)
            # BC-specific predictability: regime, kurtosis, spike frequency, drift pattern
            bc_regime_d = data.get('BC_REGIME', {})
            bc_kurt_d = data.get('BC_KURTOSIS', {})
            bc_freq_d = data.get('BC_FREQUENCY', {})
            pc1, pc2, pc3, pc4 = st.columns(4)
            regime_name = bc_regime_d.get('regime', '?')
            regime_color = "🟢" if regime_name in ['DRIFT_SMOOTH'] else "🟡" if regime_name in ['POST_SPIKE','PRE_SPIKE'] else "🔴" if regime_name in ['SPIKE_CLUSTER','CHOPPY'] else "⚪"
            pc1.metric(f"BC Regime {regime_color}", regime_name, f"conf={bc_regime_d.get('confidence',0):.0f}%")
            pc2.metric("Kurtosis", f"{bc_kurt_d.get('kurtosis',0):.1f}", bc_kurt_d.get('regime','?'))
            pc3.metric("Spike Freq", f"{bc_freq_d.get('avg_gap',0):.0f} M15", f"recent={bc_freq_d.get('recent_gap',0):.0f}")
            vr_d = data.get('VR', {})
            acf_d = data.get('ACF', {})
            pc4.metric("VR+ACF", f"{'Edge' if vr_d.get('has_edge') else 'No'} | {'Pat' if acf_d.get('has_pattern') else 'No'}",
                      f"VR:{vr_d.get('n_significant',0)} ACF:lag1={acf_d.get('acf_1',0):.3f}")

            mrkv = data.get('MARKOV', {})
            spec = data.get('SPECTRAL', {})
            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("Markov", "Dep Found" if mrkv.get('has_dependence') else "No Dep", mrkv.get('best_transition',''))
            mc2.metric("Cycles", f"{spec.get('dominant_period',0):.0f} bars" if spec.get('has_cycle') else "None")
            mc3.metric("Regime Shift", data.get('REGIME_TRANSITION', 'STABLE'), data.get('RT_DETAIL',''))

            # ── V21+ ENTRY PRECISION ──
            st.markdown("""<div class='section-header'>
                <div class='section-icon'>🎯</div>
                <span class='section-title'>Entry Precision</span>
                <div class='section-line'></div>
            </div>""", unsafe_allow_html=True)
            adx_sl = data.get('ADX_SLOPE', {})
            ribbon = data.get('EMA_RIBBON', {})
            coherence = data.get('TREND_COHERENCE', {})
            candle = data.get('CANDLE_STRUCT', {})
            maccel = data.get('MOM_ACCEL', {})
            atr_ch = data.get('ATR_CHANNEL', {})

            ep1, ep2, ep3, ep4 = st.columns(4)
            ep1.metric("ADX Phase", adx_sl.get('phase', '?'), f"slope={adx_sl.get('slope',0):.2f}")
            ep2.metric("EMA Ribbon", ribbon.get('quality', '?'), ribbon.get('direction', '?'))
            ep3.metric("TF Coherence", coherence.get('coherence', '?'), f"{coherence.get('score',0):.0f}%")
            # Clean ATR (BC-specific: spike-filtered ATR for accurate SL)
            clean_atr_v = data.get('BC_CLEAN_ATR', 0)
            raw_atr_v = data.get('RAW_ATR', 0)
            atr_ratio = clean_atr_v / raw_atr_v if raw_atr_v > 0 else 1.0
            atr_c = "🟢" if atr_ratio > 0.85 else "🟡" if atr_ratio > 0.7 else "🔴"
            ep4.metric(f"Clean ATR {atr_c}", f"{clean_atr_v:.2f}", f"ratio={atr_ratio:.0%} vs raw")

            ep5, ep6, ep7 = st.columns(3)
            ep5.metric("Candle Struct", candle.get('quality', '?'), candle.get('pattern_type', '?'))
            ep6.metric("Mom Accel", maccel.get('phase', '?'), f"conf={maccel.get('confidence',0):.0f}%")
            ep7.metric("ATR Channel", atr_ch.get('quality', '?'), f"pos={atr_ch.get('channel_position',0.5):.2f}")

            # ── V23 SNIPER ENGINE ──
            st.markdown("""<div class='section-header'>
                <div class='section-icon'>🔫</div>
                <span class='section-title'>Sniper Engine V23</span>
                <div class='section-line'></div>
            </div>""", unsafe_allow_html=True)
            ms_data = data.get('MKT_STRUCTURE', {})
            cm_data = data.get('CANDLE_MOMENTUM', {})
            sw_data = data.get('LIQ_SWEEP', {})
            es_data = data.get('ENTRY_SYNC', {})
            cp_data = data.get('CONT_PATTERN', {})

            s1, s2, s3, s4 = st.columns(4)
            ms_trend = ms_data.get('trend', '?')
            ms_event = ms_data.get('last_event', 'NONE')
            ms_color = "🟢" if ms_event.startswith("BOS_BULL") or ms_event.startswith("CHOCH_BULL") else "🔴" if ms_event.startswith("BOS_BEAR") or ms_event.startswith("CHOCH_BEAR") else "⚪"
            s1.metric(f"Mkt Structure {ms_color}", ms_trend, ms_event)
            s2.metric("Candle Mom", cm_data.get('conviction', '?'), f"score={cm_data.get('score',0):.0f}")
            # V25: Spike Probability (BC-specific)
            bc_sp = data.get('BC_SPIKE', {})
            sp_prob = bc_sp.get('probability', 0)
            sp_c = "🟢" if sp_prob >= 60 else "🟡" if sp_prob >= 35 else "⚪"
            s3.metric(f"Spike Prob {sp_c}", f"{sp_prob}%", bc_sp.get('imminence', '?'))
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
                st.markdown("""<div class='section-header' style='margin:20px 0 10px;'>
                    <span class='section-title' style='font-size:12px;'>🎯 Entry Levels</span>
                    <div class='section-line'></div>
                </div>""", unsafe_allow_html=True)
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
            st.markdown("""<div class='section-header'>
                <div class='section-icon' style='background:rgba(245,158,11,0.1);border-color:rgba(245,158,11,0.15);'>⚡</div>
                <span class='section-title'>Boom/Crash Engine</span>
                <div class='section-line'></div>
            </div>""", unsafe_allow_html=True)
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

            # V24-F TOOLS: EMA Stack + Gradient + Recovery + Consecutive + Channel
            st.markdown("""<div class='section-header'>
                <div class='section-icon'>📡</div>
                <span class='section-title'>Trend Tools V24-F</span>
                <div class='section-line'></div>
            </div>""", unsafe_allow_html=True)
            bc_stk = data.get('BC_EMA_STACK', {})
            bc_grd = data.get('BC_GRADIENT', {})
            bc_rec = data.get('BC_RECOVERY', {})
            bc_csc = data.get('BC_CONSECUTIVE', {})
            bc_chn = data.get('BC_CHANNEL', {})

            tf1, tf2, tf3, tf4, tf5 = st.columns(5)
            stk_q = bc_stk.get('stack_quality', '?')
            stk_c = "🟢" if stk_q in ["PERFECT","GOOD"] else "🟡" if stk_q == "WEAK" else "⚪"
            tf1.metric(f"EMA Stack {stk_c}", stk_q, bc_stk.get('direction','?'))

            grd_phase = bc_grd.get('phase', '?')
            grd_c = "🟢" if grd_phase == "ACCELERATING" else "🟡" if grd_phase in ["STABLE","DECELERATING"] else "🔴" if grd_phase == "DYING" else "⚪"
            tf2.metric(f"Gradient {grd_c}", grd_phase, f"{bc_grd.get('gradient',0):.2f}")

            rec_phase = bc_rec.get('recovery_phase', '?')
            rec_c = "🟢" if bc_rec.get('fade_safe') else "🔴" if rec_phase in ["STALLED","JUST_SPIKED"] else "⚪"
            tf3.metric(f"Recovery {rec_c}", rec_phase, f"spd={bc_rec.get('recovery_speed',0):.0%}" if bc_rec.get('has_recent_spike') else "No spike")

            csc_zone = bc_csc.get('zone', '?')
            csc_c = "🟢" if csc_zone in ["FRESH","NORMAL"] else "🟡" if csc_zone == "EXTENDED" else "🔴"
            tf4.metric(f"Consecutive {csc_c}", f"{bc_csc.get('count',0)} bars", bc_csc.get('entry_quality','?'))

            chn_pos = bc_chn.get('position', '?')
            chn_c = "🟢" if bc_chn.get('entry_zone') not in ['NONE','NEUTRAL','UNKNOWN',None] else "⚪"
            tf5.metric(f"Channel {chn_c}", chn_pos, f"{bc_chn.get('position_pct',50):.0f}%")

            # V25-SCALP: M5 Precision Tools
            bc_mp = data.get('BC_M5_PULSE', {})
            bc_ms = data.get('BC_M5_STRUCT', {})
            bc_mw = data.get('BC_M5_WICKS', {})
            has_m5 = bc_mp.get('pulse_phase','NO_DATA') != 'NO_DATA'
            if has_m5:
                st.markdown("""<div class='section-header'>
                    <div class='section-icon' style='background:rgba(99,102,241,0.15);'>⚡</div>
                    <span class='section-title'>M5 Scalp Precision</span>
                    <div class='section-line'></div>
                </div>""", unsafe_allow_html=True)

                m1, m2, m3 = st.columns(3)
                pulse_phase = bc_mp.get('pulse_phase', '?')
                pulse_c = "🟢" if bc_mp.get('optimal_entry') else "🟡" if bc_mp.get('pulse_active') else "⚪"
                m1.metric(f"M5 Pulse {pulse_c}", pulse_phase,
                         f"{bc_mp.get('pulse_candles',0)}c · str:{bc_mp.get('pulse_strength',0)}%")

                struct_pat = bc_ms.get('pattern', 'NONE')
                struct_c = "🟢" if bc_ms.get('entry_window') else "🟡" if struct_pat != 'NONE' else "⚪"
                m2.metric(f"M5 Structure {struct_c}", struct_pat,
                         f"{bc_ms.get('quality','?')} · {'Entry ✓' if bc_ms.get('entry_window') else 'Wait'}")

                wick_sig = bc_mw.get('signal', 'NEUTRAL')
                wick_c = "🟢" if wick_sig in ['STRONG_REJECTION','MODERATE_REJECTION'] else "🔴" if 'EXHAUSTION' in wick_sig else "⚪"
                m3.metric(f"M5 Wicks {wick_c}", wick_sig,
                         f"rej:{bc_mw.get('rejection_wicks',0)} exh:{bc_mw.get('exhaustion_wicks',0)}")

            st.markdown("""<div class='section-header'>
                <div class='section-icon'>📉</div>
                <span class='section-title'>Distribution</span>
                <div class='section-line'></div>
            </div>""", unsafe_allow_html=True)
            da = data.get('DIST_ANALYSIS', {})
            d1, d2, d3, d4 = st.columns(4)
            d1.metric("Skewness", f"{da.get('skewness',0):.3f}")
            d2.metric("Kurtosis", f"{da.get('kurtosis',3):.3f}")
            d3.metric("Tails", da.get('tail_risk', '—'))
            d4.metric("Percentile", f"{da.get('percentile',50):.0f}%")

            # ── BACKTEST ──
            st.markdown("""<div class='section-header'>
                <div class='section-icon'>✅</div>
                <span class='section-title'>Validation</span>
                <div class='section-line'></div>
            </div>""", unsafe_allow_html=True)
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

            # ── CONFLUENCES & RISKS ── (V25 Enhanced)
            if data['CONFLUENCES'] or data['RISKS']:
                st.markdown("""<div class='section-header'>
                    <div class='section-icon' style='background:rgba(16,185,129,0.1);'>✦</div>
                    <span class='section-title'>Confluences & Risks</span>
                    <div class='section-line'></div>
                </div>""", unsafe_allow_html=True)
                conf_html = "<div style='margin-bottom:12px;'>"
                for c in data.get('CONFLUENCES', []):
                    conf_html += f"<span class='pill pill-green'>{c}</span> "
                conf_html += "</div><div>"
                for r in data.get('RISKS', []):
                    conf_html += f"<span class='pill pill-red'>{r}</span> "
                conf_html += "</div>"
                st.markdown(conf_html, unsafe_allow_html=True)

            # ── TRADE PLAN ──
            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
            is_active = any(x in d for x in ["DRIFT","SPIKE","SCALP","FADE","REVERSAL","STOCH"])
            if is_active:
                st.markdown("""<div class='section-header'>
                    <div class='section-icon' style='background:rgba(16,185,129,0.1);'>🎯</div>
                    <span class='section-title'>Trade Plan</span>
                    <div class='section-line'></div>
                </div>""", unsafe_allow_html=True)

                # Entry/SL/TP as glowing card
                entry_color = "#22c55e" if "LONG" in d else "#ef4444"
                st.markdown(f"""<div class='card-glow'>
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
                        <span class='plan-note'>ATR-Based TP</span>
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
                    st.markdown("""<div class='section-header'>
                    <div class='section-icon'>△</div>
                    <span class='section-title'>Pyramid</span>
                    <div class='section-line'></div>
                </div>""", unsafe_allow_html=True)
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
                st.markdown(f"""<div class='card' style='border-color:rgba(239,68,68,0.15);border-left:3px solid rgba(239,68,68,0.4);'>
                    <div style='display:flex;align-items:center;gap:8px;'>
                        <span style='font-size:18px;'>⊘</span>
                        <span style='color:#ef4444;font-size:14px;font-weight:600;font-family:Outfit,sans-serif;'>Trade Blocked</span>
                    </div>
                    <span class='mono text-sm' style='color:var(--text-secondary);margin-top:6px;display:block;'>{reason}</span>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown("""<div class='card' style='border-color:rgba(245,158,11,0.15);border-left:3px solid rgba(245,158,11,0.3);'>
                    <div style='display:flex;align-items:center;gap:8px;'>
                        <span style='font-size:18px;'>◉</span>
                        <span style='color:#f59e0b;font-size:14px;font-weight:600;font-family:Outfit,sans-serif;'>Monitoring</span>
                    </div>
                    <span class='text-sm' style='color:var(--text-secondary);margin-top:4px;display:block;'>No setup detected. Waiting for conditions to align.</span>
                </div>""", unsafe_allow_html=True)

            # ── CHARTS ──
            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
            st.markdown("""<div class='section-header'>
                <div class='section-icon'>📈</div>
                <span class='section-title'>Charts</span>
                <div class='section-line'></div>
            </div>""", unsafe_allow_html=True)
            tabs = st.tabs(["H4", "H1", "M15"])
            for i, t in enumerate(tabs):
                with t:
                    st.image(imgs[i], use_container_width=True)

            # ── AI INSIGHT ──
            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
            st.markdown("""<div class='section-header'>
                <div class='section-icon' style='background:rgba(168,85,247,0.12);border-color:rgba(168,85,247,0.15);'>🧠</div>
                <span class='section-title'>AI Analysis</span>
                <div class='section-line'></div>
            </div>""", unsafe_allow_html=True)
            st.markdown(f"""<div class='card-accent'>
                {ai}
            </div>""", unsafe_allow_html=True)

# ==============================================================================
# SCANNER MODE
# ==============================================================================
elif mode == "Scanner":
    st.markdown("""<div class='section-header'>
        <div class='section-icon'>🔍</div>
        <span class='section-title'>Scanner</span>
        <div class='section-line'></div>
    </div>""", unsafe_allow_html=True)
    st.markdown("<p class='text-sm' style='color:var(--text-muted);margin-top:-4px;'>Scan all synthetic indices for statistical edge opportunities.</p>",
                unsafe_allow_html=True)

    if st.button("Scan All Assets", use_container_width=True):
        with st.spinner("Scanning..."):
            async def run_scan():
                return await asyncio.gather(*[quick_scan(c, n) for n, c in assets.items()])
            results = asyncio.run(run_scan())
            valid = sorted([r for r in results if r], key=lambda x: x['score'], reverse=True)

        if valid:
            st.markdown(f"""<div style='display:flex;align-items:center;gap:8px;margin:16px 0;'>
                <span class='live-dot'></span>
                <span style='font-size:12px;color:var(--text-secondary);'>{len(valid)} assets scanned</span>
            </div>""", unsafe_allow_html=True)

            for i, r in enumerate(valid[:12]):
                score = r['score']
                sc = "var(--success)" if score >= 50 else "var(--warning)" if score >= 30 else "var(--text-muted)"
                bias_c = "var(--success)" if r['bias'] == "BULLISH" else "var(--danger)"
                vr_tag = "<span class='pill pill-green' style='font-size:10px;padding:2px 8px;'>VR Edge</span>" if r.get('vr_edge') else ""

                st.markdown(f"""<div class='scan-row' style='animation-delay:{i*0.05}s;'>
                    <span class='scan-rank'>#{i+1}</span>
                    <span class='scan-name'>{r['name']}</span>
                    <span class='scan-score' style='color:{sc};'>{score}</span>
                    <div>
                        <span class='pill' style='font-size:10px;padding:2px 8px;color:{bias_c};border-color:{bias_c}30;'>{r['bias']}</span>
                        {vr_tag}
                    </div>
                    <span class='scan-meta' style='min-width:260px;text-align:right;'>
                        ADX {r['adx']} · H {r['hurst']} · Z {r['zscore']} · {r.get('spike_phase','?')[:12]} · D:{r.get('drift_str',0)}
                    </span>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("No results found")
