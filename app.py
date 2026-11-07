import streamlit as st
import numpy as np

st.set_page_config(page_title="SimuladorNy", page_icon="⚽", layout="centered")

st.markdown("""
    <style>
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
    }
    .match-card {
        background-color: #1e293b;
        padding: 16px;
        border-radius: 12px;
        margin-bottom: 12px;
        border: 1px solid #334155;
    }
    </style>
""", unsafe_allow_html=True)

st.title("⚽ SimuladorNy")
st.caption("Cartelera de Partidos & Análisis Cuantitativo")

# Base de datos de partidos directos
PARTIDOS = {
    "🇲🇽 Liga MX": {
        "Pumas vs América": {
            "local": "Pumas", "visitante": "América",
            "xg_l": 1.20, "xg_v": 1.65,
            "c_l": 3.10, "c_x": 3.40, "c_v": 2.20
        }
    },
    "🇪🇸 LaLiga": {
        "Valencia vs Real Madrid": {
            "local": "Valencia", "visitante": "Real Madrid",
            "xg_l": 0.90, "xg_v": 2.10,
            "c_l": 5.50, "c_x": 4.10, "c_v": 1.55
        },
        "Osasuna vs Athletic Club": {
            "local": "Osasuna", "visitante": "Athletic Club",
            "xg_l": 1.10, "xg_v": 1.25,
            "c_l": 2.80, "c_x": 3.10, "c_v": 2.60
        }
    },
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": {
        "Leeds vs Tottenham": {
            "local": "Leeds", "visitante": "Tottenham",
            "xg_l": 1.27, "xg_v": 1.00,
            "c_l": 2.60, "c_x": 3.40, "c_v": 2.65
        }
    }
}

liga_sel = st.selectbox("🏆 Selecciona la Liga", list(PARTIDOS.keys()))
partido_sel = st.selectbox("⚽ Selecciona el Partido", list(PARTIDOS[liga_sel].keys()))

data = PARTIDOS[liga_sel][partido_sel]

# Simulación automática
simulaciones = 10000
goles_l = np.random.poisson(data["xg_l"], simulaciones)
goles_v = np.random.poisson(data["xg_v"], simulaciones)

prob_l = (np.sum(goles_l > goles_v) / simulaciones) * 100
prob_x = (np.sum(goles_l == goles_v) / simulaciones) * 100
prob_v = (np.sum(goles_l < goles_v) / simulaciones) * 100
prob_btts = (np.sum((goles_l > 0) & (goles_v > 0)) / simulaciones) * 100

ev_l = (prob_l / 100) * data["c_l"]
ev_x = (prob_x / 100) * data["c_x"]
ev_v = (prob_v / 100) * data["c_v"]

st.markdown("---")
st.markdown(f"### 📊 {data['local']} vs {data['visitante']}")

st.markdown(f"""
<div class="match-card">
    <div style="color: #94a3b8; font-size: 13px;">Goles esperados (xG)</div>
    <div style="font-size: 18px; font-weight: bold; margin-top: 6px;">
        🔵 {data['local']} <b>{data['xg_l']:.2f}</b> &nbsp;|&nbsp; 🟡 {data['visitante']} <b>{data['xg_v']:.2f}</b>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="match-card">
    <div style="color: #94a3b8; font-size: 13px;">Ambos equipos anotan (AA)</div>
    <div style="font-size: 24px; font-weight: bold; color: #38bdf8; margin-top: 4px;">{prob_btts:.1f}%</div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="match-card">
    <div style="color: #94a3b8; font-size: 13px; text-align: center; margin-bottom: 12px;">Probabilidad de victoria (Moneyline)</div>
    <div style="display: flex; justify-content: space-around; text-align: center;">
        <div>
            <div style="color: #94a3b8; font-size: 12px;">1 · {data['local']}</div>
            <div style="font-size: 22px; font-weight: bold; margin-top: 4px;">{prob_l:.0f}%</div>
            <div style="color: #64748b; font-size: 11px;">Cuota {data['c_l']}</div>
        </div>
        <div>
            <div style="color: #94a3b8; font-size: 12px;">X · Empate</div>
            <div style="font-size: 22px; font-weight: bold; margin-top: 4px;">{prob_x:.0f}%</div>
            <div style="color: #64748b; font-size: 11px;">Cuota {data['c_x']}</div>
        </div>
        <div>
            <div style="color: #94a3b8; font-size: 12px;">2 · {data['visitante']}</div>
            <div style="font-size: 22px; font-weight: bold; margin-top: 4px;">{prob_v:.0f}%</div>
            <div style="color: #64748b; font-size: 11px;">Cuota {data['c_v']}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("### 🎯 Value Bets (Caliente.mx)")
if ev_l > 1.05:
    st.success(f"🔥 **Valor en {data['local']}** — EV: {ev_l:.2f} (Cuota: {data['c_l']})")
if ev_x > 1.05:
    st.success(f"🔥 **Valor en Empate (X)** — EV: {ev_x:.2f} (Cuota: {data['c_x']})")
if ev_v > 1.05:
    st.success(f"🔥 **Valor en {data['visitante']}** — EV: {ev_v:.2f} (Cuota: {data['c_v']})")
if ev_l <= 1.05 and ev_x <= 1.05 and ev_v <= 1.05:
    st.info("ℹ️ Sin valor claro detectado en este partido según las cuotas actuales.")
