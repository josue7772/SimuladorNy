import streamlit as st
import numpy as np

st.set_page_config(page_title="SimuladorNy", page_icon="⚽", layout="centered")

# Estilos idénticos a Sofascore (Dark Theme moderno)
st.markdown("""
    <style>
    .stApp {
        background-color: #0b0f19;
        color: #f8fafc;
    }
    .league-header {
        font-size: 15px;
        font-weight: bold;
        color: #94a3b8;
        margin-top: 20px;
        margin-bottom: 8px;
        padding-left: 5px;
        border-left: 3px solid #38bdf8;
    }
    .match-card {
        background-color: #161e2e;
        padding: 14px 16px;
        border-radius: 12px;
        margin-bottom: 10px;
        border: 1px solid #233044;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .team-name {
        font-size: 15px;
        font-weight: 600;
        color: #f8fafc;
    }
    .card-analysis {
        background-color: #161e2e;
        padding: 18px;
        border-radius: 14px;
        margin-top: 15px;
        border: 1px solid #38bdf8;
    }
    </style>
""", unsafe_allow_html=True)

st.title("⚽ SimuladorNy")
st.caption("Cartelera en Vivo & Análisis Cuantitativo")

# Cartelera global organizada
cartelera_global = {
    "🇲🇽 Liga MX, Apertura": {
        "Atlas vs Pachuca": {"local": "Atlas", "visitante": "Pachuca", "xg_l": 1.15, "xg_v": 1.40, "c_l": 2.90, "c_x": 3.30, "c_v": 2.40},
        "Toluca vs Monterrey": {"local": "Toluca", "visitante": "Monterrey", "xg_l": 1.55, "xg_v": 1.50, "c_l": 2.40, "c_x": 3.30, "c_v": 2.80},
        "Tigres vs Cruz Azul": {"local": "Tigres", "visitante": "Cruz Azul", "xg_l": 1.45, "xg_v": 1.35, "c_l": 2.30, "c_x": 3.20, "c_v": 3.00},
        "Pumas vs America": {"local": "Pumas", "visitante": "America", "xg_l": 1.20, "xg_v": 1.65, "c_l": 3.10, "c_x": 3.40, "c_v": 2.20}
    },
    "🇪🇸 LaLiga, España": {
        "Valencia vs Real Madrid": {"local": "Valencia", "visitante": "Real Madrid", "xg_l": 0.90, "xg_v": 2.10, "c_l": 5.50, "c_x": 4.10, "c_v": 1.55},
        "Osasuna vs Athletic Club": {"local": "Osasuna", "visitante": "Athletic Club", "xg_l": 1.10, "xg_v": 1.25, "c_l": 2.80, "c_x": 3.10, "c_v": 2.60},
        "Barcelona vs Atletico Madrid": {"local": "Barcelona", "visitante": "Atletico Madrid", "xg_l": 1.85, "xg_v": 1.20, "c_l": 1.80, "c_x": 3.60, "c_v": 4.20}
    },
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League, Inglaterra": {
        "Leeds vs Tottenham": {"local": "Leeds", "visitante": "Tottenham", "xg_l": 1.27, "xg_v": 1.00, "c_l": 2.60, "c_x": 3.40, "c_v": 2.65},
        "Arsenal vs Chelsea": {"local": "Arsenal", "visitante": "Chelsea", "xg_l": 1.75, "xg_v": 1.15, "c_l": 1.75, "c_x": 3.70, "c_v": 4.50},
        "Manchester City vs Liverpool": {"local": "Man City", "visitante": "Liverpool", "xg_l": 1.90, "xg_v": 1.65, "c_l": 2.10, "c_x": 3.50, "c_v": 3.20}
    }
}

# Variable de estado para recordar qué partido seleccionó el usuario de la lista
if "partido_activo" not in st.session_state:
    st.session_state["partido_activo"] = "Pumas vs America"
    st.session_state["liga_activa"] = "🇲🇽 Liga MX, Apertura"

st.markdown("### 📋 Cartelera del Día")
st.write("Toca cualquier partido para desplegar su análisis completo:")

# Renderizar listado idéntico a Sofascore por bloques de liga
for liga, partidos in cartelera_global.items():
    st.markdown(f'<div class="league-header">{liga}</div>', unsafe_allow_html=True)
    for nombre_partido, datos in partidos.items():
        # Usar botones limpios que simulan las filas de partidos de la app
        if st.button(f"⚽  {datos['local']}  vs  {datos['visitante']}", key=f"btn_{nombre_partido}", use_container_width=True):
            st.session_state["partido_activo"] = nombre_partido
            st.session_state["liga_activa"] = liga

# Obtener datos del partido activo actual
p = cartelera_global[st.session_state["liga_activa"]][st.session_state["partido_activo"]]

# Simulación de Monte Carlo automática
simulaciones = 10000
goles_l = np.random.poisson(p["xg_l"], simulaciones)
goles_v = np.random.poisson(p["xg_v"], simulaciones)

prob_l = (np.sum(goles_l > goles_v) / simulaciones) * 100
prob_x = (np.sum(goles_l == goles_v) / simulaciones) * 100
prob_v = (np.sum(goles_l < goles_v) / simulaciones) * 100
prob_btts = (np.sum((goles_l > 0) & (goles_v > 0)) / simulaciones) * 100

st.markdown("---")

# Panel de análisis detallado del partido seleccionado
st.markdown(f"""
<div class="card-analysis">
    <div style="font-size: 18px; font-weight: bold; color: #ffffff; margin-bottom: 12px; text-align: center;">
        📊 Análisis Seleccionado: {p['local']} vs {p['visitante']}
    </div>
    <div style="display: flex; justify-content: space-between; background: #0b0f19; padding: 10px; border-radius: 8px; margin-bottom: 8px;">
        <span style="color: #94a3b8; font-size: 13px;">Goles Esperados (xG)</span>
        <span style="color: #38bdf8; font-weight: bold;">{p['local']} {p['xg_l']:.2f} | {p['visitante']} {p['xg_v']:.2f}</span>
    </div>
    <div style="display: flex; justify-content: space-between; background: #0b0f19; padding: 10px; border-radius: 8px;">
        <span style="color: #94a3b8; font-size: 13px;">Ambos Equipos Anotan (AA)</span>
        <span style="color: #38bdf8; font-weight: bold;">{prob_btts:.1f}%</span>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='margin-top: 15px; font-weight: bold; color: #94a3b8; font-size: 12px;'>PROBABILIDAD DE VICTORIA (MONEYLINE)</div>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label=str(p['local']), value=f"{prob_l:.0f}%", delta=f"Cuota {p['c_l']}")
with col2:
    st.metric(label="Empate", value=f"{prob_x:.0f}%", delta=f"Cuota {p['c_x']}")
with col3:
    st.metric(label=str(p['visitante']), value=f"{prob_v:.0f}%", delta=f"Cuota {p['c_v']}")

st.markdown("---")

# Análisis Breve del Encuentro
st.markdown("### 💡 Análisis del Partido")
favorito = p['local'] if prob_l > prob_v else p['visitante']
max_prob = max(prob_l, prob_v)

analisis_texto = f"""
- **Tendencia Ofensiva:** Las métricas de goles esperados ($xG$) indican un duelo donde **{p['local']}** genera un promedio de **{p['xg_l']}** goles, mientras que **{p['visitante']}** registra **{p['xg_v']}** goles esperados.
- **Probabilidad de Goles:** Existe un **{prob_btts:.1f}%** de probabilidad de que ambos equipos consigan marcar al menos un tanto.
- **Conclusión Táctica:** El modelo proyecta a **{favorito}** con mayor control del trámite ({max_prob:.0f}% de probabilidad de victoria).
"""
st.info(analisis_texto)
