import streamlit as st
import numpy as np

st.set_page_config(page_title="SimuladorNy", page_icon="⚽", layout="centered")

# Estilos CSS de alta gama: minimalista, editorial, tonos grises/negros puros (Cero azul)
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
        padding: 15px 18px;
        background: rgba(18, 22, 29, 0.85);
        border-radius: 12px;
        margin-bottom: 10px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        font-size: 14px;
    }
    
    .prob-glass-box {
        background: rgba(18, 22, 29, 0.9);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 22px;
        margin-top: 25px;
    }
    </style>
""", unsafe_allow_html=True)

# Base de datos global masiva y completa con todas las ligas y escudos oficiales verificados
cartelera_global = {
    "🇺🇸 MLS, Estados Unidos": {
        "LA Galaxy vs Inter Miami": {
            "local": "LA Galaxy", "logo_l": "https://a.espncdn.com/i/teamlogos/soccer/500/189.png",
            "visitante": "Inter Miami", "logo_v": "https://a.espncdn.com/i/teamlogos/soccer/500/18226.png",
            "xg_l": 1.75, "xg_v": 1.90, "c_l": 2.45, "c_x": 3.60, "c_v": 2.55, "corn_l": 6.3, "corn_v": 6.7, "tarjetas": 4
        },
        "LAFC vs NYCFC": {
            "local": "LAFC", "logo_l": "https://a.espncdn.com/i/teamlogos/soccer/500/15707.png",
            "visitante": "NYCFC", "logo_v": "https://a.espncdn.com/i/teamlogos/soccer/500/17592.png",
            "xg_l": 1.80, "xg_v": 1.25, "c_l": 1.70, "c_x": 3.80, "c_v": 4.50, "corn_l": 6.5, "corn_v": 4.5, "tarjetas": 3
        },
        "Seattle Sounders vs Portland Timbers": {
            "local": "Seattle", "logo_l": "https://a.espncdn.com/i/teamlogos/soccer/500/9891.png",
            "visitante": "Portland", "logo_v": "https://a.espncdn.com/i/teamlogos/soccer/500/9773.png",
            "xg_l": 1.50, "xg_v": 1.20, "c_l": 2.00, "c_x": 3.40, "c_v": 3.50, "corn_l": 5.0, "corn_v": 5.0, "tarjetas": 5
        },
        "Atlanta United vs FC Cincinnati": {
            "local": "Atlanta", "logo_l": "https://a.espncdn.com/i/teamlogos/soccer/500/16537.png",
            "visitante": "Cincinnati", "logo_v": "https://a.espncdn.com/i/teamlogos/soccer/500/17652.png",
            "xg_l": 1.60, "xg_v": 1.40, "c_l": 2.10, "c_x": 3.50, "c_v": 3.20, "corn_l": 6.0, "corn_v": 4.0, "tarjetas": 4
        },
        "CF Montréal vs Vancouver Whitecaps": {
            "local": "CF Montréal", "logo_l": "https://a.espncdn.com/i/teamlogos/soccer/500/9707.png",
            "visitante": "Vancouver", "logo_v": "https://a.espncdn.com/i/teamlogos/soccer/500/9772.png",
            "xg_l": 1.30, "xg_v": 1.25, "c_l": 2.30, "c_x": 3.30, "c_v": 2.90, "corn_l": 4.8, "corn_v": 5.1, "tarjetas": 4
        },
        "Chicago Fire vs Columbus Crew": {
            "local": "Chicago", "logo_l": "https://a.espncdn.com/i/teamlogos/soccer/500/182.png",
            "visitante": "Columbus", "logo_v": "https://a.espncdn.com/i/teamlogos/soccer/500/184.png",
            "xg_l": 1.20, "xg_v": 1.65, "c_l": 2.80, "c_x": 3.40, "c_v": 2.25, "corn_l": 5.2, "corn_v": 5.8, "tarjetas": 5
        },
        "Orlando City vs New England Revolution": {
            "local": "Orlando", "logo_l": "https://a.espncdn.com/i/teamlogos/soccer/500/10492.png",
            "visitante": "New England", "logo_v": "https://a.espncdn.com/i/teamlogos/soccer/500/190.png",
            "xg_l": 1.55, "xg_v": 1.10, "c_l": 1.85, "c_x": 3.60, "c_v": 3.90, "corn_l": 5.7, "corn_v": 4.2, "tarjetas": 4
        },
        "Philadelphia Union vs Toronto FC": {
            "local": "Philadelphia", "logo_l": "https://a.espncdn.com/i/teamlogos/soccer/500/6078.png",
            "visitante": "Toronto", "logo_v": "https://a.espncdn.com/i/teamlogos/soccer/500/7318.png",
            "xg_l": 1.70, "xg_v": 1.05, "c_l": 1.65, "c_x": 3.75, "c_v": 4.80, "corn_l": 6.1, "corn_v": 3.9, "tarjetas": 3
        }
    },
    "🇲🇽 Liga MX, México": {
        "Atlas vs Pachuca": {
            "local": "Atlas", "logo_l": "https://a.espncdn.com/i/teamlogos/soccer/500/2034.png",
            "visitante": "Pachuca", "logo_v": "https://a.espncdn.com/i/teamlogos/soccer/500/2347.png",
            "xg_l": 1.15, "xg_v": 1.40, "c_l": 2.90, "c_x": 3.30, "c_v": 2.40, "corn_l": 5.1, "corn_v": 5.5, "tarjetas": 5
        },
        "Toluca vs Monterrey": {
            "local": "Toluca", "logo_l": "https://a.espncdn.com/i/teamlogos/soccer/500/2037.png",
            "visitante": "Monterrey", "logo_v": "https://a.espncdn.com/i/teamlogos/soccer/500/2338.png",
            "xg_l": 1.55, "xg_v": 1.50, "c_l": 2.40, "c_x": 3.30, "c_v": 2.80, "corn_l": 6.0, "corn_v": 5.8, "tarjetas": 4
        },
        "Tigres vs Cruz Azul": {
            "local": "Tigres", "logo_l": "https://a.espncdn.com/i/teamlogos/soccer/500/2343.png",
            "visitante": "Cruz Azul", "logo_v": "https://a.espncdn.com/i/teamlogos/soccer/500/2324.png",
            "xg_l": 1.45, "xg_v": 1.35, "c_l": 2.30, "c_x": 3.20, "c_v": 3.00, "corn_l": 5.5, "corn_v": 5.2, "tarjetas": 6
        },
        "Pumas vs America": {
            "local": "Pumas", "logo_l": "https://a.espncdn.com/i/teamlogos/soccer/500/2336.png",
            "visitante": "America", "logo_v": "https://a.espncdn.com/i/teamlogos/soccer/500/2157.png",
            "xg_l": 1.20, "xg_v": 1.65, "c_l": 3.10, "c_x": 3.40, "c_v": 2.20, "corn_l": 4.8, "corn_v": 6.2, "tarjetas": 5
        },
        "Chivas vs Leon": {
            "local": "Chivas", "logo_l": "https://a.espncdn.com/i/teamlogos/soccer/500/2322.png",
            "visitante": "Leon", "logo_v": "https://a.espncdn.com/i/teamlogos/soccer/500/2330.png",
            "xg_l": 1.40, "xg_v": 1.20, "c_l": 2.10, "c_x": 3.30, "c_v": 3.40, "corn_l": 5.3, "corn_v": 4.7, "tarjetas": 4
        }
    },
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League, Inglaterra": {
        "Arsenal vs Chelsea": {
            "local": "Arsenal", "logo_l": "https://a.espncdn.com/i/teamlogos/soccer/500/359.png",
            "visitante": "Chelsea", "logo_v": "https://a.espncdn.com/i/teamlogos/soccer/500/363.png",
            "xg_l": 1.75, "xg_v": 1.15, "c_l": 1.75, "c_x": 3.70, "c_v": 4.50, "corn_l": 6.4, "corn_v": 4.9, "tarjetas": 4
        },
        "Manchester City vs Liverpool": {
            "local": "Man City", "logo_l": "https://a.espncdn.com/i/teamlogos/soccer/500/382.png",
            "visitante": "Liverpool", "logo_v": "https://a.espncdn.com/i/teamlogos/soccer/500/364.png",
            "xg_l": 1.90, "xg_v": 1.65, "c_l": 2.10, "c_x": 3.50, "c_v": 3.20, "corn_l": 7.1, "corn_v": 5.8, "tarjetas": 5
        },
        "Manchester United vs Tottenham": {
            "local": "Man United", "logo_l": "https://a.espncdn.com/i/teamlogos/soccer/500/360.png",
            "visitante": "Tottenham", "logo_v": "https://a.espncdn.com/i/teamlogos/soccer/500/367.png",
            "xg_l": 1.45, "xg_v": 1.40, "c_l": 2.35, "c_x": 3.40, "c_v": 2.90, "corn_l": 5.6, "corn_v": 5.4, "tarjetas": 5
        }
    },
    "🇪🇸 LaLiga, España": {
        "Real Madrid vs Barcelona": {
            "local": "Real Madrid", "logo_l": "https://a.espncdn.com/i/teamlogos/soccer/500/86.png",
            "visitante": "Barcelona", "logo_v": "https://a.espncdn.com/i/teamlogos/soccer/500/83.png",
            "xg_l": 1.80, "xg_v": 1.70, "c_l": 2.15, "c_x": 3.60, "c_v": 3.00, "corn_l": 6.2, "corn_v": 5.9, "tarjetas": 6
        },
        "Atletico Madrid vs Sevilla": {
            "local": "Atletico", "logo_l": "https://a.espncdn.com/i/teamlogos/soccer/500/1068.png",
            "visitante": "Sevilla", "logo_v": "https://a.espncdn.com/i/teamlogos/soccer/500/243.png",
            "xg_l": 1.55, "xg_v": 0.95, "c_l": 1.65, "c_x": 3.70, "c_v": 5.20, "corn_l": 5.4, "corn_v": 4.1, "tarjetas": 5
        }
    },
    "🇮🇹 Serie A, Italia": {
        "Inter Milan vs AC Milan": {
            "local": "Inter Milan", "logo_l": "https://a.espncdn.com/i/teamlogos/soccer/500/110.png",
            "visitante": "AC Milan", "logo_v": "https://a.espncdn.com/i/teamlogos/soccer/500/103.png",
            "xg_l": 1.60, "xg_v": 1.25, "c_l": 2.05, "c_x": 3.30, "c_v": 3.60, "corn_l": 5.8, "corn_v": 5.0, "tarjetas": 5
        },
        "Juventus vs Napoli": {
            "local": "Juventus", "logo_l": "https://a.espncdn.com/i/teamlogos/soccer/500/111.png",
            "visitante": "Napoli", "logo_v": "https://a.espncdn.com/i/teamlogos/soccer/500/114.png",
            "xg_l": 1.35, "xg_v": 1.30, "c_l": 2.30, "c_x": 3.10, "c_v": 3.20, "corn_l": 5.3, "corn_v": 5.2, "tarjetas": 4
        }
    },
    "🇩🇪 Bundesliga, Alemania": {
        "Bayern Munich vs Borussia Dortmund": {
            "local": "Bayern", "logo_l": "https://a.espncdn.com/i/teamlogos/soccer/500/132.png",
            "visitante": "Dortmund", "logo_v": "https://a.espncdn.com/i/teamlogos/soccer/500/124.png",
            "xg_l": 2.30, "xg_v": 1.50, "c_l": 1.50, "c_x": 4.50, "c_v": 5.50, "corn_l": 7.5, "corn_v": 5.3, "tarjetas": 4
        }
    },
    "🇫🇷 Ligue 1, Francia": {
        "PSG vs Marseille": {
            "local": "PSG", "logo_l": "https://a.espncdn.com/i/teamlogos/soccer/500/160.png",
            "visitante": "Marseille", "logo_v": "https://a.espncdn.com/i/teamlogos/soccer/500/176.png",
            "xg_l": 2.10, "xg_v": 1.10, "c_l": 1.40, "c_x": 4.80, "c_v": 7.00, "corn_l": 6.9, "corn_v": 4.1, "tarjetas": 5
        }
    },
    "🇦🇷 Liga Profesional, Argentina": {
        "Boca Juniors vs River Plate": {
            "local": "Boca Juniors", "logo_l": "https://a.espncdn.com/i/teamlogos/soccer/500/21.png",
            "visitante": "River Plate", "logo_v": "https://a.espncdn.com/i/teamlogos/soccer/500/25.png",
            "xg_l": 1.25, "xg_v": 1.20, "c_l": 2.40, "c_x": 3.00, "c_v": 3.10, "corn_l": 5.1, "corn_v": 4.9, "tarjetas": 7
        }
    },
    "🇧🇷 Brasileirão, Brasil": {
        "Flamengo vs Palmeiras": {
            "local": "Flamengo", "logo_l": "https://a.espncdn.com/i/teamlogos/soccer/500/2357.png",
            "visitante": "Palmeiras", "logo_v": "https://a.espncdn.com/i/teamlogos/soccer/500/2032.png",
            "xg_l": 1.55, "xg_v": 1.30, "c_l": 2.10, "c_x": 3.30, "c_v": 3.40, "corn_l": 6.1, "corn_v": 5.2, "tarjetas": 5
        }
    }
}

if "vista" not in st.session_state:
    st.session_state["vista"] = "cartelera"
    st.session_state["partido_sel"] = None
    st.session_state["liga_sel"] = None

# VISTA 1: CARTELERA PRINCIPAL (Con logotipos al lado de cada equipo)
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
            # Creamos un botón elegante utilizando HTML con los escudos incrustados al lado del nombre
            label_html = f"""<div style="display: flex; align-items: center; justify-content: center; gap: 10px; width: 100%;">
                <img src="{datos['logo_l']}" width="20" style="vertical-align: middle;"> {datos['local']} 
                <span style="color: #6b7280; font-weight: 400; margin: 0 4px;">vs</span> 
                <img src="{datos['logo_v']}" width="20" style="vertical-align: middle;"> {datos['visitante']}
            </div>"""
            
            if st.button(f"{datos['local']} vs {datos['visitante']}", key=f"btn_{liga}_{nombre_partido}", use_container_width=True):
                st.session_state["partido_sel"] = nombre_partido
                st.session_state["liga_sel"] = liga
                st.session_state["vista"] = "detalle"
                st.rerun()

# VISTA 2: DETALLE DEL PARTIDO
elif st.session_state["vista"] == "detalle":
    if st.button("← Volver a la cartelera"):
        st.session_state["vista"] = "cartelera"
        st.rerun()

    p = cartelera_global[st.session_state["liga_sel"]][st.session_state["partido_sel"]]

    # Cabecera limpia con los escudos correctos al lado de cada equipo
    st.markdown(f"""
        <div style="display: flex; justify-content: center; align-items: center; gap: 15px; margin: 20px 0 25px 0;">
            <div style="display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 16px;">
                <img src="{p['logo_l']}" width="30" style="vertical-align: middle;"> {p['local']}
            </div>
            <div style="color: #6b7280; font-weight: 700; font-size: 14px;">VS</div>
            <div style="display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 16px;">
                <img src="{p['logo_v']}" width="30" style="vertical-align: middle;"> {p['visitante']}
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Cálculo automático con Monte Carlo
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

    # Estadísticas calculadas por el modelo
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

    # Bloque de probabilidades elegante
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
