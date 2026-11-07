import streamlit as st
import numpy as np

st.set_page_config(page_title="SimuladorNy", page_icon="soccer", layout="centered")

st.title("SimuladorNy")
st.caption("Cartelera de Partidos & Analisis Cuantitativo")

# Cartelera global limpia y estandarizada
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
    liga_elegida = st.selectbox("Liga:", list(cartelera_global.keys()))

partidos_disponibles = cartelera_global[liga_elegida]

with col_l2:
    partido_elegido = st.selectbox("Partido:", list(partidos_disponibles.keys()))

p = partidos_disponibles[partido_elegido]

# Monte Carlo simulation
simulaciones = 10000
goles_l = np.random.poisson(p["xg_l"], simulaciones)
goles_v = np.random.poisson(p["xg_v"], simulaciones)

prob_l = (np.sum(goles_l > goles_v) / simulaciones) * 100
prob_x = (np.sum(goles_l == goles_v) / simulaciones) * 100
prob_v = (np.sum(goles_l < goles_v) / simulaciones) * 100
prob_btts = (np.sum((goles_l > 0) & (goles_v > 0)) / simulaciones) * 100

st.divider()

st.subheader(f"{p['local']} vs {p['visitante']}")
st.write(f"Goles esperados (xG): {p['local']} {p['xg_l']:.2f} | {p['visitante']} {p['xg_v']:.2f}")
st.write(f"Ambos equipos anotan (AA): {prob_btts:.1f}%")

st.markdown("---")
st.write("Probabilidad de victoria (Moneyline):")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label=str(p['local']), value=f"{prob_l:.0f}%", delta=f"Cuota {p['c_l']}")
with col2:
    st.metric(label="Empate", value=f"{prob_x:.0f}%", delta=f"Cuota {p['c_x']}")
with col3:
    st.metric(label=str(p['visitante']), value=f"{prob_v:.0f}%", delta=f"Cuota {p['c_v']}")

st.markdown("---")
st.subheader("Deteccion de Valor")

ev_l = (prob_l / 100) * p["c_l"]
ev_x = (prob_x / 100) * p["c_x"]
ev_v = (prob_v / 100) * p["c_v"]

if ev_l > 1.05:
    st.success(f"Hay valor en la victoria de {p['local']} (EV: {ev_l:.2f})")
if ev_x > 1.05:
    st.success(f"Hay valor en el Empate (EV: {ev_x:.2f})")
if ev_v > 1.05:
    st.success(f"Hay valor en la victoria de {p['visitante']} (EV: {ev_v:.2f})")
if ev_l <= 1.05 and ev_x <= 1.05 and ev_v <= 1.05:
    st.info("Sin valor detectado frente a las cuotas actuales.")
