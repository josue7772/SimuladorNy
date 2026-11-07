import streamlit as st
import numpy as np

st.set_page_config(page_title="SimuladorNy", page_icon="soccer", layout="centered")

# Estilos CSS estilo Sofascore (Dark Theme moderno)
st.markdown("""
    <style>
    .stApp {
        background-color: #0b0f19;
        color: #f8fafc;
    }
    .league-card {
        background-color: #161e2e;
        padding: 14px;
        border-radius: 12px;
        margin-bottom: 16px;
        border: 1px solid #233044;
    }
    .match-row {
        padding: 8px 0px;
        border-bottom: 1px solid #1f293d;
        font-size: 15px;
    }
    .card-match {
        background-color: #161e2e;
        padding: 18px;
        border-radius: 14px;
        margin-bottom: 15px;
        border: 1px solid #233044;
    }
    .metric-label {
        color: #94a3b8;
        font-size: 13px;
        font-weight: 500;
    }
    </style>
""", unsafe_allow_html=True)

st.title("SimuladorNy")
st.caption("Cartelera en Vivo & Analisis Cuantitativo")

# Cartelera global organizada por ligas (Simulando Sofascore)
cartelera_global = {
    "Liga MX, Apertura": {
        "Atlas vs Pachuca": {"local": "Atlas", "visitante": "Pachuca", "xg_l": 1.15, "xg_v": 1.40, "c_l": 2.90, "c_x": 3.30, "c_v": 2.40},
        "Toluca vs Monterrey": {"local": "Toluca", "visitante": "Monterrey", "xg_l": 1.55, "xg_v": 1.50, "c_l": 2.40, "c_x": 3.30, "c_v": 2.80},
        "Tigres vs Cruz Azul": {"local": "Tigres", "visitante": "Cruz Azul", "xg_l": 1.45, "xg_v": 1.35, "c_l": 2.30, "c_x": 3.20, "c_v": 3.00},
        "Pumas vs America": {"local": "Pumas", "visitante": "America", "xg_l": 1.20, "xg_v": 1.65, "c_l": 3.10, "c_x": 3.40, "c_v": 2.20}
    },
    "LaLiga, Espana": {
        "Valencia vs Real Madrid": {"local": "Valencia", "visitante": "Real Madrid", "xg_l": 0.90, "xg_v": 2.10, "c_l": 5.50, "c_x": 4.10, "c_v": 1.55},
        "Osasuna vs Athletic Club": {"local": "Osasuna", "visitante": "Athletic Club", "xg_l": 1.10, "xg_v": 1.25, "c_l": 2.80, "c_x": 3.10, "c_v": 2.60},
        "Barcelona vs Atletico Madrid": {"local": "Barcelona", "visitante": "Atletico Madrid", "xg_l": 1.85, "xg_v": 1.20, "c_l": 1.80, "c_x": 3.60, "c_v": 4.20}
    },
    "Premier League, Inglaterra": {
        "Leeds vs Tottenham": {"local": "Leeds", "visitante": "Tottenham", "xg_l": 1.27, "xg_v": 1.00, "c_l": 2.60, "c_x": 3.40, "c_v": 2.65},
        "Arsenal vs Chelsea": {"local": "Arsenal", "visitante": "Chelsea", "xg_l": 1.75, "xg_v": 1.15, "c_l": 1.75, "c_x": 3.70, "c_v": 4.50},
        "Manchester City vs Liverpool": {"local": "Man City", "visitante": "Liverpool", "xg_l": 1.90, "xg_v": 1.65, "c_l": 2.10, "c_x": 3.50, "c_v": 3.20}
    }
}

# Crear lista plana de todos los partidos disponibles para un selector directo tipo cartelera
opciones_partidos = []
mapa_partidos = {}

for liga, partidos in cartelera_global.items():
    for partido, datos in partidos.items():
        etiqueta = f"[{liga}] {partido}"
        opciones_partidos.append(etiqueta)
        mapa_partidos[etiqueta] = datos

st.markdown("### Cartelera del Dia")
partido_seleccionado = st.selectbox("Selecciona un partido para ver el analisis:", opciones_partidos)

p = mapa_partidos[partido_seleccionado]

# Simulacion automatica de Monte Carlo
simulaciones = 10000
goles_l = np.random.poisson(p["xg_l"], simulaciones)
goles_v = np.random.poisson(p["xg_v"], simulaciones)

prob_l = (np.sum(goles_l > goles_v) / simulaciones) * 100
prob_x = (np.sum(goles_l == goles_v) / simulaciones) * 100
prob_v = (np.sum(goles_l < goles_v) / simulaciones) * 100
prob_btts = (np.sum((goles_l > 0) & (goles_v > 0)) / simulaciones) * 100

st.markdown("---")

# Tarjeta de Datos del Partido
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

# Tarjeta de Probabilidades Moneyline
st.markdown("""
<div class="card-match" style="padding-bottom: 5px;">
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

st.markdown("---")

# Análisis Breve del Partido (Reemplazando la detección de valor)
st.markdown("### Analisis Breve del Encuentro")

# Generar un resumen dinámico inteligente basado en los xG y probabilidades
favorito = p['local'] if prob_l > prob_v else p['visitante']
max_prob = max(prob_l, prob_v)

analisis_texto = f"""
- **Tendencia Ofensiva:** Las métricas de goles esperados ($xG$) indican un duelo donde **{p['local']}** genera un promedio de **{p['xg_l']}** goles por encuentro, mientras que **{p['visitante']}** registra **{p['xg_v']}** goles esperados.
- **Probabilidad de Goles:** Existe una probabilidad del **{prob_btts:.1f}%** de que ambos equipos consigan marcar al menos un tanto durante los 90 minutos regulatorios.
- **Conclusion Tactica:** El modelo estadístico proyecta a **{favorito}** con mayor control del trámite del partido ({max_prob:.0f}% de probabilidad de victoria), aunque las cuotas de mercado sugieren un margen estrecho que exige precaución táctica en las líneas de apuestas.
"""

st.info(analisis_texto)
