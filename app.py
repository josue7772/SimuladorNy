import streamlit as st
import numpy as np
import requests

st.set_page_config(page_title="SimuladorNy", page_icon="⚽", layout="centered")

# Estilos CSS totalmente renovados: Cero azul, predominan los grises carbón, metálicos y blancos puros
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
    
    /* Encabezado minimalista gris */
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
        margin-top: 20px;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        border-left: 2px solid #6b7280;
        padding-left: 8px;
    }

    /* Tarjetas de estadísticas estilo gris elegante */
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

# Cargar cartelera con la API o respaldo robusto
@st.cache_data(ttl=600)
def cargar_cartelera_api():
    ligas_api = {
        "🇺🇸 MLS, Estados Unidos": "usa.1",
        "🇲🇽 Liga MX, Apertura": "mex.1",
        "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League, Inglaterra": "eng.1",
        "🇪🇸 LaLiga, España": "esp.1"
    }
    cartelera = {}
    for nombre_liga, code in ligas_api.items():
        url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard"
        try:
            res = requests.get(url, timeout=4).json()
            events = res.get("events", [])
            partidos_liga = {}
            for ev in events:
                if ev.get("status", {}).get("type", {}).get("state", "") == "post":
                    continue
                competitors = ev["competitions"][0]["competitors"]
                home = next(c for c in competitors if c["homeAway"] == "home")
                away = next(c for c in competitors if c["homeAway"] == "away")
                team_home = home["team"]["shortDisplayName"]
                team_away = away["team"]["shortDisplayName"]
                partidos_liga[f"{team_home} vs {team_away}"] = {
                    "local": team_home, "visitante": team_away,
                    "xg_l": 1.45, "xg_v": 1.30, "c_l": 2.20, "c_x": 3.30, "c_v": 3.10,
                    "corn_l": 5.2, "corn_v": 4.8, "tarjetas": 4
                }
            if partidos_liga:
                cartelera[nombre_liga] = partidos_liga
        except Exception:
            continue
            
    if not cartelera:
        cartelera = {
            "🇺🇸 MLS, Estados Unidos": {
                "LA Galaxy vs Inter Miami": {"local": "LA Galaxy", "visitante": "Inter Miami", "xg_l": 1.75, "xg_v": 1.90, "c_l": 2.45, "c_x": 3.60, "c_v": 2.55, "corn_l": 6.3, "corn_v": 6.7, "tarjetas": 4},
                "LAFC vs NYCFC": {"local": "LAFC", "visitante": "NYCFC", "xg_l": 1.80, "xg_v": 1.25, "c_l": 1.70, "c_x": 3.80, "c_v": 4.50, "corn_l": 6.5, "corn_v": 4.5, "tarjetas": 3},
                "Seattle Sounders vs Portland Timbers": {"local": "Seattle", "visitante": "Portland", "xg_l": 1.50, "xg_v": 1.20, "c_l": 2.00, "c_x": 3.40, "c_v": 3.50, "corn_l": 5, "corn_v": 5, "tarjetas": 5}
            },
            "🇲🇽 Liga MX, Apertura": {
                "Atlas vs Pachuca": {"local": "Atlas", "visitante": "Pachuca", "xg_l": 1.15, "xg_v": 1.40, "c_l": 2.90, "c_x": 3.30, "c_v": 2.40, "corn_l": 5.1, "corn_v": 5.5, "tarjetas": 5},
                "Tigres vs Cruz Azul": {"local": "Tigres", "visitante": "Cruz Azul", "xg_l": 1.45, "xg_v": 1.35, "c_l": 2.30, "c_x": 3.20, "c_v": 3.00, "corn_l": 5.5, "corn_v": 5.2, "tarjetas": 6}
            }
        }
    return cartelera

cartelera_global = cargar_cartelera_api()

if "vista" not in st.session_state:
    st.session_state["vista"] = "cartelera"
    st.session_state["partido_sel"] = None
    st.session_state["liga_sel"] = None

# VISTA 1: CARTELERA PRINCIPAL
if st.session_state["vista"] == "cartelera":
    st.markdown("""
        <div class="app-card-header">
            <h1 style="color: #ffffff; font-size: 24px; font-weight: 800; margin: 0 0 6px 0;">⚽ SimuladorNy</h1>
            <p style="color: #9ca3af; font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; margin: 0;">Match Intelligence & Analytics</p>
        </div>
    """, unsafe_allow_html=True)

    busqueda = st.text_input("🔍 Buscar partido o liga...", placeholder="Escribe un equipo...")

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

# VISTA 2: DETALLE INTERACTIVO CON SLIDERS (GRIS Y NEGRO)
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

    # Controles deslizantes interactivos
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

    # Tarjeta de probabilidades final
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
