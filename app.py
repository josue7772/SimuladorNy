
import streamlit as st
import requests
import pandas as pd
import numpy as np
import sqlite3
import math
import os
from datetime import datetime, date
from zoneinfo import ZoneInfo

# ============================================================
# SIMULADORNY - SPORTS INTELLIGENCE
# ============================================================

st.set_page_config(
    page_title="SimuladorNy | Sports Intelligence",
    page_icon="⚽",
    layout="centered",
    initial_sidebar_state="collapsed"
)

TZ = "America/Mexico_City"
DB = "simuladorny.db"

# ============================================================
# CONFIGURACIÓN API
# ============================================================

def get_secret(name, default=""):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return os.getenv(name, default)

FOOTBALL_KEY = get_secret("API_FOOTBALL_KEY")
BASEBALL_KEY = get_secret("API_BASEBALL_KEY")
KBO_LEAGUE_ID = get_secret("KBO_LEAGUE_ID")

# ============================================================
# LIGAS
# ============================================================

LEAGUES = {
    "🇲🇽 Liga MX": 262,
    "🏴 Premier League": 39,
    "🇪🇸 LaLiga": 140,
    "🇮🇹 Serie A": 135,
    "🇩🇪 Bundesliga": 78,
    "🇫🇷 Ligue 1": 61,
    "🇳🇱 Eredivisie": 88,
    "🇵🇹 Primeira Liga": 94,
    "🇧🇷 Brasileirão": 71,
    "🇺🇸 MLS": 253,
    "🇪🇺 Champions League": 2,
    "🇪🇺 Europa League": 3,
    "🇪🇺 Conference League": 848,
    "🇬🇧 Championship": 40,
    "🇹🇷 Süper Lig": 203,
    "🇸🇦 Saudi Pro League": 307,
    "🇦🇷 Liga Profesional": 128,
    "🇧🇪 Belgian Pro League": 144,
    "🇪🇸 Segunda División": 141
}

LEAGUE_NAMES = {
    league_id: name
    for name, league_id in LEAGUES.items()
}

# ============================================================
# BASE DE DATOS
# ============================================================

def init_db():
    with sqlite3.connect(DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sport TEXT,
                match_id TEXT,
                home TEXT,
                away TEXT,
                prediction TEXT,
                created_at TEXT
            )
        """)

init_db()

# ============================================================
# DISEÑO ORIGINAL - DARK UI
# ============================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}

.stApp {
    background: #0b0d10;
    color: #f3f4f6;
}

header[data-testid="stHeader"] {
    background: #0b0d10;
}

.block-container {
    max-width: 680px;
    padding-top: 1rem;
    padding-bottom: 3rem;
}

h1, h2, h3, p, label {
    color: #f3f4f6;
}

div[data-testid="stMetric"] {
    background: #12151c;
    border: 1px solid #222733;
    border-radius: 14px;
    padding: 12px;
}

div[data-testid="stMetricLabel"] {
    color: #9ca3af;
}

div[data-testid="stMetricValue"] {
    color: white;
    font-weight: 800;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #12151c;
    border: 1px solid #222733;
    border-radius: 16px;
}

div.stButton > button {
    border-radius: 11px;
    font-weight: 700;
    border: 1px solid #303746
