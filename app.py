import html
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

def run_monte_carlo(params, iterations=10000, seed=None):
    """Simulación Monte Carlo con parámetros calculados internamente."""
    rng = random.Random(seed)
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
        hf = sample_poisson(rng, params["fouls_home"])
        af = sample_poisson(rng, params["fouls_away"])
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
        totals["fouls_home"] += hf
        totals["fouls_away"] += af

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
    """Calendario histórico en bloques semanales para evitar rangos ignorados por ESPN."""
    found = {}
    # Incluye hasta ~100 días: suficiente para localizar cinco juegos de liga,
    # aunque puede ser insuficiente durante parones o al inicio de temporada.
    for weeks_ago in range(15):
        start = selected_date - timedelta(days=7 * (weeks_ago + 1))
        finish = selected_date - timedelta(days=7 * weeks_ago + 1)
        url = league_url(sport_path, league_code) + f"?dates={start:%Y%m%d}-{finish:%Y%m%d}&limit=300"
        try:
            for e in fetch_json(url).get("events", []):
                found[str(e.get("id"))] = e
        except (requests.RequestException, ValueError):
            continue
    return list(found.values())

@st.cache_data(ttl=1800, show_spinner=False)
def team_recent_games(sport_path, league_code, team_id, cutoff):
    """Intenta el calendario de equipo de la temporada actual y anterior."""
    if not team_id:
        return []
    events = {}
    for season in (cutoff.year, cutoff.year - 1):
        url = league_url(sport_path, league_code, f"teams/{team_id}/schedule")
        try:
            payload = fetch_json(url + f"?dates={season}&limit=200")
            for event in payload.get("events", []):
                events[str(event.get("id"))] = event
        except (requests.RequestException, ValueError):
            continue
    return list(events.values())

def numeric_score(competitor):
    value = competitor.get("score")
    if isinstance(value, dict):
        value = value.get("value", value.get("displayValue"))
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

def event_day(raw):
    try:
        return date.fromisoformat(str(raw.get("date", ""))[:10])
    except ValueError:
        return None

def history_for_match(match, league_events, sport_path, league_code, cutoff):
    """Cinco resultados previos por equipo y hasta cinco duelos directos.
    Nunca incorpora resultados del encuentro a pronosticar ni fechas posteriores.
    """
    hid = str(match["home"].get("team", {}).get("id") or "")
    aid = str(match["away"].get("team", {}).get("id") or "")
    raw = {str(e.get("id")): e for e in league_events if e.get("id")}
    for tid in (hid, aid):
        for e in team_recent_games(sport_path, league_code, tid, cutoff):
            if e.get("id"):
                raw[str(e["id"])] = e
    home_games, away_games, h2h = [], [], []
    for e in raw.values():
        day = event_day(e)
        if day is None or day >= cutoff or str(e.get("id")) == str(match["id"]):
            continue
        m = parse_event(e)
        if not m or not m["completed"]:
            continue
        h, a = m["home"], m["away"]
        hs, aws = numeric_score(h), numeric_score(a)
        if hs is None or aws is None:
            continue
        eh = str(h.get("team", {}).get("id") or "")
        ea = str(a.get("team", {}).get("id") or "")
        row = {"date":day, "home":team_name(h), "away":team_name(a),
               "hs":hs, "aws":aws, "home_id":eh, "away_id":ea}
        if hid in (eh, ea):
            home_games.append({**row, "gf":hs if eh == hid else aws,
                               "ga":aws if eh == hid else hs, "at_home":eh == hid})
        if aid in (eh, ea):
            away_games.append({**row, "gf":hs if eh == aid else aws,
                               "ga":aws if eh == aid else hs, "at_home":eh == aid})
        if {hid, aid} == {eh, ea}:
            h2h.append(row)
    key = lambda r:r["date"]
    return (sorted(home_games, key=key, reverse=True)[:5],
            sorted(away_games, key=key, reverse=True)[:5],
            sorted(h2h, key=key, reverse=True)[:5])

def historical_parameters(home_games, away_games, h2h):
    """Ataque/defensa de últimos cinco, localía y H2H con regularización.
    La estimación de goles NO es xG oficial basado en calidad de disparos.
    """
    def weighted(games, field, prior):
        weights = [1.0, .86, .74, .64, .55][:len(games)]
        return (sum(g[field]*w for g,w in zip(games,weights)) + 1.5*prior)/(sum(weights)+1.5)
    ha = weighted(home_games,"gf",1.35)
    hd = weighted(home_games,"ga",1.35)
    aa = weighted(away_games,"gf",1.30)
    ad = weighted(away_games,"ga",1.35)
    # Acentúa la forma propia y el rival, sin asignar una intensidad fija universal.
    xgh = (.58*ha + .42*ad)*1.08
    xga = (.58*aa + .42*hd)*.94
    xgh = max(.15,min(4.5,xgh))
    xga = max(.15,min(4.5,xga))
    return {
        "xg_home":xgh,"xg_away":xga,
        "shots_home": 7.5 + 3.5*xgh,"shots_away":7.5 + 3.5*xga,
        "corners_home":3.0 + 1.35*xgh,"corners_away":3.0 + 1.35*xga,
        "yellow_home":1.8,"yellow_away":2.0,
        "fouls_home":12.0,"fouls_away":12.5,
    }

def team_pair_html(home, away, center="VS", large=False):
    """A single responsive flex row, not Streamlit columns."""
    def item(team):
        name = html.escape(team_name(team))
        logo = safe_logo(team)
        image = (f'<img src="{html.escape(logo, quote=True)}" alt="" loading="lazy" />'
                 if isinstance(logo, str) and logo.startswith("https://") else
                 '<span class="sn-logo-fallback">⚽</span>')
        return f'<div class="sn-side">{image}<span>{name}</span></div>'
    cls = "sn-teams sn-large" if large else "sn-teams"
    return (f'<div class="{cls}">{item(home)}'
            f'<div class="sn-center">{html.escape(str(center))}</div>'
            f'{item(away)}</div>')

def render_monte_carlo_panel(match, events, sport_path, league_code, cutoff):
    """Panel único: resultados Monte Carlo sin secciones de análisis técnico."""
    home_name, away_name = team_name(match["home"]), team_name(match["away"])
    home_games, away_games, h2h = history_for_match(
        match, events, sport_path, league_code, cutoff)
    params = historical_parameters(home_games, away_games, h2h)
    hid = str(match["home"].get("team", {}).get("id") or "")
    if h2h:
        hh = sum(g["hs"] if g["home_id"] == hid else g["aws"] for g in h2h) / len(h2h)
        ah = sum(g["aws"] if g["home_id"] == hid else g["hs"] for g in h2h) / len(h2h)
        params["xg_home"] = max(.15, min(4.5, .88*params["xg_home"] + .12*hh))
        params["xg_away"] = max(.15, min(4.5, .88*params["xg_away"] + .12*ah))
        params["shots_home"] = 7.5 + 3.5*params["xg_home"]
        params["shots_away"] = 7.5 + 3.5*params["xg_away"]
        params["corners_home"] = 3 + 1.35*params["xg_home"]
        params["corners_away"] = 3 + 1.35*params["xg_away"]
    seed = sum((i+1)*ord(ch) for i,ch in enumerate(str(match["id"])))
    result = run_monte_carlo(params, 10000, seed=seed)
    av = result["averages"]
    st.markdown("### SIMULADORNY · ANALYSIS AI")
    st.success("Motor Monte Carlo · 10,000 simulaciones")
    st.markdown(team_pair_html(match["home"], match["away"], "VS", large=True),
                unsafe_allow_html=True)
    st.divider()
    st.markdown("#### Probabilidades")
    for label, value in (
        (f"Victoria {home_name}", result["home_win"]),
        ("Empate", result["draw"]),
        (f"Victoria {away_name}", result["away_win"]),
    ):
        st.markdown(
            f"<div class='prob-label'><b>{html.escape(label)}</b><b>{value:.1f}%</b></div>",
            unsafe_allow_html=True)
        st.progress(value / 100)
    st.divider()
    st.markdown("#### Estadísticas proyectadas")
    stats = [
        ("Goles esperados (proxy xG)", f"{params['xg_home']:.2f} – {params['xg_away']:.2f}"),
        ("Tiros totales", f"{av['shots_home'] + av['shots_away']:.1f}"),
        ("Tiros a puerta", f"{av['sot_home'] + av['sot_away']:.1f}"),
        ("Tiros de esquina", f"{av['corners_home'] + av['corners_away']:.1f}"),
        ("Tarjetas amarillas", f"{av['yellow_home'] + av['yellow_away']:.1f}"),
        ("Faltas", f"{av['fouls_home'] + av['fouls_away']:.1f}"),
        ("Ambos equipos anotan", f"{result['both_score']:.1f}%"),
        ("Más de 2.5 goles", f"{result['over_25']:.1f}%"),
    ]
    for label, value in stats:
        st.markdown(
            f"<div class='stat-row'><span>{html.escape(label)}</span>"
            f"<strong>{html.escape(value)}</strong></div>",
            unsafe_allow_html=True)
    st.caption(
        "Proyecciones de un modelo experimental. Si faltan resultados históricos, "
        "se usan promedios generales; tiros, córners, faltas y tarjetas usan "
        "supuestos generales, no datos históricos específicos. "
        "El xG mostrado es una aproximación basada en goles, no xG oficial."
    )

def render_match_card(match, sport_label, league_name, historical_data, sport_path, league_code, selected_date):
    home, away = match["home"], match["away"]
    hname, aname = team_name(home), team_name(away)
    hlogo, alogo = safe_logo(home), safe_logo(away)
    with st.container(border=True):
        st.caption(f"{league_name} · {match['status']}")
        if match["state"] == "pre":
            shown = "VS"
        else:
            shown = f"{score_of(home)} : {score_of(away)}"
        st.markdown(team_pair_html(home, away, shown), unsafe_allow_html=True)
        st.caption(f"🏟️ {match['venue']}")
    with st.expander("✦ Ver predicciones y estadísticas", expanded=False):
        if sport_label == "⚽ Fútbol":
            render_monte_carlo_panel(
                match, historical_data, sport_path, league_code, selected_date)
        else:
            st.info("El panel Monte Carlo de este deporte todavía no está implementado; no se mostrarán cifras inventadas.")

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
.predicted-score { text-align:center; font-size:44px; font-weight:800; letter-spacing:2px; padding:8px 0; color:#f4f6f7; }
.prob-label { display:flex; justify-content:space-between; margin:8px 0 2px; color:#e5e7eb; font-size:14px; }
div[data-testid="stExpander"] { border: 1px solid #252a36; border-radius: 12px; }
.stButton button { border-radius: 10px; }
.small-muted { color: #9ca3af; font-size: 12px; }
.analysis-panel {background:#101616;border:1px solid #2b3838;border-radius:22px;padding:12px;margin-top:12px;}
.stApp {background:#080b0c;}
.match-card {background:#101516;border:1px solid #2c3435;border-radius:20px;}
@media (max-width: 650px) { .block-container {padding-left:.7rem;padding-right:.7rem;} .predicted-score {font-size:33px;} }
 
/* Tarjetas de encuentro compactas y adaptadas al teléfono */
.compact-team {font-size:clamp(11px,2.4vw,15px);font-weight:750;line-height:1.2;overflow-wrap:anywhere;}
.compact-score {font-size:clamp(17px,4vw,26px);font-weight:850;text-align:center;white-space:nowrap;}
div[data-testid="stVerticalBlockBorderWrapper"] > div[style*="border"] {border-radius:16px;}
@media(max-width:650px) {
 div[data-testid="stHorizontalBlock"] {flex-wrap:nowrap !important;}
 div[data-testid="column"] {min-width:0 !important;}
 .block-container {padding-left:.7rem;padding-right:.7rem;}
}
.stat-row {display:flex;justify-content:space-between;align-items:center;gap:12px;padding:13px 2px;border-bottom:1px solid #2a3032;font-size:15px;}
.stat-row span {color:#f0f1f2;}
.stat-row strong {color:#f7f7f7;white-space:nowrap;text-align:right;}
.stProgress > div > div > div > div {background-color:#18a653 !important;}
@media(max-width:650px){.stat-row{font-size:13px}.predicted-score{color:#18bb64!important;}}

/* Equipo local y visitante siempre alineados en la misma fila */
.sn-teams {display:flex;flex-direction:row;align-items:center;justify-content:space-between;width:100%;gap:6px;padding:12px 0;box-sizing:border-box;}
.sn-side {width:40%;min-width:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:7px;text-align:center;font-weight:750;font-size:clamp(12px,3.3vw,16px);overflow-wrap:anywhere;line-height:1.25;}
.sn-side img {display:block;width:56px;height:56px;max-width:100%;object-fit:contain;}
.sn-center {width:20%;min-width:0;text-align:center;font-size:clamp(17px,4.5vw,25px);font-weight:800;white-space:nowrap;}
.sn-large .sn-side img {width:82px;height:82px;}
.sn-large .sn-side {font-size:clamp(13px,3.5vw,19px);}
.sn-logo-fallback {font-size:36px;line-height:1.5;}
@media(max-width:420px){.sn-side img{width:48px;height:48px}.sn-large .sn-side img{width:68px;height:68px}.sn-teams{gap:3px;}}
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

    st.caption(f"📅 {len(matches)} partidos   ·   🔴 {live} en vivo   ·   ✓ {finished} finalizados")

    st.markdown(f"### 🏟️ Partidos · {sport_label} · {league_name}")
    st.caption(f"{selected_date.strftime('%d/%m/%Y')} · {len(matches)} partido(s) encontrados")

    if not matches:
        st.info(
            "No se encontraron partidos para esta fecha. Puede que la competición "
            "no tenga encuentros programados o que el proveedor gratuito no la cubra."
        )
    else:
        # Obtener el historial una sola vez por liga y fecha.
        historical_data = (
            historical_events(sport["path"], league_code, selected_date)
            if sport_label == "⚽ Fútbol" else []
        )
        for match in matches:
            render_match_card(match, sport_label, league_name, historical_data, sport["path"], league_code, selected_date)

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
