import streamlit as st
import numpy as np

st.set_page_config(page_title="SimuladorNy", page_icon="⚽", layout="centered")

# Estilos CSS de alta gama: tipografía limpia y diseño moderno tipo app deportiva
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    .stApp {
        background-color: #0b0f19;
        color: #f8fafc;
        font-family: 'Inter', sans-serif;
    }
    .main-title {
        font-size: 26px;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.5px;
        margin-bottom: 2px;
    }
    .main-subtitle {
        color: #64748b;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin-bottom: 20px;
    }
    .section-header {
        font-size: 15px;
        font-weight: 700;
        color: #f1f5f9;
        margin-top: 20px;
        margin-bottom: 8px;
        letter-spacing: -0.2px;
    }
    .league-header {
        font-size: 12px;
        font-weight: 700;
        color: #94a3b8;
        margin-top: 18px;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        border-left: 2px solid #38bdf8;
        padding-left: 8px;
    }
    .card-analysis {
        background: linear-gradient(135deg, #161e2e 0%, #0f172a 100%);
        padding: 18px;
        border-radius: 14px;
        margin-top: 15px;
        border: 1px solid #1e293b;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }
    .stat-row {
        display: flex;
        justify-content: space-between;
        background: rgba(15, 23, 42, 0.6);
        padding: 10px 14px;
        border-radius: 8px;
        margin-bottom: 6px;
        border: 1px solid rgba(255, 255, 255, 0.02);
    }
    </style>
""", unsafe_allow_html=True)

# Encabezado moderno y limpio
st.markdown('<div class="main-title">⚽ SimuladorNy</div>', unsafe_allow_html=True)
st.markdown('<div class="main-subtitle">Live Analytics & Quantitative Edge</div>', unsafe_allow_html=True)

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

if "partido_activo" not in st.session_state:
    st.session_state["partido_activo"] = "Pumas vs America"
    st.session_state["liga_activa"] = "🇲🇽 Liga MX, Apertura"

st.markdown('<div class="section-header">📅 Partidos del Día</div>', unsafe_allow_html=True)
st.markdown('<span style="color: #64748b; font-size: 12px;">Selecciona un encuentro para desplegar su análisis cuantitativo.</span>', unsafe_allow_html=True)

for liga, partidos in cartelera_global.items():
    st.markdown(f'<div class="league-header">{liga}</div>', unsafe_allow_html=True)
    for nombre_partido, datos in partidos.items():
        if st.button(f"⚡  {datos['local']}  vs  {datos['visitante']}", key=f"btn_{nombre_partido}", use_container_width=True):
            st.session_state["partido_activo"] = nombre_partido
            st.session_state["liga_activa"] = liga

p = cartelera_global[st.session_state["liga_activa"]][st.session_state["partido_activo"]]

# Simulación de Monte Carlo
simulaciones = 10000
goles_l = np.random.poisson(p["xg_l"], simulaciones)
goles_v = np.random.poisson(p["xg_v"], simulaciones)

prob_l = (np.sum(goles_l > goles_v) / simulaciones) * 100
prob_x = (np.sum(goles_l == goles_v) / simulaciones) * 100
prob_v = (np.sum(goles_l < goles_v) / simulaciones) * 100
prob_btts = (np.sum((goles_l > 0) & (goles_v > 0)) / simulaciones) * 100

st.markdown("---")

# Panel de análisis moderno
st.markdown(f"""
<div class="card-analysis">
    <div style="font-size: 17px; font-weight: 700; color: #ffffff; margin-bottom: 14px; text-align: center; letter-spacing: -0.3px;">
        {p['local']} <span style="color: #38bdf8;">VS</span> {p['visitante']}
    </div>
    <div class="stat-row">
        <span style="color: #94a3b8; font-size: 12px; font-weight: 500;">Goles Esperados (xG)</span>
        <span style="color: #f8fafc; font-weight: 600; font-size: 13px;">{p['local']} {p['xg_l']:.2f} &nbsp;|&nbsp; {p['visitante']} {p['xg_v']:.2f}</span>
    </div>
    <div class="stat-row" style="margin-bottom: 0px;">
        <span style="color: #94a3b8; font-size: 12px; font-weight: 500;">Ambos Equipos Anotan (AA)</span>
        <span style="color: #38bdf8; font-weight: 700; font-size: 13px;">{prob_btts:.1f}%</span>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='margin-top: 18px; font-weight: 700; color: #94a3b8; font-size: 11px; text-transform: uppercase; letter-spacing: 1px;'>Probabilidad de Victoria (Moneyline)</div>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label=str(p['local']), value=f"{prob_l:.0f}%", delta=f"Cuota {p['c_l']}")
with col2:
    st.metric(label="Empate", value=f"{prob_x:.0f}%", delta=f"Cuota {p['c_x']}")
with col3:
    st.metric(label=str(p['visitante']), value=f"{prob_v:.0f}%", delta=f"Cuota {p['c_v']}")

st.markdown("---")

st.markdown('<div class="section-header">💡 Análisis Táctico</div>', unsafe_allow_html=True)
favorito = p['local'] if prob_l > prob_v else p['visitante']
max_prob = max(prob_l, prob_v)

analisis_texto = f"""
- **Tendencia Ofensiva:** Las métricas de goles esperados ($xG$) indican un duelo donde **{p['local']}** genera un promedio de **{p['xg_l']}** goles, mientras que **{p['visitante']}** registra **{p['xg_v']}** goles esperados.
- **Probabilidad de Goles:** Existe un **{prob_btts:.1f}%** de probabilidad de que ambos equipos consigan marcar al menos un tanto.
- **Conclusión Táctica:** El modelo proyecta a **{favorito}** con mayor control del trámite ({max_prob:.0f}% de probabilidad de victoria).
"""
st.info(analisis_texto)
