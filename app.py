import streamlit as st
import numpy as np

st.set_page_config(page_title="SimuladorNy", page_icon="⚽", layout="centered")

# Estilos CSS personalizados para darle un look moderno tipo Sofascore
st.markdown("""
    <style>
    .stApp {
        background-color: #0b0f19;
        color: #f8fafc;
    }
    .card-match {
        background-color: #161e2e;
        padding: 16px;
        border-radius: 14px;
        margin-bottom: 15px;
        border: 1px solid #233044;
    }
    .metric-label {
        color: #94a3b8;
        font-size: 13px;
        font-weight: 500;
    }
    .metric-value {
        color: #ffffff;
        font-size: 24px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

st.title("⚽ SimuladorNy")
st.caption("Cartelera de Partidos & Análisis Cuantitativo")

# Cartelera global
cartelera_global = {
    "Liga MX": {
        "Pumas vs America": {"local": "Pumas", "visitante": "America", "xg_l": 1.20, "xg_v": 1.65, "c_l": 3.10, "c_x": 3.40, "c_v": 2.20},
        "Cruz Azul vs Tigres": {"local": "Cruz Azul", "visitante": "Tigres", "xg_l": 1.45, "xg_v": 1.35, "c_l": 2.30, "c_x": 3.20, "c_v": 3.00},
        "Monterrey vs Chivas": {"local": "Monterrey", "visitante": "Chivas", "xg_l": 1.70, "xg_v": 1.10, "c_l": 1.95, "c_x": 3.50, "c_v": 3.80},
        "Atlas vs Toluca": {"local": "Atlas", "visitante": "Toluca", "xg_l": 1.15, "xg_v": 1.40, "c_l": 2.90, "c_x": 3.30, "c_v": 2.40}
    },
    "LaLiga": {
        "Valencia vs Real Madrid": {"local": "Valencia", "visitante": "Real Madrid", "xg_l": 0.90, "xg_v": 2.10, "c_l": 5.50, "c_x": 4.10, "c_v": 1.55},
        "Osasuna vs Athletic Club": {"local": "Osasuna", "visitante": "Athletic Club", "xg_l": 1.10, "xg_v": 1.25, "c_l": 2.80, "c_x": 3.10, "c_v": 2.60},
        "Barcelona vs Atletico Madrid": {"local": "Barcelona", "visitante": "Atletico Madrid", "xg_l": 1.85, "xg_v": 1.20, "c_l": 1.80, "c_x": 3.60, "c_v": 4.20},
        "Sevilla vs Real Betis": {"local": "Sevilla", "visitante": "Real Betis", "xg_l": 1.30, "xg_v": 1.30, "c_l": 2.50, "c_x": 3.20, "c_v": 2.80}
    },
    "Premier League": {
        "Leeds vs Tottenham": {"local": "Leeds", "visitante": "Tottenham", "xg_l": 1.27, "xg_v": 1.00, "c_l": 2.60, "c_x": 3.40, "c_v": 2.65},
        "Arsenal vs Chelsea": {"local": "Arsenal", "visitante": "Chelsea", "xg_l": 1.75, "xg_v": 1.15, "c_l": 1.75, "c_x": 3.70, "c_v": 4.50},
        "Manchester City vs Liverpool": {"local": "Man City", "visitante": "Liverpool", "xg_l": 1.90, "xg_v": 1.65, "c_l": 2.10, "c_x": 3.50, "c_v": 3.20},
        "Manchester United vs Newcastle": {"local": "Man United", "visitante": "Newcastle", "xg_l": 1.40, "xg_v": 1.40, "c_l": 2.40, "c_x": 3.40, "c_v": 2.90}
    },
    "Serie A": {
        "Inter Milan vs AC Milan": {"local": "Inter Milan", "visitante": "AC Milan", "xg_l": 1.60, "xg_v": 1.25, "c_l": 2.05, "c_x": 3.30, "c_v": 3.60},
        "Juventus vs Napoli": {"local": "Juventus", "visitante": "Napoli", "xg_l": 1.35, "xg_v": 1.30, "c_l": 2.30, "c_x": 3.10, "c_v": 3.20}
    },
    "Bundesliga": {
        "Bayern Munich vs Borussia Dortmund": {"local": "Bayern", "visitante": "Dortmund", "xg_l": 2.30, "xg_v": 1.50, "c_l": 1.50, "c_x": 4.50, "c_v": 5.50},
        "RB Leipzig vs Bayer Leverkusen": {"local": "RB Leipzig", "visitante": "Leverkusen", "xg_l": 1.55, "xg_v": 1.60, "c_l": 2.60, "c_x": 3.50, "c_v": 2.50}
    }
}

col_l1, col_l2 = st.columns(2)
with col_l1:
    liga_elegida = st.selectbox("🏆 Liga", list(cartelera_global.keys()))

partidos_disponibles = cartelera_global[liga_elegida]

with col_l2:
    partido_elegido = st.selectbox("⚽ Partido", list(partidos_disponibles.keys()))

p = partidos_disponibles[partido_elegido]

# Simulación Monte Carlo
simulaciones = 10000
goles_l = np.random.poisson(p["xg_l"], simulaciones)
goles_v = np.random.poisson(p["xg_v"], simulaciones)

prob_l = (np.sum(goles_l > goles_v) / simulaciones) * 100
prob_x = (np.sum(goles_l == goles_v) / simulaciones) * 100
prob_v = (np.sum(goles_l < goles_v) / simulaciones) * 100
prob_btts = (np.sum((goles_l > 0) & (goles_v > 0)) / simulaciones) * 100

st.markdown("---")

# Tarjeta Principal de Partido
st.markdown(f"""
<div class="card-match">
    <div style="font-size: 20px; font-weight: bold; color: #ffffff; margin-bottom: 12px; text-align: center;">
        {p['local']} vs {p['visitante']}
    </div>
    <div style="display: flex; justify-content: space-between; background: #0b0f19; padding: 10px; border-radius: 8px; margin-bottom: 8px;">
        <span class="metric-label">Goles Esperados (xG)</span>
        <span style="color: #38bdf8; font-weight: bold;">{p['local']} {p['xg_l']:.2f} | {p['visitante']} {p['xg_v']:.2f}</span>
    </div>
    <div style="display: flex; justify-content: space-between; background: #0b0f19; padding: 10px; border-radius: 8px;">
        <span class="metric-label">Ambos Equipos Anotan (AA)</span>
        <span style="color: #38bdf8; font-weight: bold;">{prob_btts:.1f}%</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Tarjeta de Probabilidades Moneyline en Columnas Horizontales
st.markdown("""
<div class="card-match">
    <div class="metric-label" style="text-align: center; margin-bottom: 10px;">PROBABILIDAD DE VICTORIA (MONEYLINE)</div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label=str(p['local']), value=f"{prob_l:.0f}%", delta=f"Cuota {p['c_l']}")
with col2:
    st.metric(label="Empate", value=f"{prob_x:.0f}%", delta=f"Cuota {p['c_x']}")
with col3:
    st.metric(label=str(p['visitante']), value=f"{prob_v:.0f}%", delta=f"Cuota {p['c_v']}")

# Detección de Valor estilizada
st.markdown("---")
st.markdown("### 🎯 Detección de Valor (Caliente.mx)")

ev_l = (prob_l / 100) * p["c_l"]
ev_x = (prob_x / 100) * p["c_x"]
ev_v = (prob_v / 100) * p["c_v"]

hay_alerta = False
if ev_l > 1.05:
    st.success(f"🔥 **¡Valor detectado!** Apuesta recomendada a favor de **{p['local']}** (EV: {ev_l:.2f})")
    hay_alerta = True
if ev_x > 1.05:
    st.success(f"🔥 **¡Valor detectado!** Apuesta recomendada al **Empate** (EV: {ev_x:.2f})")
    hay_alerta = True
if ev_v > 1.05:
    st.success(f"🔥 **¡Valor detectado!** Apuesta recomendada a favor de **{p['visitante']}** (EV: {ev_v:.2f})")
    hay_alerta = True

if not hay_alerta:
    st.info("ℹ️ Mercado estable. Sin valor claro detectado frente a las cuotas actuales.")
