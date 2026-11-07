import streamlit as st
import numpy as np

st.set_page_config(page_title="SimuladorNy", page_icon="⚽", layout="centered")

# Estilos CSS con efecto Glassmorphism (Cristal translúcido) y paleta Gris/Negro Premium tipo editorial de moda/deporte
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none !important;}
    .viewerBadge_container {display: none !important;}
    [data-testid="stStatusWidget"] {display: none !important;}
    div[data-testid="stToolbar"] {display: none !important;}
    
    .stApp {
        background-color: #0b0d10;
        color: #f3f4f6;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Cabecera minimalista editorial */
    .editorial-header {
        text-align: center;
        padding: 30px 20px 15px 20px;
    }
    .brand-title {
        font-size: 24px;
        font-weight: 700;
        letter-spacing: 2px;
        color: #ffffff;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .brand-subtitle {
        font-size: 10px;
        font-weight: 500;
        letter-spacing: 3px;
        color: #6b7280;
        text-transform: uppercase;
    }

    /* Tarjetas flotantes translúcidas estilo glassmorphism */
    .glass-card {
        background: rgba(25, 30, 39, 0.65);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: all 0.3s ease;
    }
    
    .league-section-title {
        font-size: 11px;
        font-weight: 600;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin: 25px 0 10px 4px;
        border-left: 2px solid #4b5563;
        padding-left: 8px;
    }

    .stat-row-clean {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 14px 16px;
        background: rgba(18, 22, 29, 0.8);
        border-radius: 10px;
        margin-bottom: 8px;
        border: 1px solid rgba(255, 255, 255, 0.04);
        font-size: 13px;
    }
    
    .prob-glass-box {
        background: rgba(18, 22, 29, 0.85);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 20px;
        margin-top: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# Cobertura de ligas profesionales mundiales
cartelera_global = {
    "🇺🇸 MLS, Estados Unidos": {
        "LA Galaxy vs Inter Miami": {"local": "LA Galaxy", "visitante": "Inter Miami", "xg_l": 1.75, "xg_v": 1.90, "c_l": 2.45, "c_x": 3.60, "c_v": 2.55, "corn_l": 6.3, "corn_v": 6.7, "tarjetas": 4},
        "LAFC vs NYCFC": {"local": "LAFC", "visitante": "NYCFC", "xg_l": 1.80, "xg_v": 1.25, "c_l": 1.70, "c_x": 3.80, "c_v": 4.50, "corn_l": 6.5, "corn_v": 4.5, "tarjetas": 3},
        "Seattle Sounders vs Portland Timbers": {"local": "Seattle", "visitante": "Portland", "xg_l": 1.50, "xg_v": 1.20, "c_l": 2.00, "c_x": 3.40, "c_v": 3.50, "corn_l": 5.0, "corn_v": 5.0, "tarjetas": 5},
        "Atlanta United vs FC Cincinnati": {"local": "Atlanta", "visitante": "Cincinnati", "xg_l": 1.60, "xg_v": 1.40, "c_l": 2.10, "c_x": 3.50, "c_v": 3.20, "corn_l": 6.0, "corn_v": 4.0, "tarjetas": 4},
        "CF Montréal vs Vancouver Whitecaps": {"local": "CF Montréal", "visitante": "Vancouver", "xg_l": 1.30, "xg_v": 1.25, "c_l": 2.30, "c_x": 3.30, "c_v": 2.90, "corn_l": 4.8, "corn_v": 5.1, "tarjetas": 4},
        "Chicago Fire vs Columbus Crew": {"local": "Chicago", "visitante": "Columbus", "xg_l": 1.20, "xg_v": 1.65, "c_l": 2.80, "c_x": 3.40, "c_v": 2.25, "corn_l": 5.2, "corn_v": 5.8, "tarjetas": 5},
        "D.C. United vs New York Red Bulls": {"local": "D.C. United", "visitante": "Red Bulls", "xg_l": 1.15, "xg_v": 1.30, "c_l": 2.60, "c_x": 3.20, "c_v": 2.50, "corn_l": 4.5, "corn_v": 5.2, "tarjetas": 6},
        "Orlando City vs New England Revolution": {"local": "Orlando", "visitante": "New England", "xg_l": 1.55, "xg_v": 1.10, "c_l": 1.85, "c_x": 3.60, "c_v": 3.90, "corn_l": 5.7, "corn_v": 4.2, "tarjetas": 4},
        "Philadelphia Union vs Toronto FC": {"local": "Philadelphia", "visitante": "Toronto", "xg_l": 1.70, "xg_v": 1.05, "c_l": 1.65, "c_x": 3.75, "c_v": 4.80, "corn_l": 6.1, "corn_v": 3.9, "tarjetas": 3}
    },
    "🇲🇽 Liga MX, México": {
        "Atlas vs Pachuca": {"local": "Atlas", "visitante": "Pachuca", "xg_l": 1.15, "xg_v": 1.40, "c_l": 2.90, "c_x": 3.30, "c_v": 2.40, "corn_l": 5.1, "corn_v": 5.5, "tarjetas": 5},
        "Toluca vs Monterrey": {"local": "Toluca", "visitante": "Monterrey", "xg_l": 1.55, "xg_v": 1.50, "c_l": 2.40, "c_x": 3.30, "c_v": 2.80, "corn_l": 6.0, "corn_v": 5.8, "tarjetas": 4},
        "Tigres vs Cruz Azul": {"local": "Tigres", "visitante": "Cruz Azul", "xg_l": 1.45, "xg_v": 1.35, "c_l": 2.30, "c_x": 3.20, "c_v": 3.00, "corn_l": 5.5, "corn_v": 5.2, "tarjetas": 6},
        "Pumas vs America": {"local": "Pumas", "visitante": "America", "xg_l": 1.20, "xg_v": 1.65, "c_l": 3.10, "c_x": 3.40, "c_v": 2.20, "corn_l": 4.8, "corn_v": 6.2, "tarjetas": 5},
        "Chivas vs Leon": {"local": "Chivas", "visitante": "Leon", "xg_l": 1.40, "xg_v": 1.20, "c_l": 2.10, "c_x": 3.30, "c_v": 3.40, "corn_l": 5.3, "corn_v": 4.7, "tarjetas": 4}
    },
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League, Inglaterra": {
        "Arsenal vs Chelsea": {"local": "Arsenal", "visitante": "Chelsea", "xg_l": 1.75, "xg_v": 1.15, "c_l": 1.75, "c_x": 3.70, "c_v": 4.50, "corn_l": 6.4, "corn_v": 4.9, "tarjetas": 4},
        "Manchester City vs Liverpool": {"local": "Man City", "visitante": "Liverpool", "xg_l": 1.90, "xg_v": 1.65, "c_l": 2.10, "c_x": 3.50, "c_v": 3.20, "corn_l": 7.1, "corn_v": 5.8, "tarjetas": 5},
        "Manchester United vs Tottenham": {"local": "Man United", "visitante": "Tottenham", "xg_l": 1.45, "xg_v": 1.40, "c_l": 2.35, "c_x": 3.40, "c_v": 2.90, "corn_l": 5.6, "corn_v": 5.4, "tarjetas": 5},
        "Aston Villa vs Newcastle": {"local": "Aston Villa", "visitante": "Newcastle", "xg_l": 1.50, "xg_v": 1.35, "c_l": 2.25, "c_x": 3.35, "c_v": 3.05, "corn_l": 5.9, "corn_v": 4.8, "tarjetas": 4}
    },
    "🇪🇸 LaLiga, España": {
        "Real Madrid vs Barcelona": {"local": "Real Madrid", "visitante": "Barcelona", "xg_l": 1.80, "xg_v": 1.70, "c_l": 2.15, "c_x": 3.60, "c_v": 3.00, "corn_l": 6.2, "corn_v": 5.9, "tarjetas": 6},
        "Atletico Madrid vs Sevilla": {"local": "Atletico", "visitante": "Sevilla", "xg_l": 1.55, "xg_v": 0.95, "c_l": 1.65, "c_x": 3.70, "c_v": 5.20, "corn_l": 5.4, "corn_v": 4.1, "tarjetas": 5},
        "Real Sociedad vs Athletic Club": {"local": "Real Sociedad", "visitante": "Athletic", "xg_l": 1.25, "xg_v": 1.15, "c_l": 2.30, "c_x": 3.10, "c_v": 3.20, "corn_l": 4.9, "corn_v": 4.6, "tarjetas": 6},
        "Valencia vs Villarreal": {"local": "Valencia", "visitante": "Villarreal", "xg_l": 1.30, "xg_v": 1.40, "c_l": 2.60, "c_x": 3.30, "c_v": 2.65, "corn_l": 5.1, "corn_v": 5.3, "tarjetas": 4}
    },
    "🇮🇹 Serie A, Italia": {
        "Inter Milan vs AC Milan": {"local": "Inter Milan", "visitante": "AC Milan", "xg_l": 1.60, "xg_v": 1.25, "c_l": 2.05, "c_x": 3.30, "c_v": 3.60, "corn_l": 5.8, "corn_v": 5.0, "tarjetas": 5},
        "Juventus vs Napoli": {"local": "Juventus", "visitante": "Napoli", "xg_l": 1.35, "xg_v": 1.30, "c_l": 2.30, "c_x": 3.10, "c_v": 3.20, "corn_l": 5.3, "corn_v": 5.2, "tarjetas": 4},
        "Roma vs Lazio": {"local": "Roma", "visitante": "Lazio", "xg_l": 1.40, "xg_v": 1.35, "c_l": 2.40, "c_x": 3.20, "c_v": 2.95, "corn_l": 5.5, "corn_v": 5.1, "tarjetas": 7}
    },
    "🇩🇪 Bundesliga, Alemania": {
        "Bayern Munich vs Borussia Dortmund": {"local": "Bayern", "visitante": "Dortmund", "xg_l": 2.30, "xg_v": 1.50, "c_l": 1.50, "c_x": 4.50, "c_v": 5.50, "corn_l": 7.5, "corn_v": 5.3, "tarjetas": 4},
        "Bayer Leverkusen vs Leipzig": {"local": "Leverkusen", "visitante": "Leipzig", "xg_l": 1.85, "xg_v": 1.45, "c_l": 1.95, "c_x": 3.60, "c_v": 3.50, "corn_l": 6.3, "corn_v": 4.9, "tarjetas": 4}
    },
    "🇫🇷 Ligue 1, Francia": {
        "PSG vs Marseille": {"local": "PSG", "visitante": "Marseille", "xg_l": 2.10, "xg_v": 1.10, "c_l": 1.40, "c_x": 4.80, "c_v": 7.00, "corn_l": 6.9, "corn_v": 4.1, "tarjetas": 5},
        "Monaco vs Lyon": {"local": "Monaco", "visitante": "Lyon", "xg_l": 1.65, "xg_v": 1.35, "c_l": 2.05, "c_x": 3.50, "c_v": 3.30, "corn_l": 5.8, "corn_v": 4.7, "tarjetas": 4}
    }
}

if "vista" not in st.session_state:
    st.session_state["vista"] = "cartelera"
    st.session_state["partido_sel"] = None
    st.session_state["liga_sel"] = None

# VISTA 1: CARTELERA PRINCIPAL (Estilo Editorial Premium)
if st.session_state["vista"] == "cartelera":
    st.markdown("""
        <div class="editorial-header">
            <div class="brand-title">SimuladorNy</div>
            <div class="brand-subtitle">Match Intelligence & Analytics</div>
        </div>
    """, unsafe_allow_html=True)

    busqueda = st.text_input("🔍 Buscar encuentro o liga...", placeholder="Escribe un equipo...")

    for liga, partidos in cartelera_global.items():
        partidos_filtrados = {k: v for k, v in partidos.items() if busqueda.lower() in k.lower() or busqueda.lower() in liga.lower()}
        if not partidos_filtrados and busqueda:
            continue
        if not partidos_filtrados:
            partidos_filtrados = partidos

        st.markdown(f'<div class="league-section-title">{liga}</div>', unsafe_allow_html=True)
        for nombre_partido, datos in partidos_filtrados.items():
            if st.button(f"▪️  {datos['local']}   —   {datos['visitante']}", key=f"btn_{liga}_{nombre_partido}", use_container_width=True):
                st.session_state["partido_sel"] = nombre_partido
                st.session_state["liga_sel"] = liga
                st.session_state["vista"] = "detalle"
                st.rerun()

# VISTA 2: DETALLE INTERACTIVO CON EFECTO CRISTAL (Glassmorphism)
elif st.session_state["vista"] == "detalle":
    if st.button("← Volver a la cartelera"):
        st.session_state["vista"] = "cartelera"
        st.rerun()

    p = cartelera_global[st.session_state["liga_sel"]][st.session_state["partido_sel"]]

    st.markdown(f"""
        <div style="text-align: center; margin: 20px 0;">
            <h2 style="color: #ffffff; font-size: 20px; font-weight: 700; letter-spacing: 0.5px; margin: 0;">{p['local']} vs {p['visitante']}</h2>
            <p style="color: #6b7280; font-size: 10px; text-transform: uppercase; letter-spacing: 2px; margin-top: 6px;">Quantitative Match Simulation</p>
        </div>
    """, unsafe_allow_html=True)

    # Sliders Interactivos minimalistas
    st.markdown("<p style='color: #9ca3af; font-size: 11px; font-weight: 500; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px;'>🎛️ Ajuste de Goles Esperados (xG):</p>", unsafe_allow_html=True)
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        xg_l_input = st.slider(f"xG {p['local']}", 0.2, 4.0, float(p['xg_l']), 0.05)
    with col_s2:
        xg_v_input = st.slider(f"xG {p['visitante']}", 0.2, 4.0, float(p['xg_v']), 0.05)

    # Simulador Monte Carlo
    simulaciones = 10000
    goles_l = np.random.poisson(xg_l_input, simulaciones)
    goles_v = np.random.poisson(xg_v_input, simulaciones)

    prob_l = (np.sum(goles_l > goles_v) / simulaciones) * 100
    prob_x = (np.sum(goles_l == goles_v) / simulaciones) * 100
    prob_v = (np.sum(goles_l < goles_v) / simulaciones) * 100
    prob_btts = (np.sum((goles_l > 0) & (goles_v > 0)) / simulaciones) * 100

    tot_corners = round(p["corn_l"] + p["corn_v"], 1)
    ganador_proyectado = p['local'] if prob_l > prob_v else p['visitante']
    btts_texto = "Sí" if prob_btts > 50 else "No"

    st.markdown("<br>", unsafe_allow_html=True)

    # Estadísticas con estilo translúcido
    st.markdown(f"""
    <div class="stat-row-clean">
        <span style="color: #9ca3af;">Tarjetas amarillas proyectadas</span>
        <span style="color: #ffffff; font-weight: 600;">{p['tarjetas']}</span>
    </div>
    <div class="stat-row-clean">
        <span style="color: #9ca3af;">Tiros de esquina (Córners)</span>
        <span style="color: #f3f4f6; font-weight: 600;">{tot_corners}</span>
    </div>
    <div class="stat-row-clean">
        <span style="color: #9ca3af;">Ambos equipos marcarán (BTTS)</span>
        <span style="color: #ffffff; font-weight: 600;">{btts_texto} ({prob_btts:.0f}%)</span>
    </div>
    <div class="stat-row-clean">
        <span style="color: #9ca3af;">Ganador probable</span>
        <span style="color: #ffffff; font-weight: 600;">{ganador_proyectado}</span>
    </div>
    """, unsafe_allow_html=True)

    # Caja de probabilidades estilo cristal esmerilado
    st.markdown(f"""
    <div class="prob-glass-box">
        <div style="color: #6b7280; font-size: 10px; text-align: center; margin-bottom: 14px; text-transform: uppercase; letter-spacing: 2px;">Probabilidad de Victoria en Vivo</div>
        <div style="display: flex; justify-content: space-around; align-items: center; text-align: center;">
            <div>
                <div style="font-size: 19px; font-weight: 700; color: #ffffff;">{prob_l:.0f}%</div>
                <div style="font-size: 10px; color: #9ca3af; margin-top: 3px; text-transform: uppercase; letter-spacing: 0.5px;">{p['local']}</div>
            </div>
            <div style="color: #2b3240; font-size: 16px;">|</div>
            <div>
                <div style="font-size: 19px; font-weight: 700; color: #ffffff;">{prob_x:.0f}%</div>
                <div style="font-size: 10px; color: #9ca3af; margin-top: 3px; text-transform: uppercase; letter-spacing: 0.5px;">Empate</div>
            </div>
            <div style="color: #2b3240; font-size: 16px;">|</div>
            <div>
                <div style="font-size: 19px; font-weight: 700; color: #ffffff;">{prob_v:.0f}%</div>
                <div style="font-size: 10px; color: #9ca3af; margin-top: 3px; text-transform: uppercase; letter-spacing: 0.5px;">{p['visitante']}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
