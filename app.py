import html
import streamlit as st
import requests
import math
import random
from collections import Counter
from datetime import date, timedelta, datetime
from zoneinfo import ZoneInfo
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
    initial_sidebar_state="collapsed",
)

# Fecha local de la interfaz. Streamlit Cloud suele ejecutarse en UTC.
# America/Mexico_City evita que aparezca "mañana" cuando aún es hoy en México.
APP_TIMEZONE = ZoneInfo("America/Mexico_City")
def local_today():
    return datetime.now(APP_TIMEZONE).date()

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
    if sport_path == "baseball" and league_code == "kbo":
        # ESPN's baseball/kbo route returns HTTP 400. Do not request it.
        # KBO needs a separate verified, accessible feed; don't invent fixtures.
        return []
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
        hg = sample_poisson(rng, params["lambda_home"])
        ag = sample_poisson(rng, params["lambda_away"])
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
    if sport_path == "baseball" and league_code == "kbo":
        return []
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
    if not team_id or (sport_path == "baseball" and league_code == "kbo"):
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
               "hs":hs, "aws":aws, "home_id":eh, "away_id":ea, "id":str(e.get("id") or "")}
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

@st.cache_data(ttl=900, show_spinner=False)
def nba_recent_scoreboards(cutoff):
    """NBA: retrieve individual calendar days, avoiding unsupported date ranges."""
    events = {}
    for days_back in range(1, 31):
        day = cutoff - timedelta(days=days_back)
        try:
            for event in get_events("basketball", "nba", day):
                if event.get("id"):
                    events[str(event["id"])] = event
        except (requests.RequestException, ValueError, KeyError):
            continue
    return list(events.values())


def nba_history_for_match(match, events, cutoff):
    """Combine league/team schedules with individual-day scoreboard fallback."""
    league_events = list(events) + nba_recent_scoreboards(cutoff)
    return history_for_match(match, league_events, "basketball", "nba", cutoff)


def show_nba_lineups(lineup, ids, names, source):
    st.markdown("<div class='sn-section-title'>Rotaciones y disponibilidad</div>", unsafe_allow_html=True)
    st.caption(source)
    cols = st.columns(2)
    for col, tid, name in zip(cols, ids, names):
        with col:
            st.markdown(f"**{name}**")
            players = lineup.get(tid, {})
            for label, key in (("Titulares", "starters"), ("Suplentes", "bench"),
                               ("No participaron", "out")):
                group = players.get(key) or []
                st.caption(f"{label}: {', '.join(group[:12]) if group else 'No confirmado'}")
    st.caption("Un boxscore de un partido en vivo no confirma necesariamente "
               "la alineación previa al inicio. 'No participó' tampoco confirma lesión.")


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
    lamh = (.58*ha + .42*ad)*1.08
    lama = (.58*aa + .42*hd)*.94
    lamh = max(.15,min(4.5,lamh))
    lama = max(.15,min(4.5,lama))
    return {
        "lambda_home":lamh,"lambda_away":lama,
        "shots_home": 7.5 + 3.5*lamh,"shots_away":7.5 + 3.5*lama,
        "corners_home":3.0 + 1.35*lamh,"corners_away":3.0 + 1.35*lama,
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

def render_fair_odds(probabilities):
    """Decimal fair odds derived from model probabilities, without bookmaker margin."""
    st.markdown("<div class='sn-section-title'>Cuotas del simulador</div>", unsafe_allow_html=True)
    cards = []
    for label, probability in probabilities:
        p = max(0.0, min(100.0, float(probability)))
        value = f"{100.0 / p:.2f}" if p > 0 else "—"
        cards.append(
            "<div class='sn-odds-card'>"
            f"<div class='sn-odds-label'>{html.escape(label)}</div>"
            f"<div class='sn-odds-value'>{value}</div>"
            f"<div class='sn-odds-prob'>{p:.1f}%</div></div>"
        )
    st.markdown("<div class='sn-odds-grid'>" + "".join(cards) + "</div>", unsafe_allow_html=True)
    st.caption("Cuotas decimales justas del modelo, sin margen comercial. No son cuotas de casas de apuestas.")


def render_probability_comparison(home_label, away_label, home_pct, away_pct, draw_pct=None):
    """Visual comparison; displays model outputs without altering probabilities."""
    h = max(0.0, min(100.0, float(home_pct)))
    a = max(0.0, min(100.0, float(away_pct)))
    d = max(0.0, min(100.0, float(draw_pct))) if draw_pct is not None else None
    segments = [(h, '#8b5cf6'), (a, '#c4b5fd')] if d is None else [(h, '#8b5cf6'), (d, '#75658e'), (a, '#c4b5fd')]
    bar = ''.join(f'<div style="width:{v:.5f}%;background:{color};height:100%"></div>' for v,color in segments)
    middle = f'<span>Empate {d:.1f}%</span>' if d is not None else '<span>Probabilidad de victoria</span>'
    st.markdown(
        '<div class="sn-compare">'
        f'<div class="sn-compare-head"><span>{html.escape(home_label)} · {h:.1f}%</span>{middle}'
        f'<span>{html.escape(away_label)} · {a:.1f}%</span></div>'
        f'<div class="sn-compare-track" style="gap:0">{bar}</div></div>',
        unsafe_allow_html=True)


def render_metric_comparison(title, home, away, total=None):
    """Display existing simulated metrics as a two-team comparison, not new predictions."""
    try:
        h, a = float(home), float(away)
    except (ValueError, TypeError):
        return
    denom = max(0.0, h) + max(0.0, a)
    left = (max(0.0, h) / denom * 100.0) if denom else 50.0
    t = h + a if total is None else float(total)
    st.markdown(
        '<div class="sn-compare">'
        f'<div class="sn-compare-head"><strong>{h:.1f}</strong><span>{html.escape(title)}</span><strong>{a:.1f}</strong></div>'
        f'<div class="sn-compare-track"><div style="width:{left:.3f}%"></div><div></div></div>'
        f'<div class="sn-compare-total">Total proyectado: <strong>{t:.1f}</strong></div></div>',
        unsafe_allow_html=True)


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
        params["lambda_home"] = max(.15, min(4.5, .88*params["lambda_home"] + .12*hh))
        params["lambda_away"] = max(.15, min(4.5, .88*params["lambda_away"] + .12*ah))
        params["shots_home"] = 7.5 + 3.5*params["lambda_home"]
        params["shots_away"] = 7.5 + 3.5*params["lambda_away"]
        params["corners_home"] = 3 + 1.35*params["lambda_home"]
        params["corners_away"] = 3 + 1.35*params["lambda_away"]
    seed = sum((i+1)*ord(ch) for i,ch in enumerate(str(match["id"])))
    result = run_monte_carlo(params, 10000, seed=seed)
    av = result["averages"]
    st.markdown("<div class='sn-panel-head'><div class='sn-kicker'>SIMULADORNY / PREDICTION ENGINE</div>" 
                "<div class='sn-panel-title'>Predicciones del partido</div>"
                "<div class='sn-chip'>✦ Predicción cuantitativa</div></div>", unsafe_allow_html=True)
    st.markdown(team_pair_html(match["home"], match["away"], "VS", large=True),
                unsafe_allow_html=True)
    st.divider()
    if sport_path == "basketball":
        st.markdown("<div class='sn-section-title'>Disponibilidad y titulares NBA</div>", unsafe_allow_html=True)
        st.caption(lineup_source)
        for name, tid in zip(names, ids):
            players = lineup.get(tid, {})
            starters = players.get("starters", [])
            bench = players.get("bench", [])
            out = players.get("out", [])
            st.markdown(f"**{name}** · Titulares: " + (", ".join(starters) if starters else "No confirmados"))
            if bench: st.caption("Suplentes publicados: " + ", ".join(bench))
            if out: st.caption("No jugaron (según boxscore): " + ", ".join(out))
        st.info("Las predicciones NBA usan los últimos resultados de los equipos. "
                "Los titulares se muestran si están publicados, pero NO se aplican "
                "ajustes por jugadores sin datos individuales fiables de impacto y minutos. "
                "Antes del inicio las alineaciones pueden no estar confirmadas.")
    st.markdown("<div class='sn-section-title'>Probabilidades del encuentro</div>", unsafe_allow_html=True)
    render_probability_comparison(home_name, away_name, result["home_win"], result["away_win"], result["draw"])
    for label, value in (
        (f"Victoria {home_name}", result["home_win"]),
        ("Empate", result["draw"]),
        (f"Victoria {away_name}", result["away_win"]),
    ):
        pct = max(0.0, min(100.0, float(value)))
        st.markdown(
            f"<div class='sn-prob'><div class='sn-prob-top'><span>{html.escape(label)}</span>"
            f"<strong>{pct:.1f}%</strong></div><div class='sn-track'>"
            f"<div class='sn-fill' style='width:{pct:.1f}%'></div></div></div>",
            unsafe_allow_html=True)
    render_fair_odds([
        ("Local", result["home_win"]), ("Empate", result["draw"]),
        ("Visitante", result["away_win"]),
    ])
    st.divider()
    st.markdown("<div class='sn-section-title'>Estadísticas proyectadas</div>", unsafe_allow_html=True)
    stats = [
        ("Goles proyectados · local", f"{params['lambda_home']:.2f}"),
        ("Goles proyectados · visitante", f"{params['lambda_away']:.2f}"),
        ("Total de goles esperados · modelo", f"{params['lambda_home'] + params['lambda_away']:.2f}"),
        ("Tiros totales · estimación", f"{av['shots_home'] + av['shots_away']:.1f}"),
        ("Tiros a puerta · estimación", f"{av['sot_home'] + av['sot_away']:.1f}"),
        ("Córners · estimación", f"{av['corners_home'] + av['corners_away']:.1f}"),
        ("Tarjetas · estimación", f"{av['yellow_home'] + av['yellow_away']:.1f}"),
        ("Faltas · estimación", f"{av['fouls_home'] + av['fouls_away']:.1f}"),
        ("Ambos equipos anotan", f"{result['both_score']:.1f}%"),
        ("Más de 2.5 goles", f"{result['over_25']:.1f}%"),
    ]
    render_metric_comparison("Goles proyectados", params['lambda_home'], params['lambda_away'])
    stats.insert(3, ("xG oficial · calidad de disparos", "No disponible"))
    for label, value in stats:
        st.markdown(
            f"<div class='stat-row'><span>{html.escape(label)}</span>"
            f"<strong>{html.escape(value)}</strong></div>",
            unsafe_allow_html=True)
    st.caption(
        "Proyecciones de un modelo experimental. Si faltan resultados históricos, "
        "se usan promedios generales; tiros, córners, faltas y tarjetas usan "
        "supuestos generales, no datos históricos específicos. "
        "El xG auténtico requiere datos de calidad de disparos y no está disponible en esta fuente. "
        "El total proyectado es la suma de las tasas de gol de ambos equipos, no xG oficial."
    )


@st.cache_data(ttl=1800, show_spinner=False)
def sport_boxscore(sport_path, league_code, event_id):
    url = league_url(sport_path, league_code, "summary") + f"?event={event_id}"
    return fetch_json(url)


def _num_stat(value):
    try:
        if value is None or isinstance(value, bool):
            return None
        return float(str(value).replace(",", ""))
    except (ValueError, TypeError):
        return None


def boxscore_team_metrics(payload):
    """Team boxscore, with NBA player-boxscore fallback for AST/REB/3PM/TO."""
    result = {}
    box = payload.get("boxscore") or {}
    for entry in box.get("teams") or []:
        tid = str((entry.get("team") or {}).get("id") or "")
        if not tid:
            continue
        stats = {}
        for item in entry.get("statistics") or []:
            if not isinstance(item, dict):
                continue
            key = str(item.get("name") or item.get("abbreviation") or item.get("label") or "").lower().replace(" ", "")
            value = _num_stat(item.get("value", item.get("displayValue")))
            if value is not None:
                stats[key] = value
        result[tid] = stats

    # ESPN NBA commonly publishes AST/REB/3PM/TO in boxscore.players,
    # even when boxscore.teams.statistics lacks the corresponding totals.
    aliases = {"AST":"assists", "REB":"totalrebounds", "3PM":"threepointfieldgoalsmade", "TO":"turnovers"}
    for team_block in box.get("players") or []:
        tid = str((team_block.get("team") or {}).get("id") or "")
        if not tid:
            continue
        team_stats = result.setdefault(tid, {})
        sums = {k:0.0 for k in aliases.values()}
        seen = {k:0 for k in aliases.values()}
        for group in team_block.get("statistics") or []:
            labels = [str(x).upper() for x in group.get("labels") or []]
            for athlete in group.get("athletes") or []:
                if athlete.get("didNotPlay"):
                    continue
                values = athlete.get("stats") or []
                for pos, label in enumerate(labels):
                    if label not in aliases or pos >= len(values):
                        continue
                    key = aliases[label]
                    val = _num_stat(values[pos])
                    if val is not None:
                        sums[key] += val
                        seen[key] += 1
        for key in sums:
            if seen[key] and key not in team_stats:
                team_stats[key] = sums[key]
    return result


def get_stat(stats, names):
    for key in names:
        if key.lower() in stats:
            return stats[key.lower()]
    return None


def recent_stat_means(games, team_id, sport_path, league_code, definitions):
    """Fetch the five preceding games; missing boxscores remain missing."""
    collected = {key: [] for key in definitions}
    for game in games[:5]:
        eid = game.get("id")
        if not eid:
            continue
        try:
            box = boxscore_team_metrics(sport_boxscore(sport_path, league_code, eid))
            stats = box.get(team_id, {})
            for key, aliases in definitions.items():
                value = get_stat(stats, aliases)
                if value is not None and value >= 0:
                    collected[key].append(value)
        except (requests.RequestException, ValueError, KeyError):
            continue
    return {key: (sum(vals) / len(vals) if len(vals) >= 3 else None)
            for key, vals in collected.items()}


def nba_lineup_information(event_id):
    """Read only explicitly published player availability/starting flags."""
    try:
        payload = sport_boxscore("basketball", "nba", event_id)
    except (requests.RequestException, ValueError, KeyError):
        return {}, "Sin alineaciones confirmadas del proveedor"
    info = {}
    for group in ((payload.get("boxscore") or {}).get("players") or []):
        tid = str((group.get("team") or {}).get("id") or "")
        if not tid:
            continue
        starters, bench, out = [], [], []
        for statgroup in group.get("statistics") or []:
            for athlete in statgroup.get("athletes") or []:
                person = athlete.get("athlete") or {}
                name = person.get("displayName") or person.get("shortName")
                if not name:
                    continue
                did_not_play = athlete.get("didNotPlay") is True
                if did_not_play:
                    out.append(name)
                elif athlete.get("starter") is True:
                    starters.append(name)
                elif athlete.get("starter") is False:
                    bench.append(name)
        if starters or bench or out:
            info[tid] = {"starters": starters, "bench": bench, "out": out}
    return info, ("Alineación publicada en boxscore" if info else
                  "Alineación no confirmada: sin ajustes por titulares")


def nba_simulation_with_lineup(home_games, away_games, seed, lineup, ids, iterations=10000):
    """NBA Monte Carlo; no invented lineup impact when individual data is missing.

    Player-aware adjustment requires individual historical on/off impact and
    confirmed active status. Starter flags alone cannot quantify that impact.
    """
    base = simulate_other_sport(home_games, away_games, "basketball", seed, iterations)
    if base is None:
        return None
    base["lineup_adjusted"] = False
    base["lineup_coverage"] = [bool(lineup.get(tid, {}).get("starters")) for tid in ids]
    return base

def simulate_other_sport(home_games, away_games, sport, seed, iterations=10000):
    """Scores derive from five historical games; no default fictitious projections."""
    if len(home_games) < 3 or len(away_games) < 3:
        return None
    def mean(games, key):
        return sum(float(g[key]) for g in games) / len(games)
    h = max(.05, .55 * mean(home_games, "gf") + .45 * mean(away_games, "ga"))
    a = max(.05, .55 * mean(away_games, "gf") + .45 * mean(home_games, "ga"))
    if sport == "basketball":
        # Normal distribution is more suitable for high-count NBA scoring.
        hs = [float(g["gf"]) for g in home_games]
        ass = [float(g["gf"]) for g in away_games]
        def spread(vals):
            avg = sum(vals) / len(vals)
            return max(8.0, (sum((v-avg)**2 for v in vals)/len(vals))**.5)
        sh, sa = spread(hs), spread(ass)
    rng = random.Random(seed)
    wins = losses = draws = 0
    sumh = suma = 0
    over = 0
    threshold = {"basketball": 220.5, "hockey": 5.5, "baseball": 8.5}[sport]
    for _ in range(iterations):
        if sport == "basketball":
            x = max(0, round(rng.gauss(h, sh)))
            y = max(0, round(rng.gauss(a, sa)))
            if x == y:  # NBA has overtime; simulate the winner, not a draw.
                if rng.random() < h / (h+a):
                    x += 1
                else:
                    y += 1
        else:
            x, y = sample_poisson(rng, h), sample_poisson(rng, a)
            if sport == "baseball" and x == y:
                if rng.random() < h / (h+a): x += 1
                else: y += 1
            if sport == "hockey" and x == y:
                if rng.random() < h / (h+a): x += 1
                else: y += 1
        sumh += x; suma += y
        wins += x > y; losses += x < y; draws += x == y
        over += (x + y) > threshold
    return {"home":sumh/iterations, "away":suma/iterations,
            "win_h":100*wins/iterations, "win_a":100*losses/iterations,
            "draw":100*draws/iterations, "over":100*over/iterations,
            "threshold":threshold}


def render_other_sport_panel(match, events, sport_path, league_code, cutoff):
    names = (team_name(match["home"]), team_name(match["away"]))
    st.markdown("<div class='sn-panel-head'><div class='sn-kicker'>SIMULADORNY / PREDICTION ENGINE</div>"
                "<div class='sn-panel-title'>Predicciones del partido</div>"
                "<div class='sn-chip'>✦ Predicción cuantitativa</div></div>",
                unsafe_allow_html=True)
    st.markdown(team_pair_html(match["home"], match["away"], "VS", large=True),
                unsafe_allow_html=True)
    if sport_path == "basketball":
        home_games, away_games, _ = nba_history_for_match(match, events, cutoff)
    else:
        home_games, away_games, _ = history_for_match(match, events, sport_path, league_code, cutoff)
    seed = sum((i+1)*ord(ch) for i,ch in enumerate(str(match["id"])))
    ids = [str(match[side].get("team", {}).get("id") or "") for side in ("home", "away")]
    lineup, lineup_source = nba_lineup_information(match["id"]) if sport_path == "basketball" else ({}, "")
    prediction = (nba_simulation_with_lineup(home_games, away_games, seed, lineup, ids)
                  if sport_path == "basketball" else
                  simulate_other_sport(home_games, away_games, sport_path, seed))
    if prediction is None:
        st.warning(f"Historial insuficiente: {names[0]} ({len(home_games)}), {names[1]} ({len(away_games)}). "
                   "No se mostrarán cifras inventadas.")
        return
    st.markdown("<div class='sn-section-title'>Probabilidades del encuentro</div>", unsafe_allow_html=True)
    render_probability_comparison(names[0], names[1], prediction["win_h"], prediction["win_a"])
    for label, value in ((f"Victoria {names[0]}", prediction["win_h"]),
                         (f"Victoria {names[1]}", prediction["win_a"])):
        st.markdown(f"<div class='sn-prob'><div class='sn-prob-top'><span>{html.escape(label)}</span>"
                    f"<strong>{value:.1f}%</strong></div><div class='sn-track'>"
                    f"<div class='sn-fill' style='width:{value:.1f}%'></div></div></div>",
                    unsafe_allow_html=True)
    render_fair_odds([
        ("Local", prediction["win_h"]), ("Visitante", prediction["win_a"]),
    ])
    st.divider()
    st.markdown("<div class='sn-section-title'>Estadísticas proyectadas</div>", unsafe_allow_html=True)
    if sport_path == "basketball":
        definitions = {
            "assists": ["assists", "ast"],
            "rebounds": ["totalrebounds", "rebounds", "reb", "trb"],
            "threes": ["threepointfieldgoalsmade", "threepointfieldgoals", "3pm"],
            "turnovers": ["turnovers", "to"],
        }
        unit = "Puntos"
    elif sport_path == "hockey":
        definitions = {"shots": ["shots", "shotsongoal", "sog"],
                       "powerplay": ["powerplaygoals", "ppg"]}
        unit = "Goles"
    else:
        definitions = {"hits": ["hits", "h"], "errors": ["errors", "e"],
                       "walks": ["basesonballs", "walks", "bb"]}
        unit = "Carreras"
    stats = [(f"{unit} · {names[0]}", f"{prediction['home']:.1f}"),
             (f"{unit} · {names[1]}", f"{prediction['away']:.1f}"),
             (f"{unit} totales", f"{prediction['home']+prediction['away']:.1f}"),
             (f"Más de {prediction['threshold']} {unit.lower()}", f"{prediction['over']:.1f}%")]
    ids = [str(match[side].get("team", {}).get("id") or "") for side in ("home", "away")]
    titles = {"assists":"Asistencias", "rebounds":"Rebotes", "threes":"Triples anotados",
              "turnovers":"Pérdidas de balón", "shots":"Tiros a portería",
              "powerplay":"Goles en power play", "hits":"Hits", "errors":"Errores",
              "walks":"Bases por bolas"}
    # Each available metric is sampled in every Monte Carlo iteration.
    # Missing real boxscores are not replaced with fabricated league values.
    rng_metrics = random.Random(seed + 713)
    simulated = {}
    for idx, (games, tid) in enumerate(((home_games, ids[0]), (away_games, ids[1]))):
        observations = {key: [] for key in definitions}
        for game in games[:5]:
            try:
                payload = sport_boxscore(sport_path, league_code, str(game["id"]))
                actual = boxscore_team_metrics(payload).get(tid, {})
                for key, aliases in definitions.items():
                    val = get_stat(actual, aliases)
                    if val is not None and val >= 0:
                        observations[key].append(float(val))
            except (requests.RequestException, ValueError, KeyError, TypeError):
                continue
        for key, values in observations.items():
            if len(values) >= 3:
                # Bootstrap: sample 10,000 complete game-level values from
                # the actual observed metric distribution for this team.
                draws = [rng_metrics.choice(values) for _ in range(10000)]
                simulated[(idx,key)] = sum(draws) / len(draws)
    for key in definitions:
        left, right = simulated.get((0,key)), simulated.get((1,key))
        if left is None or right is None:
            continue  # Don't clutter UI with unavailable rows.
        stats.extend([
            (f"{titles[key]} · {names[0]}", f"{left:.1f}"),
            (f"{titles[key]} · {names[1]}", f"{right:.1f}"),
            (f"{titles[key]} · total", f"{left+right:.1f}"),
        ])

    render_metric_comparison(unit + " proyectados", prediction['home'], prediction['away'])
    for metric_key in definitions:
        left, right = simulated.get((0, metric_key)), simulated.get((1, metric_key))
        if left is not None and right is not None:
            render_metric_comparison(titles[metric_key], left, right)
    with st.expander("Ver desglose numérico", expanded=False):
        for label, value in stats:
            st.markdown(f"<div class='stat-row'><span>{html.escape(label)}</span>"
                        f"<strong>{html.escape(value)}</strong></div>", unsafe_allow_html=True)
    # Compact comparison cards above replace the long list of repeated rows.
    st.caption("Proyecciones experimentales; las estadísticas adicionales se remuestrean "
               "a partir de boxscores verificados. Las alineaciones aún no ajustan el modelo.")

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
            render_other_sport_panel(match, historical_data, sport_path, league_code, selected_date)

# --------------------------- INTERFAZ PREMIUM (SOLO PRESENTACIÓN) ---------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');
:root{color-scheme:dark;--bg:#090a0c;--surface:#17191c;--border:#373b40;--muted:#a0a4aa;--accent:#e8e9eb}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif!important}
.stApp{background:radial-gradient(ellipse 110% 380px at 50% -120px,#22252a 0%,#090a0c 72%);color:#f4f5f6}
.block-container{max-width:920px!important;padding:20px 17px 90px!important}
[data-testid="stSidebar"],[data-testid="collapsedControl"]{display:none!important}
header[data-testid="stHeader"]{background:transparent!important}
h1,h2,h3,p,label{color:#f2f3f4}
.sn-header{display:flex;align-items:center;justify-content:space-between;padding:8px 0 18px;gap:12px}
.sn-mark{display:flex;align-items:center;gap:10px}.sn-logo{width:39px;height:39px;border-radius:13px;background:linear-gradient(140deg,#d3d6db,#737982);color:#101114;display:grid;place-items:center;font-size:23px;font-weight:900;box-shadow:0 5px 22px #ffffff15}
.sn-wordmark{font-weight:800;font-size:clamp(19px,5vw,25px);letter-spacing:-.8px;color:#faf8fc;line-height:1.1}.sn-wordmark span{color:#eceef0}
.sn-brand-sub{font-size:9px;letter-spacing:2.4px;font-weight:800;color:#92979d;margin-top:4px}
.sn-header-tag{font-size:10px;color:#afb3b8;border:1px solid #41464c;border-radius:30px;padding:7px 10px;white-space:nowrap}
.sn-hero{background:linear-gradient(130deg,#202226,#15171a 70%);border:1px solid #42474e;border-radius:23px;padding:19px 19px 18px;margin:4px 0 18px;box-shadow:0 14px 30px #0003}
.sn-eyebrow{color:#d3d6db;font-size:10px;letter-spacing:2px;font-weight:800}.sn-hero-title{font-size:clamp(21px,5.2vw,30px);font-weight:800;letter-spacing:-1.1px;line-height:1.15;margin:9px 0}.sn-hero-desc{font-size:13px;color:#aeb3ba;line-height:1.5;max-width:500px}
.sn-pills{display:flex;align-items:center;gap:8px;margin-top:14px;flex-wrap:wrap}.sn-pill{font-size:11px;font-weight:700;background:#292c31;border:1px solid #44494f;border-radius:99px;padding:7px 10px;color:#e6e7e9}.sn-pill-live{color:#f1b7bd;background:#3b252c;border-color:#62404b}
.sn-list-heading{font-size:clamp(24px,6vw,32px);font-weight:800;letter-spacing:-1px;margin:17px 0 6px;color:#f8f6fa}.sn-list-heading span{font-size:12px;letter-spacing:0;font-weight:500;color:#a392ba;margin-left:7px}
.sn-section-label{font-size:11px;color:#adb1b7;letter-spacing:1.5px;font-weight:800;margin:13px 0 9px}
.sn-competition{color:#adb1b7;font-size:12px;margin:0 0 13px}
[data-testid="stTextInput"] input,[data-testid="stDateInput"] input,[data-testid="stSelectbox"]>div>div{background:#1e2125!important;color:#f7f5f9!important;border:1px solid #41464d!important;border-radius:13px!important;min-height:45px}
[data-testid="stTextInput"] input:focus{border-color:#e8e9eb!important}
[data-testid="stRadio"]>div[role="radiogroup"]{display:flex!important;flex-wrap:nowrap!important;overflow-x:auto!important;gap:7px!important;padding:3px 0 10px!important;scrollbar-width:none}
[data-testid="stRadio"]>div[role="radiogroup"] label{border:1px solid #41464d!important;border-radius:12px!important;background:#22252a!important;padding:10px 13px!important;white-space:nowrap!important;flex-shrink:0!important;margin:0!important}
[data-testid="stRadio"]>div[role="radiogroup"] label:has(input:checked){background:#f0f1f3!important;border-color:#f0f1f3!important}
[data-testid="stRadio"]>div[role="radiogroup"] label:has(input:checked) p{color:#17191c!important;font-weight:800!important}
[data-testid="stRadio"] [data-baseweb="radio"]>div:first-child{display:none!important}
[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p{font-size:13px!important}
[data-testid="stDateInput"]{max-width:230px}
[data-testid="stExpander"]{background:#17191c!important;border:1px solid #373b42!important;border-radius:16px!important;overflow:hidden;margin:5px 0 15px}
[data-testid="stExpander"] summary{color:#f0f1f3!important;font-weight:750!important;font-size:13px!important}
[data-testid="stVerticalBlockBorderWrapper"]>div[style*="border"]{background:linear-gradient(145deg,#1e2125,#121416)!important;border:1px solid #373b42!important;border-radius:19px!important;box-shadow:0 8px 25px #0003}
.sn-teams{display:flex;flex-direction:row;align-items:center;justify-content:space-between;width:100%;gap:6px;padding:13px 0;box-sizing:border-box}
.sn-side{width:40%;min-width:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;text-align:center;font-weight:750;font-size:clamp(12px,3.2vw,16px);overflow-wrap:anywhere;line-height:1.25;color:#f8f6fa}
.sn-side img{display:block;width:56px;height:56px;max-width:100%;object-fit:contain;filter:drop-shadow(0 6px 10px #0007)}
.sn-center{width:20%;min-width:0;text-align:center;font-size:clamp(17px,4.5vw,25px);font-weight:800;white-space:nowrap;color:#e7e8eb}
.sn-large .sn-side img{width:73px;height:73px}.sn-large .sn-side{font-size:clamp(13px,3.5vw,18px)}
.sn-logo-fallback{font-size:32px}
.sn-panel-head{padding:7px 0 14px;border-bottom:1px solid #31283f;margin-bottom:16px}
.sn-kicker{color:#d2d5d9;font-size:10px;letter-spacing:1.8px;font-weight:800;margin-bottom:9px}
.sn-panel-title{font-size:clamp(21px,5vw,27px);font-weight:800;letter-spacing:-.6px;color:#f5fafa}
.sn-chip{display:inline-block;background:#292c31;color:#f1f1f2;border:1px solid #555b62;padding:7px 11px;border-radius:99px;font-size:11px;font-weight:750;margin-top:12px}
.sn-section-title{font-size:19px;font-weight:800;letter-spacing:-.4px;margin:20px 0 17px;color:#f8f6fb}
.sn-prob{margin:0 0 18px}.sn-prob-top{display:flex;justify-content:space-between;gap:12px;font-size:13px;font-weight:650;margin-bottom:9px;color:#dce8e8}.sn-prob-top strong{font-variant-numeric:tabular-nums}
.sn-track{height:8px;border-radius:99px;background:#383c42;overflow:hidden}.sn-fill{height:100%;border-radius:99px;background:linear-gradient(90deg,#767c85,#eceef0)}
.stat-row{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:13px 1px;border-bottom:1px solid #402f54;font-size:13px}.stat-row span{color:#aeb2b8;max-width:70%}.stat-row strong{color:#f7f5f9;font-variant-numeric:tabular-nums;text-align:right;white-space:nowrap}
.sn-teams{padding:15px 3px 19px!important}
.stButton button{border-radius:12px!important}
[data-testid="stAlert"]{border-radius:14px!important}
@media(max-width:500px){.block-container{padding:16px 12px 70px!important}.sn-hero{padding:17px}.sn-header-tag{display:none}.sn-side img{width:48px;height:48px}.sn-large .sn-side img{width:63px;height:63px}.sn-teams{gap:3px}.stat-row{font-size:12px}}
.sn-odds-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px;margin:8px 0 12px}
.sn-odds-card{background:linear-gradient(145deg,#24272b,#17191c);border:1px solid #454a51;border-radius:15px;text-align:center;padding:15px 7px}
.sn-odds-label{color:#bfc3c9;font-size:11px;font-weight:700}
.sn-odds-value{color:#f3f4f5;font-size:clamp(20px,5vw,29px);font-weight:850;margin:6px 0;font-variant-numeric:tabular-nums}
.sn-odds-prob{color:#c4c8cf;font-size:11px}
/* Comparison widgets */
.sn-compare{background:linear-gradient(150deg,#24272b,#15171a);border:1px solid #4c3568;border-radius:16px;padding:13px 14px;margin:10px 0}
.sn-compare-head{display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:11px;color:#f3ebfc;font-size:12px;font-weight:750}
.sn-compare-head span:nth-child(2){color:#a9aeb5;font-size:11px;font-weight:600;text-align:center}
.sn-compare-track{display:flex;width:100%;height:8px;overflow:hidden;border-radius:12px;background:#33373c;gap:3px}
.sn-compare-track div:first-child{background:linear-gradient(90deg,#7f858d,#a8adb4)}
.sn-compare-track div:last-child{background:linear-gradient(90deg,#d2d5d9,#e3e5e7);flex:1}
.sn-compare-total{text-align:center;color:#a9aeb5;font-size:11px;margin-top:9px}
.sn-odds-grid:has(.sn-odds-card:nth-child(2):last-child){grid-template-columns:repeat(2,minmax(0,1fr))}
.sn-odds-card{box-shadow:0 8px 20px #0002}
@media(max-width:500px){.sn-compare{padding:12px 10px}.sn-odds-value{font-size:23px}}

/* SIMULADORNY / OBSIDIAN: premium compact mobile-first presentation */
.stApp{background:radial-gradient(ellipse 95% 390px at 85% -90px,#24272d 0%,transparent 75%),radial-gradient(ellipse 70% 350px at -25% 350px,#1a1d22 0%,transparent 80%),#0b0c0e!important}
.block-container{max-width:1040px!important;padding-top:14px!important}
[data-testid="stVerticalBlock"]{gap:.7rem!important}
.sn-header{padding:4px 0 9px}
.sn-logo{width:44px;height:44px;border-radius:14px;background:linear-gradient(145deg,#e5e7e9,#a5aab0 52%,#676d75);box-shadow:0 0 0 1px #c8a8f460,0 9px 30px #ffffff16}
.sn-wordmark{font-size:clamp(21px,5.5vw,29px);letter-spacing:-1.1px}
.sn-brand-sub{color:#a5aab1;letter-spacing:2.7px}
.sn-header-tag{border-color:#555b62;color:#e6e8ea;background:#22252a}
.sn-hero{position:relative;isolation:isolate;overflow:hidden;border:1px solid #454b52;background:linear-gradient(122deg,#25282d 0%,#181a1e 57%,#181a1e 100%);border-radius:24px;padding:22px 22px 20px;margin:2px 0 8px;box-shadow:0 18px 55px #0006,inset 0 1px #f1f1f228}
.sn-hero:before{content:'';position:absolute;z-index:-1;width:245px;height:245px;border-radius:50%;right:-85px;top:-110px;background:radial-gradient(circle,#ffffff1c,transparent 67%);filter:blur(4px)}
.sn-hero:after{content:'';position:absolute;z-index:-1;width:180px;height:180px;right:-35px;bottom:-130px;border:1px solid #eceef055;border-radius:50%;box-shadow:0 0 0 28px #ffffff06,0 0 0 57px #ffffff05}
.sn-eyebrow{color:#e0e2e5;font-size:10px;letter-spacing:2px}
.sn-hero-title{font-size:clamp(27px,7vw,46px);letter-spacing:-1.8px;line-height:1.08;max-width:570px;margin:12px 0 11px}
.sn-hero-title em{font-style:normal;background:linear-gradient(95deg,#fff,#c7cbd0);-webkit-background-clip:text;background-clip:text;color:transparent}
.sn-hero-desc{font-size:13px;color:#b5bac1;max-width:370px}
.sn-pills{margin-top:17px;gap:7px}.sn-pill{font-size:10px;padding:7px 10px;background:#ffffff0c;border-color:#ffffff26;color:#e4e6e9}.sn-pill-live{color:#ffbbc8;background:#fa567a12;border-color:#f57c994d}
.sn-micro{display:flex;align-items:center;gap:8px;margin-top:17px;padding-top:14px;border-top:1px solid #d5baf720;color:#b5bac1;font-size:11px;flex-wrap:wrap}
.sn-micro b{color:#f7f2fd;font-weight:750}.sn-micro-dot{height:5px;width:5px;border-radius:50%;background:#f0f1f2}
.sn-workflow{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin:0 0 5px}
.sn-step{border:1px solid #3b4046;background:linear-gradient(155deg,#202327,#15171a);border-radius:14px;padding:12px 10px;min-width:0}
.sn-step-icon{font-size:17px;color:#d9dce0;margin-bottom:6px}.sn-step-name{font-size:11px;font-weight:800;color:#f3f4f5}.sn-step-sub{font-size:10px;color:#aab0b7;margin-top:3px;line-height:1.3}
.sn-list-heading{margin:11px 0 1px;font-size:clamp(23px,6vw,30px)}
.sn-list-heading span{display:block;margin:3px 0 0;font-size:11px;color:#a9afb6}
.sn-section-label{margin:3px 0 4px;color:#b9bec5}
[data-testid="stTextInput"] input,[data-testid="stDateInput"] input,[data-testid="stSelectbox"]>div>div{background:#1b1d21!important;border-color:#42474e!important;box-shadow:inset 0 1px #ffffff0a!important}
[data-testid="stRadio"]>div[role="radiogroup"]{padding-bottom:4px!important;gap:6px!important}
[data-testid="stRadio"]>div[role="radiogroup"] label{border-color:#3a3f45!important;background:#1f2226!important;border-radius:11px!important;padding:9px 12px!important}
[data-testid="stRadio"]>div[role="radiogroup"] label:has(input:checked){background:linear-gradient(135deg,#f0f1f3,#d9dce0)!important;border-color:#f0f1f3!important;box-shadow:0 4px 17px #ffffff16}
[data-testid="stRadio"]>div[role="radiogroup"] label:has(input:checked) p{color:#fff!important}
[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p{font-size:12px!important}
[data-testid="stDateInput"]{max-width:190px}
[data-testid="stExpander"]{background:#1b1d21!important;border-color:#3a3e45!important}
.sn-odds-card{background:linear-gradient(145deg,#292c31,#1b1d21);border-color:#704c9c}
.sn-compare{background:linear-gradient(150deg,#25282d,#17191c)}
@media(max-width:500px){.block-container{padding:12px 13px 75px!important}.sn-hero{padding:19px 17px}.sn-hero-title{font-size:clamp(27px,7.1vw,34px)}.sn-step{padding:10px 8px}.sn-step-name{font-size:10px}.sn-step-sub{font-size:9px}.sn-pills{gap:5px}.sn-pill{padding:6px 8px}}

/* OBSIDIAN MONO: accessible monochrome styling */
.sn-logo{background:linear-gradient(145deg,#f4f5f6,#9ea3aa)!important;color:#111315!important;box-shadow:0 4px 22px #ffffff12!important}
.sn-wordmark span{color:#d6d9dd!important}
.sn-hero{background:linear-gradient(120deg,#272a2f,#15171a 75%)!important;border-color:#484d54!important}
.sn-hero:before{background:radial-gradient(circle,#ffffff16,transparent 70%)!important}
.sn-hero-title em{background:linear-gradient(95deg,#fff,#aeb3ba);-webkit-background-clip:text;background-clip:text;color:transparent}
[data-testid="stRadio"]>div[role="radiogroup"] label:has(input:checked){background:#f0f1f3!important;border-color:#f0f1f3!important;box-shadow:none!important}
[data-testid="stRadio"]>div[role="radiogroup"] label:has(input:checked) p{color:#121416!important}
.sn-fill{background:linear-gradient(90deg,#828891,#eceef0)!important}
.sn-odds-value{color:#f4f5f6!important}
.sn-compare-track div:first-child{background:#e3e5e8!important}.sn-compare-track div:last-child{background:#747b84!important}
.sn-date-title{font-size:11px;color:#9da3ab;letter-spacing:1.5px;font-weight:800;margin:5px 0 4px}
div[data-testid="stHorizontalBlock"]:has(.sn-date-title){align-items:center}
.stButton button[kind="secondary"]{background:#1c1f23!important;border:1px solid #353a40!important;color:#d7dade!important;border-radius:13px!important;min-height:58px!important;padding:7px 2px!important}
.stButton button[kind="primary"]{background:#e8eaed!important;border:1px solid #e8eaed!important;color:#141619!important;border-radius:13px!important;min-height:58px!important;padding:7px 2px!important;font-weight:800!important}
.stButton button p{font-size:12px!important;line-height:1.25!important;white-space:pre-line!important}
@media(max-width:500px){.sn-hero{padding:14px 16px!important}.sn-hero-title{font-size:24px!important}.sn-hero-desc{font-size:12px!important}.sn-workflow{display:none!important}.sn-micro{margin-top:10px!important;padding-top:9px!important}}
/* El radio semanal se desplaza lateralmente en iPhone; jamás se convierte en columna. */
[data-testid="stRadio"] [role="radiogroup"]{
 display:flex!important;flex-direction:row!important;flex-wrap:nowrap!important;
 overflow-x:auto!important;overflow-y:hidden!important;gap:7px!important;
 width:100%!important;max-width:100%!important;padding:4px 1px 10px!important;
 -webkit-overflow-scrolling:touch;scrollbar-width:none;
}
[data-testid="stRadio"] [role="radiogroup"]::-webkit-scrollbar{display:none}
[data-testid="stRadio"] [role="radiogroup"]>label{
 flex:0 0 auto!important;white-space:nowrap!important;min-width:max-content!important;
}
/* En la franja de fechas, el día activo debe tener texto oscuro sobre blanco. */
[data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) *{color:#141619!important}
[data-testid="stRadio"] [role="radiogroup"] label:has(input:checked){background:#f0f1f3!important;border-color:#f0f1f3!important}
</style>

""",unsafe_allow_html=True)

st.markdown("""
<div class="sn-header"><div class="sn-mark"><div class="sn-logo">✦</div><div>
<div class="sn-wordmark">SIMULADOR<span>NY</span></div><div class="sn-brand-sub">SPORTS INTELLIGENCE</div>
</div></div><div class="sn-header-tag">✦ PREDICTION LAB</div></div>
""",unsafe_allow_html=True)

search = st.text_input("Buscar equipos", placeholder="⌕  Buscar equipos...", label_visibility="collapsed")
st.markdown("<div class='sn-list-heading'>Centro de partidos <span>Encuentra un encuentro y descubre lo que proyecta el modelo</span></div>", unsafe_allow_html=True)
status_filter = st.radio("Estado", ["Todos", "En vivo", "Próximos", "Finalizados"],
                         horizontal=True, label_visibility="collapsed", key="status_tabs")
# Calendario semanal: un único control horizontal (sin columnas que se apilen en móvil).
if "sn_selected_date" not in st.session_state:
    st.session_state.sn_selected_date = local_today()
selected_date = st.session_state.sn_selected_date
short_days = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
week_days = [selected_date + timedelta(days=i) for i in range(-3, 4)]
labels_by_date = {
    day.isoformat(): ("Hoy" if day == local_today() else short_days[day.weekday()]) + f"  {day.day}"
    for day in week_days
}
# El calendario puede saltar a cualquier fecha. El selector se sincroniza ANTES de dibujar el widget.
if st.session_state.get("sn_week_choice") not in labels_by_date:
    st.session_state.sn_week_choice = selected_date.isoformat()

def _sn_change_day():
    st.session_state.sn_selected_date = date.fromisoformat(st.session_state.sn_week_choice)

st.markdown('<div class="sn-date-title">SELECCIONA EL DÍA</div>', unsafe_allow_html=True)
with st.popover("▦  Calendario", use_container_width=False):
    # Sin key persistente: se inicializa siempre desde el día elegido en la franja.
    chosen = st.date_input("Ir a fecha", value=selected_date)
    if chosen != selected_date:
        st.session_state.sn_selected_date = chosen
        st.session_state.sn_week_choice = chosen.isoformat()
        st.rerun()
st.radio(
    "Calendario semanal",
    options=list(labels_by_date),
    format_func=lambda iso: labels_by_date[iso],
    horizontal=True,
    label_visibility="collapsed",
    key="sn_week_choice",
    on_change=_sn_change_day,
)
selected_date = st.session_state.sn_selected_date

st.markdown("<div class='sn-section-label'>ELIGE TU DEPORTE</div>", unsafe_allow_html=True)
sport_label = st.radio("Deporte", list(SPORTS.keys()), horizontal=True,
                       label_visibility="collapsed", key="sport_tabs")
sport = SPORTS[sport_label]
if sport_label == "⚾ KBO":
    st.info("KBO: la fuente ESPN utilizada no ofrece un endpoint válido para esta liga. "
            "Se ha desactivado esa consulta para evitar el error HTTP 400. "
            "Los partidos y las predicciones KBO requieren integrar otra fuente verificable.")
with st.expander("Liga o competición", expanded=False):
    league_name = st.selectbox("Selecciona una liga", list(sport["leagues"].keys()))
st.markdown("<div class='sn-competition'>" + html.escape(league_name) + "</div>", unsafe_allow_html=True)

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

    st.caption(f"{len(matches)} encuentros  ·  {live} en vivo  ·  {finished} finalizados")

    st.markdown(f"<div class='sn-section-title'>{html.escape(sport_label)} · Encuentros</div>", unsafe_allow_html=True)
    st.caption(f"{selected_date.strftime('%d/%m/%Y')} · {len(matches)} encuentros")

    if not matches:
        st.info(
            "No se encontraron partidos para esta fecha. Puede que la competición "
            "no tenga encuentros programados o que el proveedor gratuito no la cubra."
        )
    else:
        # Obtener el historial una sola vez por liga y fecha.
        historical_data = (
            historical_events(sport["path"], league_code, selected_date)
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
