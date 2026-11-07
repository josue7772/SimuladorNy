import streamlit as st
import numpy as np

st.set_page_config(page_title="SimuladorNy", page_icon="⚽", layout="centered")

# Estilos CSS avanzados para eliminar la barra superior, menús de Streamlit y estilizar todo como app nativa
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    /* Ocultar elementos de la interfaz de Streamlit que ensucian la vista */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    
    .stApp {
        background-color: #0b0f19;
        color: #f8fafc;
        font-family: 'Inter', sans-serif;
    }
    .main-title {
        font-size: 24px;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.5px;
        margin-bottom: 2px;
    }
    .main-subtitle {
        color: #64748b;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin-bottom: 15px;
    }
    .section-header {
        font-size: 14px;
        font-weight: 700;
        color: #f1f5f9;
        margin-top: 15px;
        margin-bottom: 6px;
    }
    .league-header {
        font-size: 11px;
        font-weight: 700;
        color: #94a3b8;
        margin-top: 15px;
        margin-bottom: 6px;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        border-left: 2px solid #38bdf8;
        padding-left: 6px;
    }
    .card-analysis {
        background: linear-gradient(135deg, #161e2e 0%, #0f172a 100%);
        padding: 16px;
        border-radius: 14px;
        margin-top: 12px;
        border: 1px solid #1e293b;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }
    .stat-row {
        display: flex;
        justify-content: space-between;
        background: rgba(15, 23, 42, 0.6);
        padding: 9px 12px;
        border-radius: 8px;
        margin-bottom: 5px;
        border: 1px solid rgba(255, 255, 255, 0.02);
    }
    </style>
""", unsafe_allow_html=True)

# Encabezado limpio
st.markdown('<div class="main-title">⚽ SimuladorNy</div>', unsafe_allow_html=True)
st.markdown('<div class="main-subtitle">Global Live Cartelera & Quantitative Analytics</div>', unsafe_allow_html=True)

# Cartelera global
cartelera_global = {
    "🇲🇽 Liga MX, Apertura": {
        "Atlas vs Pachuca": {"local": "Atlas", "visitante": "Pachuca", "xg_l": 1.15, "xg_v": 1.40, "c_l": 2.90, "c_x": 3.30, "c_v": 2.40, "corn_l": 5.1, "corn_v": 5.5},
        "Toluca vs Monterrey": {"local": "Toluca", "visitante": "Monterrey", "xg_l": 1.55, "xg_v": 1.50, "c_l": 2.40, "c_x": 3.30, "c_v": 2.80, "corn_l": 6.0, "corn_v": 5.8},
        "Tigres vs Cruz Azul": {"local": "Tigres", "visitante": "Cruz Azul", "xg_l": 1.45, "xg_v": 1.35, "c_l": 2.30, "c_x": 3.20, "c_v": 3.00, "corn_l": 5.5, "corn_v": 5.2},
        "Pumas vs America": {"local": "Pumas", "visitante": "America", "xg_l": 1.20, "xg_v": 1.65, "c_l": 3.10, "c_x": 3.40, "c_v": 2.20, "corn_l": 4.8, "corn_v": 6.2}
    },
    "🇺🇸 MLS, Estados Unidos": {
        "LA Galaxy vs Inter Miami": {"local": "LA Galaxy", "visitante": "Inter Miami", "xg_l": 1.75, "xg_v": 1.90, "c_l": 2.45, "c_x": 3.60, "c_v": 2.55, "corn_l": 6.3, "corn_v": 6.7},
        "LAFC vs New York City": {"local": "LAFC", "visitante": "NYCFC", "xg_l": 1.80, "xg_v": 1.25, "c_l": 1.70, "c_x": 3.80, "c_v": 4.50, "corn_l": 6.5, "corn_v": 4.5}
    },
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 FA Cup, Inglaterra": {
        "Manchester United vs Liverpool": {"local": "Man United", "visitante": "Liverpool", "xg_l": 1.50, "xg_v": 1.85, "c_l": 3.20, "c_x": 3.50, "c_v": 2.15, "corn_l": 5.2, "corn_v": 6.8}
    },
    "🇪🇸 LaLiga, España": {
        "Valencia vs Real Madrid": {"local": "Valencia", "visitante": "Real Madrid", "xg_l": 0.90, "xg_v": 2.10, "c_l": 5.50, "c_x": 4.10, "c_v": 1.55, "corn_l": 4.0, "corn_v": 6.5},
        "Barcelona vs Atletico Madrid": {"local": "Barcelona", "visitante": "Atletico Madrid", "xg_l": 1.85, "xg_v": 1.20, "c_l": 1.80, "c_x": 3.60, "c_v": 4.20, "corn_l": 6.2, "corn_v": 4.8}
    },
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League, Inglaterra": {
        "Arsenal vs Chelsea": {"local": "Arsenal", "visitante": "Chelsea", "xg_l": 1.75, "xg_v": 1.15, "c_l": 1.75, "c_x": 3.70, "c_v": 4.50, "corn_l": 6.4, "corn_v": 4.9},
        "Manchester City vs Tottenham": {"local": "Man City", "visitante": "Tottenham", "xg_l": 2.10, "xg_v": 1.30, "c_l": 1.45, "c_x": 4.60, "c_v": 6.00, "corn_l": 7.1, "corn_v": 4.2}
    },
    "🇮🇹 Serie A, Italia": {
        "Inter Milan vs AC Milan": {"local": "Inter Milan", "visitante": "AC Milan", "xg_l": 1.60, "xg_v": 1.25, "c_l": 2.05, "c_x": 3.30, "c_v": 3.60, "corn_l": 5.8, "corn_v": 5.0},
        "Juventus vs Napoli": {"local": "Juventus", "visitante": "Napoli", "xg_l": 1.35, "xg_v": 1.30, "c_l": 2.30, "c_x": 3.10, "c_v": 3.20, "corn_l": 5.3, "corn_v": 5.2}
    },
    "🇩🇪 Bundesliga, Alemania": {
        "Bayern Munich vs Borussia Dortmund": {"local": "Bayern", "visitante": "Dortmund", "xg_l": 2.30, "xg_v": 1.50, "c_l": 1.50, "c_x": 4.50, "c_v": 5.50, "corn_l": 7.5, "corn_v": 5.3}
    },
    "🇫🇷 Ligue 1, Francia": {
        "PSG vs Marseille": {"local": "PSG", "visitante": "Marseille", "xg_l": 2.10, "xg_v": 1.10, "c_l": 1.40, "c_x": 4.80, "c_v": 7.00, "corn_l": 6.9, "corn_v": 4.1}
    }
}

if "liga_activa" not in st.session_state or st.session_state["liga_activa"] not in cartelera_global:
    st.session_state["liga_activa"] = list(cartelera_global.keys())[0]

if "partido_activo" not in st.session_state or st.session_state["partido_activo"] not in cartelera_global[st.session_state["liga_activa"]]:
    st.session_state["partido_activo"] = list(cartelera_global[st.session_state["liga_activa"]].keys())[0]

st.markdown('<div class="section-header">📅 Cartelera Mundial de Partidos</div>', unsafe_allow_html=True)
st.markdown('<span style="color: #64748b; font-size: 11px;">Toca un encuentro para ver su análisis:</span>', unsafe_allow_html=True)

for liga, partidos in cartelera_global.items():
    st.markdown(f'<div class="league-header">{liga}</div>', unsafe_allow_html=True)
    for nombre_partido, datos in partidos.items():
        if st.button(f"⚡  {datos['local']}  vs  {datos['visitante']}", key=f"btn_{liga}_{nombre_partido}", use_container_width=True):
            st.session_state["partido_activo"] = nombre_partido
            st.session_state["liga_activa"] = liga

p = cartelera_global[st.session_state["liga_activa"]][st.session_state["partido_activo"]]

# Simulacion de Monte Carlo
simulaciones = 10000
goles_l = np.random.poisson(p["xg_l"], simulaciones)
goles_v = np.random.poisson(p["xg_v"], simulaciones)

prob_l = (np.sum(goles_l > goles_v) / simulaciones) * 100
prob_x = (np.sum(goles_l == goles_v) / simulaciones) * 100
prob_v = (np.sum(goles_l < goles_v) / simulaciones) * 100
prob_btts = (np.sum((goles_l > 0) & (goles_v > 0)) / simulaciones) * 100

corners_totales = p["corn_l"] + p["corn_v"]

st.markdown("---")

# Panel de análisis moderno limpio
st.markdown(f"""
<div class="card-analysis">
    <div style="font-size: 16px; font-weight: 700; color: #ffffff; margin-bottom: 12px; text-align: center;">
        {p['local']} <span style="color: #38bdf8;">VS</span> {p['visitante']}
    </div>
    <div class="stat-row">
        <span style="color: #94a3b8; font-size: 11px;">Goles Esperados (xG)</span>
        <span style="color: #f8fafc; font-weight: 600; font-size: 12px;">{p['local']} {p['xg_l']:.2f} | {p['visitante']} {p['xg_v']:.2f}</span>
    </div>
    <div class="stat-row">
        <span style="color: #94a3b8; font-size: 11px;">Ambos Equipos Anotan (AA)</span>
        <span style="color: #38bdf8; font-weight: 700; font-size: 12px;">{prob_btts:.1f}%</span>
    </div>
    <div class="stat-row">
        <span style="color: #94a3b8; font-size: 11px;">Promedio Córners (Equipo)</span>
        <span style="color: #f8fafc; font-weight: 600; font-size: 12px;">{p['local']} {p['corn_l']} | {p['visitante']} {p['corn_v']}</span>
    </div>
    <div class="stat-row" style="margin-bottom: 0px;">
        <span style="color: #94a3b8; font-size: 11px;">Total Córners Proyectados</span>
        <span style="color: #38bdf8; font-weight: 700; font-size: 12px;">{corners_totales:.1f} córners</span>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='margin-top: 15px; font-weight: 700; color: #94a3b8; font-size: 10px; text-transform: uppercase; letter-spacing: 1px;'>Probabilidad de Victoria (Moneyline)</div>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label=str(p['local']), value=f"{prob_l:.0f}%", delta=f"Cuota {p['c_l']}")
with col2:
    st.metric(label="Empate", value=f"{prob_x:.0f}%", delta=f"Cuota {p['c_x']}")
with col3:
    st.metric(label=str(p['visitante']), value=f"{prob_v:.0f}%", delta=f"Cuota {p['c_v']}")

st.markdown("---")

st.markdown('<div class="section-header">💡 Análisis Táctico & Estadístico</div>', unsafe_allow_html=True)
favorito = p['local'] if prob_l > prob_v else p['visitante']
max_prob = max(prob_l, prob_v)

analisis_texto = f"""
- **Tendencia Ofensiva y Goles:** El modelo proyecta **{p['xg_l']} xG** para **{p['local']}** frente a **{p['xg_v']} xG** de **{p['visitante']}**. La probabilidad de que ambos anoten es del **{prob_btts:.1f}%**.
- **Saques de Esquina:** Se anticipan **{corners_totales:.1f} córners** totales, con aportes individuales de **{p['corn_l']}** para **{p['local']}** y **{p['corn_v']}** para **{p['visitante']}**.
- **Conclusión:** Se otorga favoritismo a **{favorito}** con un **{max_prob:.0f}%** de probabilidad de triunfo.
"""
st.info(analisis_texto)
