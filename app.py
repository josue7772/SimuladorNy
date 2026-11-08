import streamlit as st
import requests
import math
from datetime import date, timedelta
from urllib.parse import quote

# ============================================================
# SIMULADORNY — Dashboard deportivo con fuentes gratuitas
# Ejecutar: pip install streamlit requests
#           streamlit run app.py
# ============================================================

st.set_page_config(
    page_title="SimuladorNy — Analysis AI",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ESPN publica marcadores JSON sin clave. Es una API no oficial:
# cobertura, disponibilidad y campos pueden cambiar sin aviso.
ESPN = "https://site.api.espn.com/apis/site/v2/sports"

# Slugs ESPN. La cobertura depende de cada competencia.
SOCCER_LEAGUES = {
    "México · Liga MX": "mex.1",
    "Estados Unidos · MLS": "usa.1",
    "Inglaterra · Premier League": "eng.1",
    "Inglaterra · Championship": "eng.2",
    "España · LaLiga": "esp.1",
    "España · LaLiga 2": "esp.2",
    "Italia · Serie A": "ita.1",
    "Italia · Serie B": "ita.2",
    "Alemania · Bundesliga": "ger.1",
    "Alemania · 2. Bundesliga": "ger.2",
    "Francia · Ligue 1": "fra.1",
    "Francia · Ligue 2": "fra.2",
    "Países Bajos · Eredivisie": "ned.1",
    "Portugal · Primeira Liga": "por.1",
    "Brasil · Série A": "bra.1",
    "Argentina · Liga Profesional": "arg.1",
    "Escocia · Premiership": "sco.1",
    "Turquía · Süper Lig": "tur.1",
    "Bélgica · Pro League": "bel.1",
    "Grecia · Super League": "gre.1",
    "Arabia Saudita · Pro League": "ksa.1",
    "Japón · J1 League": "jpn.1",
    "Corea del Sur · K League 1": "kor.1",
    "Australia · A-League": "aus.1",
    "UEFA · Champions League": " UEFA.CHAMPIONS",
    "UEFA · Europa League": " UEFA.EUROPA",
    "UEFA · Conference League": " UEFA.EUROPA.CONF",
    "CONMEBOL · Copa Libertadores": " CONMEBOL.LIBERTADORES",
    "CONMEBOL · Copa Sudamericana": " CONMEBOL.SUDAMERICANA",
}

# ESPN no garantiza una cobertura uniforme de todas estas ligas.
# KBO se consulta como baseball/kbo; si el proveedor no la expone,
# la interfaz muestra el error de disponibilidad y no inventa partidos.
SPORTS = {
    "⚽ Fútbol": {"path": "soccer", "leagues": SOCCER_LEAGUES},
    "🏀 NBA": {"path": "basketball", "leagues": {"NBA · Estados Unidos": "nba"}},
    "⚾ KBO": {"path": "baseball", "leagues": {"KBO League · Corea del Sur": "kbo"}},
    "🏒 NHL": {"path": "hockey", "leagues": {"NHL · Estados Unidos/Canadá": "nhl"}},
}

# Quita espacios accidentales en algunos slugs y permite slugs con punto.
def league_url(sport_path, league_code, endpoint="scoreboard"):
    code = league_code.strip()
    return f"{ESPN}/{sport_path}/{quote(code, safe='.')}/{endpoint}"

@st.cache_data(ttl=120, show_spinner=False)
def fetch_json(url):
    headers = {"User-Agent": "SimuladorNy/1.0 (Streamlit sports dashboard)"}
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    return response.json()

def get_events(sport_path, league_code, selected_date):
    # ESPN acepta fechas YYYYMMDD en scoreboard.
    url = league_url(sport_path, league_code) + f"?dates={selected_date:%Y%m%d}&limit=100"
    payload = fetch_json(url)
    return payload.get("events", [])

def safe_logo(competitor):
    return competitor.get("logo") or competitor.get("team", {}).get("logo") or ""

def parse_event(event):
    comp = (event.get("competitions") or [{}])[0]
    competitors = comp.get("competitors") or []
    home = next((x for x in competitors if x.get("homeAway") == "home"), None)
    away = next((x for x in competitors if x.get("homeAway") == "away"), None)
    if not home and competitors:
        home = competitors[0]
    if not away and len(competitors) > 1:
        away = competitors[1]
    if not home or not away:
        return None

    status = event.get("status", {}).get("type", {})
    return {
        "id": event.get("id"),
        "name": event.get("name", "Partido"),
        "date": event.get("date"),
        "status": status.get("shortDetail") or status.get("detail") or "Programado",
        "completed": bool(status.get("completed")),
        "state": status.get("state", "pre"),
        "home": home,
        "away": away,
        "venue": (comp.get("venue") or {}).get("fullName", "Sede no disponible"),
        "broadcast": ", ".join((x.get("names") or [""])[0] for x in comp.get("broadcasts", []) if x.get("names")),
    }

def score_of(team):
    value = team.get("score")
    return str(value) if value not in (None, "") else "—"

def team_name(team):
    t = team.get("team", {})
    return t.get("displayName") or team.get("displayName") or "Equipo"

def stat_value(stats, *needles):
    """Busca una estadística por etiqueta en un arreglo ESPN."""
    for item in stats or []:
        label = str(item.get("name", "")).lower().replace("_", " ")
        display = str(item.get("displayValue") or item.get("value") or "")
        if any(n.lower() in label for n in needles):
            return display or "—"
    return "No disponible"

@st.cache_data(ttl=180, show_spinner=False)
def fetch_summary(event_id):
    url = f"{ESPN}/soccer/summary?event={event_id}"
    return fetch_json(url)

def extract_team_stats(summary):
    # En fútbol ESPN suele devolver boxscore. En otros deportes la
    # estructura puede variar, por eso se comprueba antes de mostrar.
    box = summary.get("boxscore") or {}
    teams = box.get("teams") or []
    output = []
    for team in teams:
        output.append({
            "name": team.get("team", {}).get("displayName", "Equipo"),
            "stats": team.get("statistics") or [],
        })
    return output

def poisson(lam, k):
    return math.exp(-lam) * (lam ** k) / math.factorial(k)

def score_prediction(home_goals, away_goals):
    # No se calcula con promedios ficticios. Se requiere información
    # suficiente del proveedor para estimar goles.
    if home_goals is None or away_goals is None:
        return None
    best = (0, 0, -1)
    for h in range(6):
        for a in range(6):
            p = poisson(home_goals, h) * poisson(away_goals, a)
            if p > best[2]:
                best = (h, a, p)
    return best

def render_match_card(match, sport_label, league_name):
    home, away = match["home"], match["away"]
    hname, aname = team_name(home), team_name(away)
    hlogo, alogo = safe_logo(home), safe_logo(away)
    st.markdown('<div class="match-card">', unsafe_allow_html=True)
    top1, top2 = st.columns([3, 1])
    with top1:
        st.caption(f"{league_name}  ·  {match['status']}")
    with top2:
        if match["state"] == "in":
            st.markdown("🔴 **EN VIVO**")
        elif match["completed"]:
            st.caption("FINALIZADO")
        else:
            st.caption("PROGRAMADO")

    c1, cm, c2 = st.columns([4, 2, 4], vertical_alignment="center")
    with c1:
        if hlogo:
            st.image(hlogo, width=54)
        st.markdown(f"**{hname}**")
        st.caption("LOCAL")
    with cm:
        st.markdown(
            f"<div class='score'>{score_of(home)} : {score_of(away)}</div>",
            unsafe_allow_html=True,
        )
        st.caption("MARCADOR")
    with c2:
        if alogo:
            st.image(alogo, width=54)
        st.markdown(f"**{aname}**")
        st.caption("VISITANTE")

    st.caption(f"🏟️ {match['venue']}")
    with st.expander("Ver análisis y estadísticas"):
        st.write("**Datos disponibles del proveedor**")
        if sport_label == "⚽ Fútbol":
            try:
                summary = fetch_summary(match["id"])
                stats_by_team = extract_team_stats(summary)
                if stats_by_team:
                    cols = st.columns(len(stats_by_team))
                    for i, team_data in enumerate(stats_by_team[:2]):
                        with cols[i]:
                            st.markdown(f"**{team_data['name']}**")
                            stats = team_data["stats"]
                            rows = [
                                ("Posesión", stat_value(stats, "possession")),
                                ("Tiros", stat_value(stats, "total shots", "shots")),
                                ("Tiros a puerta", stat_value(stats, "shots on target")),
                                ("Córners", stat_value(stats, "won corners", "corners")),
                                ("Faltas", stat_value(stats, "fouls")),
                                ("Amarillas", stat_value(stats, "yellow cards")),
                                ("Rojas", stat_value(stats, "red cards")),
                                ("Goles esperados (xG)", stat_value(stats, "expected goals", "xg")),
                            ]
                            for label, value in rows:
                                st.write(f"{label}: **{value}**")
                else:
                    st.info("El proveedor no publicó estadísticas detalladas para este partido.")
            except Exception:
                st.info("Las estadísticas detalladas no están disponibles para este partido.")
        else:
            st.info(
                "El marcador está disponible si ESPN cubre este encuentro. "
                "Las estadísticas avanzadas de NBA, KBO y NHL requieren un feed "
                "específico; esta versión no inventa xG, córners, tarjetas ni métricas."
            )

        st.caption(
            "Marcador exacto: no se muestra una predicción hasta disponer de "
            "promedios recientes verificables de ambos equipos. Los valores no "
            "publicados por la fuente se indican como no disponibles."
        )
    st.markdown("</div>", unsafe_allow_html=True)

# --------------------------- ESTILO ---------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
.stApp { background: #0b0d10; color: #f3f4f6; }
section[data-testid="stSidebar"] { background: #10131a; border-right: 1px solid #252a36; }
h1, h2, h3, p, label { color: #f3f4f6; }
div[data-testid="stMetric"] { background: #141923; border: 1px solid #252a36; padding: 14px; border-radius: 14px; }
.match-card { background: #12151c; border: 1px solid #252a36; border-radius: 16px; padding: 16px; margin: 0 0 16px 0; }
.score { text-align: center; font-size: 27px; font-weight: 800; padding-top: 8px; }
div[data-testid="stExpander"] { border: 1px solid #252a36; border-radius: 12px; }
.stButton button { border-radius: 10px; }
.small-muted { color: #9ca3af; font-size: 12px; }
</style>
""", unsafe_allow_html=True)

# --------------------------- CABECERA ---------------------------
st.markdown("""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:4px">
  <div style="font-size:30px">⚽</div>
  <div>
    <div style="font-size:23px;font-weight:800;letter-spacing:1px">SIMULADOR<span style="color:#9ca3af">NY</span></div>
    <div style="font-size:10px;color:#9ca3af;letter-spacing:3px;font-weight:700">SPORTS ANALYSIS</div>
  </div>
</div>
""", unsafe_allow_html=True)
st.caption("Centro de partidos · estadísticas disponibles · múltiples deportes")

# --------------------------- CONTROLES ---------------------------
with st.sidebar:
    st.markdown("## ⚙️ Configuración")
    sport_label = st.radio("Deporte", list(SPORTS.keys()), horizontal=False)
    sport = SPORTS[sport_label]
    league_name = st.selectbox("Liga / competición", list(sport["leagues"].keys()))
    selected_date = st.date_input("Fecha de partidos", value=date.today())
    search = st.text_input("Buscar equipo", placeholder="Ej. América, Lakers, Doosan...")
    st.divider()
    st.caption("Fuentes gratuitas / sin clave")
    st.markdown("- ESPN scoreboard (no oficial)\n- Escudos entregados por el proveedor")
    st.caption("Los límites y la cobertura dependen de cada liga.")

league_code = sport["leagues"][league_name]
try:
    with st.spinner("Consultando calendario deportivo..."):
        events = get_events(sport["path"], league_code, selected_date)
    matches = [m for m in (parse_event(e) for e in events) if m]
    if search.strip():
        q = search.strip().lower()
        matches = [
            m for m in matches
            if q in team_name(m["home"]).lower() or q in team_name(m["away"]).lower()
        ]

    live = sum(1 for m in matches if m["state"] == "in")
    finished = sum(1 for m in matches if m["completed"])
    upcoming = len(matches) - live - finished

    a, b, c = st.columns(3)
    a.metric("Partidos", len(matches))
    b.metric("En vivo", live)
    c.metric("Finalizados", finished)

    st.markdown(f"### {sport_label} · {league_name}")
    st.caption(f"{selected_date.strftime('%d/%m/%Y')} · {len(matches)} partido(s) encontrados")

    if not matches:
        st.info(
            "No se encontraron partidos para esta fecha. Puede que la competición "
            "no tenga encuentros programados o que el proveedor gratuito no la cubra."
        )
    else:
        for match in matches:
            render_match_card(match, sport_label, league_name)

except requests.HTTPError as exc:
    st.error(f"El proveedor respondió con un error HTTP: {exc}")
    st.info(
        "Comprueba otra fecha o competición. Algunas ligas no están disponibles "
        "en la fuente gratuita."
    )
except requests.RequestException as exc:
    st.error(f"No se pudo conectar con el proveedor deportivo: {exc}")
    st.info("Revisa tu conexión e inténtalo de nuevo.")
except Exception as exc:
    st.error(f"No se pudieron interpretar los datos: {exc}")

st.divider()
st.caption(
    "SimuladorNy es un proyecto independiente. ESPN y las ligas mencionadas "
    "pertenecen a sus respectivos titulares. Los datos pueden retrasarse, "
    "cambiar o no estar disponibles. No se generan estadísticas inexistentes."
)
