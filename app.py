import streamlit as st
import requests
import math
import random
from collections import Counter
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


def sample_poisson(rng, lam):
    """Muestra de Poisson mediante el algoritmo de Knuth."""
    lam = max(0.01, float(lam))
    limit = math.exp(-lam)
    product = 1.0
    count = 0
    while product > limit:
        count += 1
        product *= rng.random()
    return count - 1

def sample_binomial(rng, n, probability):
    """Muestra binomial sencilla para conteos como tiros a puerta."""
    probability = min(1.0, max(0.0, probability))
    return sum(1 for _ in range(max(0, int(n))) if rng.random() < probability)

def run_monte_carlo(params, iterations=10000):
    """Simulación Monte Carlo con parámetros editables, no datos históricos automáticos."""
    rng = random.Random()
    scores = Counter()
    home_wins = draws = away_wins = both_score = over_25 = 0
    totals = Counter()

    for _ in range(iterations):
        hg = sample_poisson(rng, params["xg_home"])
        ag = sample_poisson(rng, params["xg_away"])
        hs = sample_poisson(rng, params["shots_home"])
        aws = sample_poisson(rng, params["shots_away"])
        hc = sample_poisson(rng, params["corners_home"])
        ac = sample_poisson(rng, params["corners_away"])
        hy = sample_poisson(rng, params["yellow_home"])
        ay = sample_poisson(rng, params["yellow_away"])
        hst = sample_binomial(rng, hs, 0.36)
        ast = sample_binomial(rng, aws, 0.36)

        scores[(hg, ag)] += 1
        if hg > ag:
            home_wins += 1
        elif hg == ag:
            draws += 1
        else:
            away_wins += 1
        both_score += int(hg > 0 and ag > 0)
        over_25 += int(hg + ag >= 3)

        totals["shots_home"] += hs
        totals["shots_away"] += aws
        totals["sot_home"] += hst
        totals["sot_away"] += ast
        totals["corners_home"] += hc
        totals["corners_away"] += ac
        totals["yellow_home"] += hy
        totals["yellow_away"] += ay

    best_score, best_count = scores.most_common(1)[0]
    averages = {key: value / iterations for key, value in totals.items()}
    return {
        "iterations": iterations,
        "home_win": home_wins / iterations * 100,
        "draw": draws / iterations * 100,
        "away_win": away_wins / iterations * 100,
        "both_score": both_score / iterations * 100,
        "over_25": over_25 / iterations * 100,
        "score": best_score,
        "score_frequency": best_count / iterations * 100,
        "top_scores": scores.most_common(5),
        "averages": averages,
    }

@st.cache_data(ttl=1800, show_spinner=False)
def historical_events(sport_path, league_code, selected_date):
    """Resultados recientes; la cobertura del feed gratuito puede ser incompleta."""
    start = selected_date - timedelta(days=35)
    url = league_url(sport_path, league_code) + f"?dates={start:%Y%m%d}-{selected_date:%Y%m%d}&limit=500"
    try:
        return fetch_json(url).get("events", [])
    except (requests.RequestException, ValueError):
        return []

def historical_parameters(match, events):
    """Estima intensidades a partir de goles recientes, sin controles del visitante."""
    home_id = str(match["home"].get("team", {}).get("id", ""))
    away_id = str(match["away"].get("team", {}).get("id", ""))
    records = {home_id: [], away_id: []}
    for event in events:
        parsed = parse_event(event)
        if not parsed or not parsed["completed"] or parsed["id"] == match["id"]:
            continue
        for side, other in (("home", "away"), ("away", "home")):
            team = parsed[side]
            team_id = str(team.get("team", {}).get("id", ""))
            if team_id not in records:
                continue
            try:
                gf = float(team["score"])
                ga = float(parsed[other]["score"])
            except (KeyError, TypeError, ValueError):
                continue
            records[team_id].append((gf, ga))
    home_games = records[home_id][-10:]
    away_games = records[away_id][-10:]
    # Priors de liga para reducir ruido; nunca se presentan como xG oficiales.
    def blended(games, idx, prior):
        return (sum(x[idx] for x in games) + 5 * prior) / (len(games) + 5)
    home_attack = blended(home_games, 0, 1.4)
    home_defense = blended(home_games, 1, 1.3)
    away_attack = blended(away_games, 0, 1.3)
    away_defense = blended(away_games, 1, 1.4)
    xgh = min(4.5, max(.15, (home_attack*.55 + away_defense*.45)*1.06))
    xga = min(4.5, max(.15, (away_attack*.55 + home_defense*.45)*.94))
    # Estas métricas auxiliares son aproximaciones, no históricos oficiales.
    return {
        "xg_home": xgh, "xg_away": xga,
        "shots_home": 8 + 3.0*xgh, "shots_away": 8 + 3.0*xga,
        "corners_home": 3 + 1.2*xgh, "corners_away": 3 + 1.2*xga,
        "yellow_home": 1.9, "yellow_away": 2.0,
    }, len(home_games), len(away_games)

def render_monte_carlo_panel(match, events):
    home_name = team_name(match["home"])
    away_name = team_name(match["away"])
    params, hn, an = historical_parameters(match, events)
    result = run_monte_carlo(params, 10000)
    st.markdown("### ✦ SIMULADORNY · ANALYSIS AI")
    st.caption("10,000 simulaciones Monte Carlo · xG calculado automáticamente")
    c1, c2, c3 = st.columns([2,3,2], vertical_alignment="center")
    with c1:
        if safe_logo(match["home"]):
            st.image(safe_logo(match["home"]), width=60)
        st.markdown(f"**{home_name}**")
    with c2:
        st.markdown(f"<div class='predicted-score'>{result['score'][0]} - {result['score'][1]}</div>", unsafe_allow_html=True)
        st.caption(f"Marcador más frecuente · {result['score_frequency']:.2f}%")
    with c3:
        if safe_logo(match["away"]):
            st.image(safe_logo(match["away"]), width=60)
        st.markdown(f"**{away_name}**")
    st.markdown("**Probabilidades de resultado**")
    for label, value in [
        (f"Victoria {home_name}", result["home_win"]),
        ("Empate", result["draw"]),
        (f"Victoria {away_name}", result["away_win"]),
    ]:
        st.markdown(f"<div class='prob-label'><span>{label}</span><b>{value:.1f}%</b></div>", unsafe_allow_html=True)
        st.progress(value / 100)
    st.markdown("**5 marcadores más probables**")
    for i, ((h, a), count) in enumerate(result["top_scores"], 1):
        st.markdown(f"**{i}. {h} - {a}** · {count / 100:.2f}% ({count:,} de 10,000)")
        st.progress(count / 10000)
    st.markdown("**Estadísticas proyectadas**")
    av = result["averages"]
    table_data = [
        {"Métrica": "xG estimado", home_name: f"{params['xg_home']:.2f}", away_name: f"{params['xg_away']:.2f}"},
        {"Métrica": "Tiros totales*", home_name: f"{av['shots_home']:.1f}", away_name: f"{av['shots_away']:.1f}"},
        {"Métrica": "Tiros a puerta*", home_name: f"{av['sot_home']:.1f}", away_name: f"{av['sot_away']:.1f}"},
        {"Métrica": "Córners*", home_name: f"{av['corners_home']:.1f}", away_name: f"{av['corners_away']:.1f}"},
        {"Métrica": "Tarjetas amarillas*", home_name: f"{av['yellow_home']:.1f}", away_name: f"{av['yellow_away']:.1f}"},
    ]
    st.dataframe(table_data, hide_index=True, use_container_width=True)
    c1, c2 = st.columns(2)
    c1.metric("Ambos anotan", f"{result['both_score']:.1f}%")
    c2.metric("Más de 2.5 goles", f"{result['over_25']:.1f}%")
    st.caption(f"Historial encontrado en la liga: {home_name} {hn} partidos; {away_name} {an} partidos.")
    if hn < 3 or an < 3:
        st.warning("Muestra histórica insuficiente: se emplean promedios de referencia y la confianza es baja.")
    st.caption("El xG es una estimación basada en goles recientes, NO xG oficial de tiros. *Tiros, córners y tarjetas se aproximan mediante parámetros base, no mediante históricos detallados. Las simulaciones no garantizan resultados.")


def render_match_card(match, sport_label, league_name, historical_data):
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
    with st.expander("Ver análisis y estadísticas", expanded=False):
        if sport_label == "⚽ Fútbol":
            render_monte_carlo_panel(match, historical_data)
            st.markdown("---")
        st.write("**Estadísticas reales publicadas por el proveedor (si existen)**")
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

        st.caption("Las proyecciones son probabilísticas y se distinguen de los datos reales del proveedor.")
    st.markdown("</div>", unsafe_allow_html=True)

# --------------------------- ESTILO ---------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
.stApp { background: #090b0d; color: #f3f4f6; }
section[data-testid="stSidebar"] { background: #10131a; border-right: 1px solid #252a36; }
h1, h2, h3, p, label { color: #f3f4f6; }
div[data-testid="stMetric"] { background: #141923; border: 1px solid #252a36; padding: 14px; border-radius: 14px; }
.match-card { background: linear-gradient(135deg,#171c20,#101417); border: 1px solid #252a36; border-radius: 20px; padding: 18px; margin: 0 0 16px 0; }
.score { text-align: center; font-size: 27px; font-weight: 800; padding-top: 8px; }
.predicted-score { text-align:center; font-size:38px; font-weight:800; letter-spacing:2px; padding:8px 0; color:#f4f6f7; }
.prob-label { display:flex; justify-content:space-between; margin:8px 0 2px; color:#e5e7eb; font-size:14px; }
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
st.caption("SPORTS PREDICTION LAB · 10,000 SIMULACIONES MONTE CARLO")

# --------------------------- CONTROLES ---------------------------
with st.sidebar:
    st.markdown("## ⚡ Explorar deportes")
    sport_label = st.radio("Deporte", list(SPORTS.keys()), horizontal=True)
    sport = SPORTS[sport_label]
    league_name = st.selectbox("Liga / competición", list(sport["leagues"].keys()))
    selected_date = st.date_input("Fecha de partidos", value=date.today())
    search = st.text_input("Buscar equipo", placeholder="🔎 Buscar equipos...")
    status_filter = st.radio("Estado", ["Todos", "En vivo", "Próximos", "Finalizados"], horizontal=True)
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

    if status_filter == "En vivo":
        matches = [m for m in matches if m["state"] == "in"]
    elif status_filter == "Próximos":
        matches = [m for m in matches if m["state"] == "pre"]
    elif status_filter == "Finalizados":
        matches = [m for m in matches if m["completed"]]
    live = sum(1 for m in matches if m["state"] == "in")
    finished = sum(1 for m in matches if m["completed"])
    upcoming = len(matches) - live - finished

    a, b, c = st.columns(3)
    a.metric("Partidos", len(matches))
    b.metric("En vivo", live)
    c.metric("Finalizados", finished)

    st.markdown(f"### 🏟️ Partidos · {sport_label} · {league_name}")
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
