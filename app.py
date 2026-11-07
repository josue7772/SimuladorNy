import streamlit as st
import numpy as np

# Configuración móvil de Streamlit
st.set_page_config(page_title="SimuladorNy", page_icon="⚽", layout="centered")

# Estilos CSS estilo editorial de lujo (Paleta monocromática carbón/gris, cero azul)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
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
    
    /* Encabezado Principal */
    .editorial-header {
        text-align: center;
        padding: 25px 15px 15px 15px;
    }
    .brand-title {
        font-size: 24px;
        font-weight: 800;
        letter-spacing: 2.5px;
        color: #ffffff;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .brand-subtitle {
        font-size: 10px;
        font-weight: 600;
        letter-spacing: 3px;
        color: #6b7280;
        text-transform: uppercase;
    }

    /* Títulos de liga */
    .league-section-title {
        font-size: 11px;
        font-weight: 700;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin: 22px 0 10px 4px;
        border-left: 2px solid #4b5563;
        padding-left: 8px;
    }

    /* Filas estadísticas */
    .stat-row-clean {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 15px 18px;
        background: rgba(18, 22, 29, 0.85);
        border-radius: 12px;
        margin-bottom: 10px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        font-size: 14px;
    }
    
    /* Contenedores de Cristal */
    .prob-glass-box {
        background: rgba(18, 22, 29, 0.9);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 22px;
        margin-top: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# Registro individual de escudos en alta definición (SVG / Wikimedia) por equipo
logos_equipos = {
    "LA Galaxy": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c9/LA_Galaxy_logo_%282007%E2%80%932023%29.svg/500px-LA_Galaxy_logo_%282007%E2%80%932023%29.svg.png",
    "Inter Miami": "https://upload.wikimedia.org/wikipedia/en/thumb/5/5e/Inter_Miami_CF_logo.svg/500px-Inter_Miami_CF_logo.svg.png",
    "LAFC": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Los_Angeles_FC_%28logo%29.svg/500px-Los_Angeles_FC_%28logo%29.svg.png",
    "NYCFC": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b8/New_York_City_FC_logo.svg/500px-New_York_City_FC_logo.svg.png",
    "Seattle": "https://upload.wikimedia.org/wikipedia/en/thumb/c/ce/Seattle_Sounders_FC_logo_%282024%29.svg/500px-Seattle_Sounders_FC_logo_%282024%29.svg.png",
    "Portland": "https://upload.wikimedia.org/wikipedia/en/thumb/d/d7/Portland_Timbers_logo.svg/500px-Portland_Timbers_logo.svg.png",
    "Atlanta": "https://upload.wikimedia.org/wikipedia/en/thumb/0/07/Atlanta_United_FC_logo.svg/500px-Atlanta_United_FC_logo.svg.png",
    "Cincinnati": "https://upload.wikimedia.org/wikipedia/en/thumb/d/d5/FC_Cincinnati_logo.svg/500px-FC_Cincinnati_logo.svg.png",
    "Atlas": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/17/Atlas_FC_logo.svg/500px-Atlas_FC_logo.svg.png",
    "Pachuca": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/CF_Pachuca_logo.svg/500px-CF_Pachuca_logo.svg.png",
    "Toluca": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/Deportivo_Toluca_FC_logo.svg/500px-Deportivo_Toluca_FC_logo.svg.png",
    "Monterrey": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/CF_Monterrey_logo.svg/500px-CF_Monterrey_logo.svg.png",
    "Tigres": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/ce/Tigres_UANL_logo.svg/500px-Tigres_UANL_logo.svg.png",
    "Cruz Azul": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Cruz_Azul_fc_logo.svg/500px-Cruz_Azul_fc_logo.svg.png",
    "Pumas": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Pumas_UNAM_logo.svg/500px-Pumas_UNAM_logo.svg.png",
    "America": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Club_Am%C3%A9rica_logo_%282023%29.svg/500px-Club_Am%C3%A9rica_logo_%282023%29.svg.png",
    "Arsenal": "https://upload.wikimedia.org/wikipedia/en/thumb/5/53/Arsenal_FC.svg/500px-Arsenal_FC.svg.png",
    "Chelsea": "https://upload.wikimedia.org/wikipedia/en/thumb/c/cc/Chelsea_FC.svg/500px-Chelsea_FC.svg.png",
    "Man City": "https://upload.wikimedia.org/wikipedia/en/thumb/e/eb/Manchester_City_FC_badge.svg/500px-Manchester_City_FC_badge.svg.png",
    "Liverpool": "https://upload.wikimedia.org/wikipedia/en/thumb/0/0c/Liverpool_FC.svg/500px-Liverpool_FC.svg.png",
    "Real Madrid": "https://upload.wikimedia.org/wikipedia/en/thumb/5/56/Real_Madrid_CF.svg/500px-Real_Madrid_CF.svg.png",
    "Barcelona": "https://upload.wikimedia.org/wikipedia/en/thumb/4/47/FC_Barcelona_%28crest%29.svg/500px-FC_Barcelona_%28crest%29.svg.png",
    "Inter Milan": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/FC_Internazionale_Milano_2021.svg/500px-FC_Internazionale_Milano_2021.svg.png",
    "AC Milan": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d0/Logo_of_AC_Milan.svg/500px-Logo_of_AC_Milan.svg.png",
    "Bayern": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/FC_Bayern_M%C3%BCnchen_logo_%282002%E2%80%932024%29.svg/500px-FC_Bayern_M%C3%BCnchen_logo_%282002%E2%80%932024%29.svg.png",
    "Dortmund": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/67/Borussia_Dortmund_logo.svg/500px-Borussia_Dortmund_logo.svg.png",
    "PSG": "https://upload.wikimedia.org/wikipedia/en/thumb/a/a7/Paris_Saint-Germain_F.C..svg/500px-Paris_Saint-Germain_F.C..svg.png",
    "Marseille": "https://upload.wikimedia.org/wikipedia/en/thumb/d/d8/Olympique_de_Marseille_logo.svg/500px-Olympique_de_Marseille_logo.svg.png",
    "Boca Juniors": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/CA_Boca_Juniors_logo_%282010s%29.svg/500px-CA_Boca_Juniors_logo_%282010s%29.svg.png",
    "River Plate": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/CA_River_Plate_logo_%282022%29.svg/500px-CA_River_Plate_logo_%282022%29.svg.png",
    "Flamengo": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/CR_Flamengo_logo.svg/500px-CR_Flamengo_logo.svg.png",
    "Palmeiras": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/10/SE_Palmeiras_logo.svg/500px-SE_Palmeiras_logo.svg.png"
}

# Cartelera global completa de ligas profesionales
cartelera_global = {
    "🇺🇸 MLS, Estados Unidos": {
        "LA Galaxy vs Inter Miami": {"local": "LA Galaxy", "visitante": "Inter Miami", "xg_l": 1.75, "xg_v": 1.90, "corn_l": 6.3, "corn_v": 6.7, "tarjetas": 4},
        "LAFC vs NYCFC": {"local": "LAFC", "visitante": "NYCFC", "xg_l": 1.80, "xg_v": 1.25, "corn_l": 6.5, "corn_v": 4.5, "tarjetas": 3},
        "Seattle vs Portland": {"local": "Seattle", "visitante": "Portland", "xg_l": 1.50, "xg_v": 1.20, "corn_l": 5.0, "corn_v": 5.0, "tarjetas": 5},
        "Atlanta vs Cincinnati": {"local": "Atlanta", "visitante": "Cincinnati", "xg_l": 1.60, "xg_v": 1.40, "corn_l": 6.0, "corn_v": 4.0, "tarjetas": 4}
    },
    "🇲🇽 Liga MX, México": {
        "Atlas vs Pachuca": {"local": "Atlas", "visitante": "Pachuca", "xg_l": 1.15, "xg_v": 1.40, "corn_l": 5.1, "corn_v": 5.5, "tarjetas": 5},
        "Toluca vs Monterrey": {"local": "Toluca", "visitante": "Monterrey", "xg_l": 1.55, "xg_v": 1.50, "corn_l": 6.0, "corn_v": 5.8, "tarjetas": 4},
        "Tigres vs Cruz Azul": {"local": "Tigres", "visitante": "Cruz Azul", "xg_l": 1.45, "xg_v": 1.35, "corn_l": 5.5, "corn_v": 5.2, "tarjetas": 6},
        "Pumas vs America": {"local": "Pumas", "visitante": "America", "xg_l": 1.20, "xg_v": 1.65, "corn_l": 4.8, "corn_v": 6.2, "tarjetas": 5}
    },
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League, Inglaterra": {
        "Arsenal vs Chelsea": {"local": "Arsenal", "visitante": "Chelsea", "xg_l": 1.75, "xg_v": 1.15, "corn_l": 6.4, "corn_v": 4.9, "tarjetas": 4},
        "Man City vs Liverpool": {"local": "Man City", "visitante": "Liverpool", "xg_l": 1.90, "xg_v": 1.65, "corn_l": 7.1, "corn_v": 5.8, "tarjetas": 5}
    },
    "🇪🇸 LaLiga, España": {
        "Real Madrid vs Barcelona": {"local": "Real Madrid", "visitante": "Barcelona", "xg_l": 1.80, "xg_v": 1.70, "corn_l": 6.2, "corn_v": 5.9, "tarjetas": 6}
    },
    "🇮🇹 Serie A, Italia": {
        "Inter Milan vs AC Milan": {"local": "Inter Milan", "visitante": "AC Milan", "xg_l": 1.60, "xg_v": 1.25, "corn_l": 5.8, "corn_v": 5.0, "tarjetas": 5}
    },
    "🇩🇪 Bundesliga, Alemania": {
        "Bayern vs Dortmund": {"local": "Bayern", "visitante": "Dortmund", "xg_l": 2.30, "xg_v": 1.50, "corn_l": 7.5, "corn_v": 5.3, "tarjetas": 4}
    },
    "🇫🇷 Ligue 1, Francia": {
        "PSG vs Marseille": {"local": "PSG", "visitante": "Marseille", "xg_l": 2.10, "xg_v": 1.10, "corn_l": 6.9, "corn_v": 4.1, "tarjetas": 5}
    },
    "🇦🇷 Liga Profesional, Argentina": {
        "Boca Juniors vs River Plate": {"local": "Boca Juniors", "visitante": "River Plate", "xg_l": 1.25, "xg_v": 1.20, "corn_l": 5.1, "corn_v": 4.9, "tarjetas": 7}
    },
    "🇧🇷 Brasileirão, Brasil": {
        "Flamengo vs Palmeiras": {"local": "Flamengo", "visitante": "Palmeiras", "xg_l": 1.55, "xg_v": 1.30, "corn_l": 6.1, "corn_v": 5.2, "tarjetas": 5}
    }
}

# Manejo de vistas (Cartelera vs Detalle)
if "vista" not in st.session_state:
    st.session_state["vista"] = "cartelera"
    st.session_state["partido_sel"] = None
    st.session_state["liga_sel"] = None

# VISTA 1: CARTELERA PRINCIPAL
if st.session_state["vista"] == "cartelera":
    st.markdown("""
        <div class="editorial-header">
            <div class="brand-title">SimuladorNy</div>
            <div class="brand-subtitle">Análisis Predictivo Cuantitativo</div>
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
            if st.button(f"{datos['local']}   vs   {datos['visitante']}", key=f"btn_{liga}_{nombre_partido}", use_container_width=True):
                st.session_state["partido_sel"] = nombre_partido
                st.session_state["liga_sel"] = liga
                st.session_state["vista"] = "detalle"
                st.rerun()

# VISTA 2: DETALLE AUTOMÁTICO DEL PARTIDO
elif st.session_state["vista"] == "detalle":
    if st.button("← Volver a la cartelera"):
        st.session_state["vista"] = "cartelera"
        st.rerun()

    p = cartelera_global[st.session_state["liga_sel"]][st.session_state["partido_sel"]]
    l_url = logos_equipos.get(p['local'], "")
    v_url = logos_equipos.get(p['visitante'], "")

    # Cabecera con escudos oficiales garantizados
    st.markdown(f"""
        <div style="display: flex; justify-content: center; align-items: center; gap: 18px; margin: 20px 0 25px 0;">
            <div style="display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 16px;">
                <img src="{l_url}" width="32" style="object-fit: contain;"> {p['local']}
            </div>
            <div style="color: #6b7280; font-weight: 700; font-size: 14px;">VS</div>
            <div style="display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 16px;">
                <img src="{v_url}" width="32" style="object-fit: contain;"> {p['visitante']}
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Simulación Monte Carlo (10,000 iteraciones automáticas)
    simulaciones = 10000
    goles_l = np.random.poisson(p['xg_l'], simulaciones)
    goles_v = np.random.poisson(p['xg_v'], simulaciones)

    prob_l = (np.sum(goles_l > goles_v) / simulaciones) * 100
    prob_x = (np.sum(goles_l == goles_v) / simulaciones) * 100
    prob_v = (np.sum(goles_l < goles_v) / simulaciones) * 100
    prob_btts = (np.sum((goles_l > 0) & (goles_v > 0)) / simulaciones) * 100

    tot_corners = round(p["corn_l"] + p["corn_v"], 1)
    ganador_proyectado = p['local'] if prob_l > prob_v else p['visitante']
    btts_texto = "Sí" if prob_btts > 50 else "No"

    # Tarjetas estadísticas calculadas
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

    # Probabilidades de victoria en vivo
    st.markdown(f"""
    <div class="prob-glass-box">
        <div style="color: #6b7280; font-size: 10px; text-align: center; margin-bottom: 14px; text-transform: uppercase; letter-spacing: 2px;">Probabilidad de Victoria en Vivo</div>
        <div style="display: flex; justify-content: space-around; align-items: center; text-align: center;">
            <div>
                <div style="font-size: 19px; font-weight: 700; color: #ffffff;">{prob_l:.0f}%</div>
                <div style="font-size: 10px; color: #9ca3af; margin-top: 3px; text-transform: uppercase;">{p['local']}</div>
            </div>
            <div style="color: #2b3240; font-size: 16px;">|</div>
            <div>
                <div style="font-size: 19px; font-weight: 700; color: #ffffff;">{prob_x:.0f}%</div>
                <div style="font-size: 10px; color: #9ca3af; margin-top: 3px; text-transform: uppercase;">Empate</div>
            </div>
            <div style="color: #2b3240; font-size: 16px;">|</div>
            <div>
                <div style="font-size: 19px; font-weight: 700; color: #ffffff;">{prob_v:.0f}%</div>
                <div style="font-size: 10px; color: #9ca3af; margin-top: 3px; text-transform: uppercase;">{p['visitante']}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
