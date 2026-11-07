import streamlit as st
import numpy as np

st.set_page_config(page_title="SimuladorNy", page_icon="⚽", layout="centered")

st.title("SimuladorNy - Cartelera de Partidos")
st.write("Selecciona un partido para ver el análisis de goles esperados y probabilidades.")

# Base de datos de partidos
partidos_data = {
    "Liga MX: Pumas vs America": {
        "local": "Pumas", "visitante": "America",
        "xg_l": 1.20, "xg_v": 1.65,
        "cuota_l": 3.10, "cuota_x": 3.40, "cuota_v": 2.20
    },
    "LaLiga: Valencia vs Real Madrid": {
        "local": "Valencia", "visitante": "Real Madrid",
        "xg_l": 0.90, "xg_v": 2.10,
        "cuota_l": 5.50, "cuota_x": 4.10, "cuota_v": 1.55
    },
    "Premier League: Leeds vs Tottenham": {
        "local": "Leeds", "visitante": "Tottenham",
        "xg_l": 1.27, "xg_v": 1.00,
        "cuota_l": 2.60, "cuota_x": 3.40, "cuota_v": 2.65
    }
}

seleccion = st.selectbox("Elige un partido del dia:", list(partidos_data.keys()))
p = partidos_data[seleccion]

# Simulacion automatica
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
st.write("Probabilidad de victoria:")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label=p['local'], value=f"{prob_l:.0f}%", delta=f"Cuota {p['cuota_l']}")
with col2:
    st.metric(label="Empate", value=f"{prob_x:.0f}%", delta=f"Cuota {p['cuota_x']}")
with col3:
    st.metric(label=p['visitante'], value=f"{prob_v:.0f}%", delta=f"Cuota {p['cuota_v']}")

st.markdown("---")
st.subheader("Detección de Valor")

ev_l = (prob_l / 100) * p["cuota_l"]
ev_v = (prob_v / 100) * p["cuota_v"]

if ev_l > 1.05:
    st.success(f"Hay valor en la victoria de {p['local']} (EV: {ev_l:.2f})")
elif ev_v > 1.05:
    st.success(f"Hay valor en la victoria de {p['visitante']} (EV: {ev_v:.2f})")
else:
    st.info("Sin valor detectado frente a las cuotas actuales.")
