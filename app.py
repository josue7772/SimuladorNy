import numpy as np
import streamlit as st

st.set_page_config(page_title="Simulador de Partidos y Value Bets", page_icon="⚽", layout="centered")

st.title("⚽ Simulador Analítico & Value Bets")
st.write("Calcula probabilidades de goles, córners, tarjetas y detecta valor contra Caliente.mx.")

st.sidebar.header("⚙️ Configuración del Partido")

equipo_local = st.sidebar.text_input("Equipo Local", "América")
equipo_visitante = st.sidebar.text_input("Equipo Visitante", "Chivas")

st.sidebar.subheader("Estadísticas Base")
goles_base_local = st.sidebar.number_input(f"Goles esperados ({equipo_local})", value=1.6, step=0.1)
goles_base_visitante = st.sidebar.number_input(f"Goles esperados ({equipo_visitante})", value=1.1, step=0.1)
corners_base_local = st.sidebar.number_input(f"Córners ({equipo_local})", value=5.5, step=0.5)
corners_base_visitante = st.sidebar.number_input(f"Córners ({equipo_visitante})", value=4.0, step=0.5)

st.sidebar.subheader("Factores Contextuales")
factor_localia = st.sidebar.slider("Ventaja por Localía (%)", 0, 30, 15) / 100.0
baja_estrella = st.sidebar.checkbox(f"¿{equipo_local} no tiene a su delantero estrella?")
rigor_arbitro = st.sidebar.slider("Rigor del Árbitro (Tarjetas)", 2.0, 7.0, 4.5)

st.sidebar.subheader("🎲 Cuotas de Caliente.mx")
cuota_caliente_local = st.sidebar.number_input(f"Cuota Gana {equipo_local}", value=1.85, step=0.05)
cuota_caliente_empate = st.sidebar.number_input("Cuota Empate", value=3.50, step=0.05)
cuota_caliente_visita = st.sidebar.number_input(f"Cuota Gana {equipo_visitante}", value=4.20, step=0.05)

if st.button("🚀 Ejecutar Simulación de Partidos", type="primary"):
    lambda_goles_loc = goles_base_local * (1 + factor_localia)
    lambda_goles_vis = goles_base_visitante
    if baja_estrella:
        lambda_goles_loc *= 0.80

    num_simulaciones = 10000
    sim_goles_loc = np.random.poisson(lambda_goles_loc, num_simulaciones)
    sim_goles_vis = np.random.poisson(lambda_goles_vis, num_simulaciones)
    sim_corners = np.random.poisson(corners_base_local + corners_base_visitante, num_simulaciones)
    sim_tarjetas = np.random.poisson(rigor_arbitro, num_simulaciones)

    p_local = np.mean(sim_goles_loc > sim_goles_vis) * 100
    p_empate = np.mean(sim_goles_loc == sim_goles_vis) * 100
    p_visita = np.mean(sim_goles_loc < sim_goles_vis) * 100

    prob_caliente_local = (1 / cuota_caliente_local) * 100
    prob_caliente_empate = (1 / cuota_caliente_empate) * 100
    prob_caliente_visita = (1 / cuota_caliente_visita) * 100

    st.success("¡Simulación completada con éxito!")
    st.subheader(f"📊 Resultados para: {equipo_local} vs {equipo_visitante}")
    
    col1, col2, col3 = st.columns(3)
    col1.metric(f"Gana {equipo_local}", f"{p_local:.1f}%", f"Cuota justa: @{(100/p_local):.2f}")
    col2.metric("Empate", f"{p_empate:.1f}%", f"Cuota justa: @{(100/p_empate):.2f}")
    col3.metric(f"Gana {equipo_visitante}", f"{p_visita:.1f}%", f"Cuota justa: @{(100/p_visita):.2f}")

    st.markdown("---")
    st.subheader("🔥 Detector de Valor (vs Caliente.mx)")

    def evaluar_valor(nombre, p_modelo, p_casa, cuota):
        if p_modelo > p_casa:
            st.markdown(f"✅ **{nombre} (@{cuota}):** ¡Hay VALOR! Tu modelo dice **{p_modelo:.1f}%** y la casa implica **{p_casa:.1f}%**.")
        else:
            st.markdown(f"❌ **{nombre} (@{cuota}):** Sin valor matemático (La casa paga menos de lo esperado).")

    evaluar_valor(f"Victoria {equipo_local}", p_local, prob_caliente_local, cuota_caliente_local)
    evaluar_valor("Empate", p_empate, prob_caliente_empate, cuota_caliente_empate)
    evaluar_valor(f"Victoria {equipo_visitante}", p_visita, prob_caliente_visita, cuota_caliente_visita)

    st.markdown("---")
    st.info(f"🚩 **Promedio Córners Totales:** {np.mean(sim_corners):.1f}  |  🟨 **Promedio Tarjetas:** {np.mean(sim_tarjetas):.1f}")
