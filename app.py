import streamlit as st
import numpy as np
import requests

st.set_page_config(page_title="SimuladorNy", page_icon="⚽", layout="centered")

# Estilos CSS de diseño ultra moderno y gamificado estilo app de élite
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
        background-color: #0b0f19;
        color: #f8fafc;
        font-family: 'Inter', sans-serif;
    }
    .app-header {
        background: linear-gradient(135deg, #111827 0%, #1f2937 100%);
        padding: 20px;
        border-radius: 16px;
        margin-bottom: 20px;
        border: 1px solid #374151;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
        text-align: center;
    }
    .league-title {
        font-size: 13px;
        font-weight: 700;
        color: #38bdf8;
        margin-top: 15px;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .stat-row-clean {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 16px;
        background: #111827;
        border-radius: 10px;
        margin-bottom: 8px;
        border: 1px solid #1f2937;
        font-size: 14px;
    }
    .prob-box {
        background: linear-gradient(135deg, #111827 0%, #0f172a 100%);
        border-radius: 14px;
        padding: 18px;
        margin-top: 20px;
        border: 1px solid #374151;
        box-shadow: 0 8px 20px rgba(0,0,0,0.3);
    }
    </style>
""", unsafe_allow_html=True)

# Cartelera robusta con respaldo y API en vivo
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
                "LAFC vs NYCFC": {"local": "LAFC", "visitante": "NYCFC", "xg_l": 1.80, "xg_v": 1.25, "c_l": 1.70, "c_x": 3.80, "c_v": 4.50, "corn_l": 6.5, "corn_v": 4.5, "tarjetas": 3}
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

# VISTA 1: CARTELERA MODAL E INTERACTIVA
if st.session_state["vista"] == "cartelera":
    st.markdown("""
        <div class="app-header">
            <h1 style="color: #ffffff; font-size: 24px; margin-bottom: 4px;">⚽ SimuladorNy</h1>
            <p style="color: #94a3b8; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin: 0;">Quantitative Match Intelligence</p>
        </div>
    """, unsafe_allow_html=True)

    # Buscador interactivo para filtrar partidos al instante
    busqueda = st.text_input("🔍 Buscar equipo o liga...", placeholder="Ej. Galaxy, Atlas, Premier...")

    for liga, partidos in cartelera_global.items():
        # Filtrar partidos si el usuario escribe en el buscador
        partidos_filtrados = {k: v for k, v in partidos.items() if busqueda.lower() in k.lower() or busqueda.lower() in liga.lower()}
        if not partidos_filtrados and busqueda:
            continue
        if not partidos_filtrados:
            partidos_filtrados = partidos

        st.markdown(f'<div class="league-header">{liga}</div>', unsafe_allow_html=True)
        for nombre_partido, datos in partidos_filtrados.items():
            if st.button(f"⚡  {datos['local']}  vs  {datos['visitante']}", key=f"btn_{liga}_{nombre_partido}", use_container_width=True):
                st.session_state["partido_sel"] = nombre_partido
                st.session_state["liga_sel"] = liga
                st.session_state["vista"] = "detalle"
                st.rerun()

# VISTA 2: DETALLE INTERACTIVO CON SIMULADOR DE xG EN TIEMPO REAL
elif st.session_state["vista"] == "detalle":
    if st.button("⬅️ Volver a la cartelera principal"):
        st.session_state["vista"] = "cartelera"
        st.rerun()

    p = cartelera_global[st.session_state["liga_sel"]][st.session_state["partido_sel"]]

    st.markdown(f"""
        <div style="text-align: center; margin-top: 10px; margin-bottom: 15px;">
            <h2 style="color: #ffffff; font-size: 22px; font-weight: 800;">{p['local']} vs {p['visitante']}</h2>
            <p style="color: #38bdf8; font-size: 11px; text-transform: uppercase; letter-spacing: 1px;">Panel de Simulación Interactiva</p>
        </div>
    """, unsafe_allow_html=True)

    # Sliders interactivos para que el usuario mueva el xG y personalice el análisis
    st.markdown("<p style='color: #94a3b8; font-size: 12px; font-weight: 600; margin-bottom: 4px;'>🎛️ Ajusta el xG (Goles Esperados) en tiempo real:</p>", unsafe_allow_html=True)
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        xg_l_input = st.slider(f"xG {p['local']}", 0.2, 4.0, float(p['xg_l']), 0.05)
    with col_s2:
        xg_v_input = st.slider(f"xG {p['visitante']}", 0.2, 4.0, float(p['xg_v']), 0.05)

    # Simulación de Monte Carlo dinámica con los valores del usuario
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

    # Métricas limpias y modernas
    st.markdown(f"""
    <div class="stat-row-clean">
        <span style="color: #94a3b8;">Total de tarjetas amarillas proyectadas</span>
        <span style="color: #ffffff; font-weight: 700;">{p['tarjetas']}</span>
    </div>
    <div class="stat-row-clean">
        <span style="color: #94a3b8;">Total de tiros de esquina (Córners)</span>
        <span style="color: #38bdf8; font-weight: 700;">{tot_corners}</span>
    </div>
    <div class="stat-row-clean">
        <span style="color: #94a3b8;">Ambos equipos marcarán (BTTS)</span>
        <span style="color: #ffffff; font-weight: 700;">{btts_texto} ({prob_btts:.0f}%)</span>
    </div>
    <div class="stat-row-clean">
        <span style="color: #94a3b8;">Ganador probable (Tiempo completo)</span>
        <span style="color: #38bdf8; font-weight: 700;">{ganador_proyectado}</span>
    </div>
    """, unsafe_allow_html=True)

    # Bloque de probabilidades dinámicas
    st.markdown(f"""
    <div class="prob-box">
        <div style="color: #94a3b8; font-size: 12px; text-align: center; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.8px;">Probabilidad de Victoria en Vivo</div>
        <div style="display: flex; justify-content: space-around; align-items: center; text-align: center;">
            <div>
                <div style="font-size: 20px; font-weight: 800; color: #ffffff;">{prob_l:.0f}%</div>
                <div style="font-size: 11px; color: #94a3b8; margin-top: 2px;">{p['local']}</div>
            </div>
            <div style="color: #374151; font-size: 18px;">|</div>
            <div>
                <div style="font-size: 20px; font-weight: 800; color: #ffffff;">{prob_x:.0f}%</div>
                <div style="font-size: 11px; color: #94a3b8; margin-top: 2px;">Empate</div>
            </div>
            <div style="color: #374151; font-size: 18px;">|</div>
            <div>
                <div style="font-size: 20px; font-weight: 800; color: #ffffff;">{prob_v:.0f}%</div>
                <div style="font-size: 11px; color: #94a3b8; margin-top: 2px;">{p['visitante']}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
