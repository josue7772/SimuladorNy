import streamlit as st
import numpy as np

st.set_page_config(page_title="SimuladorNy", page_icon="⚽", layout="centered")

# Estilos CSS grises oscuros, metálicos y sin rastros de color azul
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none !important;}
    .viewerBadge_container {display: none !important;}
    [data-testid="stStatusWidget"] {display: none !important;}
    div[data-testid="stToolbar"] {display: none !important;}
    
    .stApp {
        background-color: #090a0f;
        color: #e2e8f0;
        font-family: 'Inter', sans-serif;
    }
    
    .app-card-header {
        background: #12151c;
        padding: 24px;
        border-radius: 16px;
        margin-bottom: 20px;
        border: 1px solid #222733;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }
    
    .league-title {
        font-size: 11px;
        font-weight: 700;
        color: #9ca3af;
        margin-top: 22px;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        border-left: 3px solid #6b7280;
        padding-left: 8px;
    }

    .stat-card-gray {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 14px 18px;
        background: #12151c;
        border-radius: 12px;
        margin-bottom: 10px;
        border: 1px solid #1f2430;
        font-size: 14px;
    }
    
    .prob-container {
        background: #12151c;
        border-radius: 14px;
        padding: 20px;
        margin-top: 20px;
        border: 1px solid #1f2430;
    }
    </style>
""", unsafe_allow_html=True)

# Cobertura global completa de ligas profesionales del mundo
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
    },
    "🇦🇷 Liga Profesional, Argentina": {
        "Boca Juniors vs River Plate": {"local": "Boca Juniors", "visitante": "River Plate", "xg_l": 1.25, "xg_v": 1.20, "c_l": 2.40, "c_x": 3.00, "c_v": 3.10, "corn_l": 5.1, "corn_v": 4.9, "tarjetas": 7},
        "Racing Club vs Independiente": {"local": "Racing", "visitante": "Independiente", "xg_l": 1.35, "xg_v": 1.10, "c_l": 2.15, "c_x": 3.10, "c_v": 3.50, "corn_l": 5.4, "corn_v": 4.2, "tarjetas": 6}
    },
    "🇧🇷 Brasileirão, Brasil": {
        "Flamengo vs Palmeiras": {"local": "Flamengo", "visitante": "Palmeiras", "xg_l": 1.55, "xg_v": 1.30, "c_l": 2.10, "c_x": 3.30, "c_v": 3.40, "corn_l": 6.1, "corn_v": 5.2, "tarjetas": 5},
        "São Paulo vs Corinthians": {"local": "São Paulo", "visitante": "Corinthians", "xg_l": 1.40, "xg_v": 1.15, "c_l": 2.20, "c_x": 3.20, "c_v": 3.30, "corn_l": 5.5, "corn_v": 4.5, "tarjetas": 6}
    }
}

if "vista" not in st.session_state:
    st.session_state["vista"] = "cartelera"
    st.session_state["partido_sel"] = None
    st.session_state["liga_sel"] = None

# VISTA 1: CARTELERA PRINCIPAL
if st.session_state["vista"] == "cartelera":
    st.markdown("""
        <div class="app-card-header">
            <h1 style="color: #ffffff; font-size: 24px; font-weight: 800; margin: 0 0 6px 0;">⚽ SimuladorNy</h1>
            <p style="color: #9ca3af; font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; margin: 0;">Global League Intelligence & Analytics</p>
        </div>
    """, unsafe_allow_html=True)

    busqueda = st.text_input("🔍 Buscar partido o liga...", placeholder="Escribe un equipo (ej. Miami, Madrid, Atlas)...")

    for liga, partidos in cartelera_global.items():
        partidos_filtrados = {k: v for k, v in partidos.items() if busqueda.lower() in k.lower() or busqueda.lower() in liga.lower()}
        if not partidos_filtrados and busqueda:
            continue
        if not partidos_filtrados:
            partidos_filtrados = partidos

        st.markdown(f'<div class="league-title">{liga}</div>', unsafe_allow_html=True)
        for nombre_partido, datos in partidos_filtrados.items():
            if st.button(f"▪️  {datos['local']}   VS   {datos['visitante']}", key=f"btn_{liga}_{nombre_partido}", use_container_width=True):
                st.session_state["partido_sel"] = nombre_partido
                st.session_state["liga_sel"] = liga
                st.session_state["vista"] = "detalle"
                st.rerun()

# VISTA 2: DETALLE INTERACTIVO CON SLIDERS GRISES
elif st.session_state["vista"] == "detalle":
    if st.button("⬅️ Volver a la cartelera"):
        st.session_state["vista"] = "cartelera"
        st.rerun()

    p = cartelera_global[st.session_state["liga_sel"]][st.session_state["partido_sel"]]

    st.markdown(f"""
        <div style="text-align: center; margin: 15px 0 20px 0;">
            <h2 style="color: #ffffff; font-size: 21px; font-weight: 800; margin: 0;">{p['local']} vs {p['visitante']}</h2>
            <p style="color: #9ca3af; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; margin-top: 4px;">Simulador Cuantitativo en Vivo</p>
        </div>
    """, unsafe_allow_html=True)

    # Sliders para interactuar con los xG
    st.markdown("<p style='color: #9ca3af; font-size: 12px; font-weight: 600; margin-bottom: 6px;'>🎛️ Modifica el xG (Goles Esperados) para recalcular:</p>", unsafe_allow_html=True)
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

    # Bloques de estadísticas grises
    st.markdown(f"""
    <div class="stat-card-gray">
        <span style="color: #9ca3af;">Tarjetas amarillas proyectadas</span>
        <span style="color: #ffffff; font-weight: 700;">{p['tarjetas']}</span>
    </div>
    <div class="stat-card-gray">
        <span style="color: #9ca3af;">Tiros de esquina (Córners)</span>
        <span style="color: #e2e8f0; font-weight: 700;">{tot_corners}</span>
    </div>
    <div class="stat-card-gray">
        <span style="color: #9ca3af;">Ambos equipos marcarán (BTTS)</span>
        <span style="color: #ffffff; font-weight: 700;">{btts_texto} ({prob_btts:.0f}%)</span>
    </div>
    <div class="stat-card-gray">
        <span style="color: #9ca3af;">Ganador probable</span>
        <span style="color: #ffffff; font-weight: 700;">{ganador_proyectado}</span>
    </div>
    """, unsafe_allow_html=True)

    # Tarjeta de probabilidades
    st.markdown(f"""
    <div class="prob-container">
        <div style="color: #9ca3af; font-size: 11px; text-align: center; margin-bottom: 14px; text-transform: uppercase; letter-spacing: 1px;">Probabilidad de Victoria en Tiempo Real</div>
        <div style="display: flex; justify-content: space-around; align-items: center; text-align: center;">
            <div>
                <div style="font-size: 20px; font-weight: 800; color: #ffffff;">{prob_l:.0f}%</div>
                <div style="font-size: 11px; color: #9ca3af; margin-top: 3px;">{p['local']}</div>
            </div>
            <div style="color: #2b3240; font-size: 18px;">|</div>
            <div>
                <div style="font-size: 20px; font-weight: 800; color: #ffffff;">{prob_x:.0f}%</div>
                <div style="font-size: 11px; color: #9ca3af; margin-top: 3px;">Empate</div>
            </div>
            <div style="color: #2b3240; font-size: 18px;">|</div>
            <div>
                <div style="font-size: 20px; font-weight: 800; color: #ffffff;">{prob_v:.0f}%</div>
                <div style="font-size: 11px; color: #9ca3af; margin-top: 3px;">{p['visitante']}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
