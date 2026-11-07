import streamlit as st
import numpy as np

st.set_page_config(page_title="SimuladorNy - Apuestas Deportivas", page_icon="⚽", layout="centered")

st.title("⚽ SimuladorNy: Modelo Poisson & Monte Carlo")
st.markdown("Herramienta de análisis cuantitativo para detección de valor (Value Bets) frente a cuotas de mercado.")

st.sidebar.header("⚙️ Parámetros del Partido")

equipo_local = st.sidebar.text_input("Equipo Local", "América")
equipo_visitante = st.sidebar.text_input("Equipo Visitante", "Guadalajara")

st.sidebar.subheader("📊 Goles Esperados (xG Base)")
xg_local = st.sidebar.slider(f"xG {equipo_local}", 0.5, 4.0, 1.65, 0.05)
xg_visitante = st.sidebar.slider(f"xG {equipo_visitante}", 0.2, 3.0, 1.15, 0.05)

st.sidebar.subheader("💰 Cuotas de Caliente.mx")
cuota_local = st.sidebar.number_input(f"Cuota Local ({equipo_local})", min_value=1.01, value=1.95, step=0.01)
cuota_empate = st.sidebar.number_input("Cuota Empate (X)", min_value=1.01, value=3.40, step=0.01)
cuota_visitante = st.sidebar.number_input(f"Cuota Visitante ({equipo_visitante})", min_value=1.01, value=4.00, step=0.01)

simulaciones = st.sidebar.slider("Número de Simulaciones Monte Carlo", 1000, 50000, 10000, 1000)

if st.button("🚀 Ejecutar Simulación del Partido", type="primary"):
    # Simulación de Poisson
    goles_l = np.random.poisson(xg_local, simulaciones)
    goles_v = np.random.poisson(xg_visitante, simulaciones)
    
    wins_local = np.sum(goles_l > goles_v)
    draws = np.sum(goles_l == goles_v)
    wins_visitante = np.sum(goles_l < goles_v)
    
    prob_local = (wins_local / simulaciones) * 100
    prob_empate = (draws / simulaciones) * 100
    prob_visitante = (wins_visitante / simulaciones) * 100
    
    # Cálculo de valor (Value = Prob_Modelo * Cuota > 1.0)
    val_local = (prob_local / 100) * cuota_local
    val_empate = (prob_empate / 100) * cuota_empate
    val_visitante = (prob_visitante / 100) * cuota_visitante
    
    st.subheader(f"📈 Resultados de la Simulación ({simulaciones:,} escenarios)")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label=f"Victoria {equipo_local}", value=f"{prob_local:.1f}%", delta=f"Cuota: {cuota_local}")
        if val_local > 1.05:
            st.success(f"🔥 ¡Hay valor! (EV: {val_local:.2f})")
        else:
            st.info(f"Sin valor (EV: {val_local:.2f})")
            
    with col2:
        st.metric(label="Empate", value=f"{prob_empate:.1f}%", delta=f"Cuota: {cuota_empate}")
        if val_empate > 1.05:
            st.success(f"🔥 ¡Hay valor! (EV: {val_empate:.2f})")
        else:
            st.info(f"Sin valor (EV: {val_empate:.2f})")
            
    with col3:
        st.metric(label=f"Victoria {equipo_visitante}", value=f"{prob_visitante:.1f}%", delta=f"Cuota: {cuota_visitante}")
        if val_visitante > 1.05:
            st.success(f"🔥 ¡Hay valor! (EV: {val_visitante:.2f})")
        else:
            st.info(f"Sin valor (EV: {val_visitante:.2f})")

    st.markdown("---")
    st.write("### 📌 Análisis Detallado del Modelo")
    promedio_goles_l = np.mean(goles_l)
    promedio_goles_v = np.mean(goles_v)
    st.write(- Goles promedio simulados para **{equipo_local}**: **{promedio_goles_l:.2f}**)
    st.write(- Goles promedio simulados para **{equipo_visitante}**: **{promedio_goles_v:.2f}**)
else:
    st.info("👈 Configura los parámetros en el menú lateral izquierdo y presiona **'Ejecutar Simulación del Partido'** para calcular las probabilidades y detectar valor.")
