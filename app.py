import streamlit as st
import numpy as np

st.set_page_config(page_title="SimuladorNy", page_icon="⚽", layout="centered")

# Estilos CSS limpios y modernos tipo app nativa
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

# Cartelera global optimizada y limpia
cartelera_global = {
    "🇲🇽 Liga MX, Apertura": {
        "Atlas vs Pachuca": {
            "local": "Atlas", "visitante": "Pachuca",
            "xg_l": 1.15, "xg_v": 1.40, "c_l": 2.90, "c_x": 3.30, "c_v": 2.40, "corn_l": 5, "corn_v": 4, "tarjetas": 5
        },
        "Toluca vs Monterrey": {
            "local": "Toluca", "visitante": "Monterrey",
            "xg_l": 1.55, "xg_v": 1.50, "c_l": 2.40, "c_x": 3.30, "c_v": 2.80, "corn_l": 6, "corn_v": 6, "tarjetas": 4
        },
        "Tigres vs Cruz Azul": {
            "local": "Tigres", "visitante": "Cruz Azul",
            "xg_l": 1.45, "xg_v": 1.35, "c_l": 2.30, "c_x": 3.20, "c_v": 3.00, "corn_l": 5, "corn_v": 5, "tarjetas": 6
        },
        "Pumas vs America": {
            "local": "Pumas", "visitante": "America",
            "xg_l": 1.20, "xg_v": 1.65, "c_l": 3.10, "c_x": 3.40, "c_v": 2.20, "corn_l": 4, "corn_v": 6, "tarjetas": 5
        }
    },
    "🇺🇸 MLS, Estados Unidos": {
        "LA Galaxy vs Inter Miami": {
            "local": "LA Galaxy", "visitante": "Inter Miami",
            "xg_l": 1.75, "xg_v": 1.90, "c_l": 2.45, "c_x": 3.60, "c_v": 2.55, "corn_l": 6, "corn_v": 7, "tarjetas": 4
        },
        "LAFC vs New York City": {
            "local": "LAFC", "visitante": "NYCFC",
            "xg_l": 1.80, "xg_v": 1.25, "c_l": 1.70, "c_x": 3.80, "c_v": 4.50, "corn_l": 7, "corn_v": 4, "tarjetas": 3
        }
    },
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 FA Cup, Inglaterra": {
        "Manchester United vs Liverpool": {
            "local": "Man United", "visitante": "Liverpool",
            "xg_l": 1.50, "xg_v": 1.85, "c_l": 3.20, "c_x": 3.50, "c_v": 2.15, "corn_l": 5, "corn_v": 7, "tarjetas": 5
        }
    },
    "🇪🇸 LaLiga, España": {
        "Espanyol vs Real Valladolid": {
            "local": "Espanyol", "visitante": "Valladolid",
            "xg_l": 1.40, "xg_v": 1.10, "c_l": 2.20, "c_x": 3.10, "c_v": 3.40, "corn_l": 5, "corn_v": 4, "tarjetas": 5
        },
        "Valencia vs Real Madrid": {
            "local": "Valencia", "visitante": "Real Madrid",
            "xg_l": 0.90, "xg_v": 2.10, "c_l": 5.50, "c_x": 4.10, "c_v": 1.55, "corn_l": 4, "corn_v": 6, "tarjetas": 4
        },
        "Barcelona vs Atletico Madrid": {
            "local": "Barcelona", "visitante": "Atletico Madrid",
            "xg_l": 1.85, "xg_v": 1.20, "c_l": 1.80, "c_x": 3.60, "c_v": 4.20, "corn_l": 6, "corn_v": 5, "tarjetas": 6
        }
    }
}

if "vista" not in st.session_state:
    st.session_state["vista"] = "cartelera"
    st.session_state["partido_sel"] = None
    st.session_state["liga_sel"] = None

# VISTA 1: CARTELERA PRINCIPAL
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

    # Bloque de probabilidades limpio
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
