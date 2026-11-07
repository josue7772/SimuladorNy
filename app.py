import streamlit as st
import numpy as np
import requests

st.set_page_config(page_title="SimuladorNy", page_icon="⚽", layout="centered")

# Estilos CSS avanzados para ocultar basura de Streamlit y mantener el diseño limpio
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
        background-color: #0d1117;
        color: #f8fafc;
        font-family: 'Inter', sans-serif;
    }
    .league-header {
        font-size: 12px;
        font-weight: 700;
        color: #8b949e;
        margin-top: 18px;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        border-left: 2px solid #38bdf8;
        padding-left: 8px;
    }
    .match-header-title {
        font-size: 20px;
        font-weight: 800;
        color: #ffffff;
        text-align: center;
        margin-bottom: 20px;
    }
    .stat-row-clean {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 14px 4px;
        border-bottom: 1px solid #161b22;
        font-size: 15px;
    }
    .stat-label {
        color: #f8fafc;
        font-weight: 400;
    }
    .stat-value {
        color: #ffffff;
        font-weight: 700;
    }
    .prob-box {
        background-color: #161b22;
        border-radius: 12px;
        padding: 16px;
        margin-top: 25px;
        border: 1px solid #21262d;
    }
    .prob-title {
        color: #8b949e;
        font-size: 13px;
        text-align: center;
        margin-bottom: 15px;
        font-weight: 500;
    }
    .prob-row {
        display: flex;
        justify-content: space-around;
        align-items: center;
        text-align: center;
    }
    .prob-num {
        font-size: 18px;
        font-weight: 800;
        color: #ffffff;
    }
    .prob-team {
        font-size: 12px;
        color: #8b949e;
        margin-top: 2px;
    }
    </style>
""", unsafe_allow_html=True)

# Función para consultar la cartelera real desde API pública (ESPN Soccer endpoints)
@st.cache_data(ttl=600)
def cargar_cartelera_api():
    ligas_api = {
        "🇺🇸 MLS, Estados Unidos": "usa.1",
        "🇲🇽 Liga MX, Apertura": "mex.1",
        "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League, Inglaterra": "eng.1",
        "🇪🇸 LaLiga, España": "esp.1",
        "🇮🇹 Serie A, Italia": "ita.1",
        "🇩🇪 Bundesliga, Alemania": "ger.1",
        "🇫🇷 Ligue 1, Francia": "fra.1",
        "🏴󠁧󠁢󠁥󠁮󠁧󠁿 FA Cup, Inglaterra": "eng.fa"
    }
    
    cartelera = {}
    
    for nombre_liga, code in ligas_api.items():
        url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard"
        try:
            res = requests.get(url, timeout=5).json()
            events = res.get("events", [])
            
            partidos_liga = {}
            for ev in events:
                # Filtrar estado del partido (solo pendientes o en juego, excluir finalizados)
                status = ev.get("status", {}).get("type", {}).get("state", "")
                if status == "post":
                    continue # Omite partidos ya jugados
                    
                competitors = ev["competitions"][0]["competitors"]
                home = next(c for c in competitors if c["homeAway"] == "home")
                away = next(c for c in competitors if c["homeAway"] == "away")
                
                team_home = home["team"]["shortDisplayName"]
                team_away = away["team"]["shortDisplayName"]
                match_name = f"{team_home} vs {team_away}"
                
                # Proyección estadística estimada si no hay cuotas directas
                partidos_liga[match_name] = {
                    "local": team_home,
                    "visitante": team_away,
                    "xg_l": 1.45,
                    "xg_v": 1.25,
                    "c_l": 2.20, "c_x": 3.30, "c_v": 3.10,
                    "corn_l": 5, "corn_v": 4,
                    "tarjetas": 4
                }
            
            if partidos_liga:
                cartelera[nombre_liga] = partidos_liga
        except Exception:
            continue
            
    # Si la API no retorna partidos por ser horario sin juegos, mantenemos una base por defecto
    if not cartelera:
        cartelera = {
            "🇺🇸 MLS, Estados Unidos": {
                "LA Galaxy vs Inter Miami": {"local": "LA Galaxy", "visitante": "Inter Miami", "xg_l": 1.75, "xg_v": 1.90, "c_l": 2.45, "c_x": 3.60, "c_v": 2.55, "corn_l": 6, "corn_v": 7, "tarjetas": 4},
                "LAFC vs NYCFC": {"local": "LAFC", "visitante": "NYCFC", "xg_l": 1.80, "xg_v": 1.25, "c_l": 1.70, "c_x": 3.80, "c_v": 4.50, "corn_l": 7, "corn_v": 4, "tarjetas": 3},
                "Seattle Sounders vs Portland Timbers": {"local": "Seattle", "visitante": "Portland", "xg_l": 1.50, "xg_v": 1.20, "c_l": 2.00, "c_x": 3.40, "c_v": 3.50, "corn_l": 5, "corn_v": 5, "tarjetas": 5},
                "Atlanta United vs FC Cincinnati": {"local": "Atlanta", "visitante": "Cincinnati", "xg_l": 1.60, "xg_v": 1.40, "c_l": 2.10, "c_x": 3.50, "c_v": 3.20, "corn_l": 6, "corn_v": 4, "tarjetas": 4}
            }
        }
        
    return cartelera

cartelera_global = cargar_cartelera_api()

if "vista" not in st.session_state:
    st.session_state["vista"] = "cartelera"
    st.session_state["partido_sel"] = None
    st.session_state["liga_sel"] = None

# VISTA 1: CARTELERA AUTOMÁTICA
if st.session_state["vista"] == "cartelera":
    st.markdown('<div style="font-size: 22px; font-weight: 800; color: #ffffff; margin-bottom: 15px;">⚽ SimuladorNy</div>', unsafe_allow_html=True)
    st.markdown('<div style="color: #8b949e; font-size: 12px; margin-bottom: 15px;">Toca un partido para abrir su análisis completo:</div>', unsafe_allow_html=True)

    for liga, partidos in cartelera_global.items():
        st.markdown(f'<div class="league-header">{liga}</div>', unsafe_allow_html=True)
        for nombre_partido, datos in partidos.items():
            if st.button(f"⚡  {datos['local']}  vs  {datos['visitante']}", key=f"btn_{liga}_{nombre_partido}", use_container_width=True):
                st.session_state["partido_sel"] = nombre_partido
                st.session_state["liga_sel"] = liga
                st.session_state["vista"] = "detalle"
                st.rerun()

# VISTA 2: DETALLE DEL PARTIDO
elif st.session_state["vista"] == "detalle":
    if st.button("⬅️ Volver a la cartelera"):
        st.session_state["vista"] = "cartelera"
        st.rerun()

    p = cartelera_global[st.session_state["liga_sel"]][st.session_state["partido_sel"]]

    # Simulación de Monte Carlo
    simulaciones = 10000
    goles_l = np.random.poisson(p["xg_l"], simulaciones)
    goles_v = np.random.poisson(p["xg_v"], simulaciones)

    prob_l = (np.sum(goles_l > goles_v) / simulaciones) * 100
    prob_x = (np.sum(goles_l == goles_v) / simulaciones) * 100
    prob_v = (np.sum(goles_l < goles_v) / simulaciones) * 100
    prob_btts = (np.sum((goles_l > 0) & (goles_v > 0)) / simulaciones) * 100

    tot_corners = p["corn_l"] + p["corn_v"]
    ganador_proyectado = p['local'] if prob_l > prob_v else p['visitante']
    btts_texto = "Sí" if prob_btts > 50 else "No"

    st.markdown(f'<div class="match-header-title">{p["local"]} vs {p["visitante"]}</div>', unsafe_allow_html=True)

    # Filas de estadísticas limpias
    st.markdown(f"""
    <div class="stat-row-clean">
        <span class="stat-label">Total de tarjetas amarillas</span>
        <span class="stat-value">{p['tarjetas']}</span>
    </div>
    <div class="stat-row-clean">
        <span class="stat-label">Total de tiros de esquina</span>
        <span class="stat-value">{tot_corners}</span>
    </div>
    <div class="stat-row-clean">
        <span class="stat-label">Ambos equipos marcarán</span>
        <span class="stat-value">{btts_texto}</span>
    </div>
    <div class="stat-row-clean" style="border-bottom: none;">
        <span class="stat-label">Ganador tiempo completo</span>
        <span class="stat-value">{ganador_proyectado}</span>
    </div>
    """, unsafe_allow_html=True)

    # Bloque de probabilidades
    st.markdown(f"""
    <div class="prob-box">
        <div class="prob-title">Probabilidad de victoria al finalizar el encuentro</div>
        <div class="prob-row">
            <div>
                <div class="prob-num">{prob_l:.0f}%</div>
                <div class="prob-team">{p['local']}</div>
            </div>
            <div style="color: #30363d; font-size: 18px;">|</div>
            <div>
                <div class="prob-num">{prob_x:.0f}%</div>
                <div class="prob-team">Empate</div>
            </div>
            <div style="color: #30363d; font-size: 18px;">|</div>
            <div>
                <div class="prob-num">{prob_v:.0f}%</div>
                <div class="prob-team">{p['visitante']}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
