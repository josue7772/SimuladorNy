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
    initial_sidebar_state="collapsed",
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


def boxscore_team_metrics(payload):
    """Only use actual published team boxscore numbers, never synthetic assists/rebounds."""
    result = {}
    for entry in (payload.get("boxscore") or {}).get("teams") or []:
        tid = str((entry.get("team") or {}).get("id") or "")
        if not tid:
            continue
        stats = {}
        for item in entry.get("statistics") or []:
            if not isinstance(item, dict):
                continue
            key = str(item.get("name") or item.get("abbreviation") or item.get("label") or "").lower().replace(" ", "")
            val = item.get("value", item.get("displayValue"))
            if isinstance(val, (int, float)):
                stats[key] = float(val)
            elif isinstance(val, str):
                try:
                    stats[key] = float(val.replace(",", ""))
                except ValueError:
                    pass
        result[tid] = stats
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
                   "Se intentaron calendarios de equipos y 30 días de marcadores NBA. "
                   "No se mostrarán cifras inventadas.")
        return
    st.markdown("<div class='sn-section-title'>Probabilidades del encuentro</div>", unsafe_allow_html=True)
    for label, value in ((f"Victoria {names[0]}", prediction["win_h"]),
                         (f"Victoria {names[1]}", prediction["win_a"])):
        st.markdown(f"<div class='sn-prob'><div class='sn-prob-top'><span>{html.escape(label)}</span>"
                    f"<strong>{value:.1f}%</strong></div><div class='sn-track'>"
                    f"<div class='sn-fill' style='width:{value:.1f}%'></div></div></div>",
                    unsafe_allow_html=True)
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
        for game in games[:10]:
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

    for label, value in stats:
        st.markdown(f"<div class='stat-row'><span>{html.escape(label)}</span>"
                    f"<strong>{html.escape(value)}</strong></div>", unsafe_allow_html=True)
    if sport_path == "basketball":
        st.caption("Las alineaciones visibles son informativas: la versión actual NO ajusta "
                   "todavía los escenarios por minutos y estadísticas individuales. "
                   "Se requieren datos de jugadores verificados para hacerlo.")
    st.caption("Proyecciones Monte Carlo experimentales. Las métricas adicionales "
               "se simulan mediante remuestreo de boxscores históricos cuando existen "
               "al menos tres registros. No se muestran métricas sin datos suficientes.")

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

/* SIMULADORNY PREMIUM MOBILE UI */
:root{color-scheme:dark}
.stApp{background:radial-gradient(ellipse 90% 35% at 50% -12%,#15342d 0%,#080b0d 72%);color:#f6f8f7}
.block-container{max-width:920px;padding-top:1.3rem}
section[data-testid="stSidebar"]{background:#0c1114;border-right:1px solid #26312f}
[data-testid="stVerticalBlockBorderWrapper"] > div[style*="border"]{border:1px solid #263531!important;background:linear-gradient(140deg,#141d1d,#0c1113)!important;border-radius:22px!important;box-shadow:0 10px 30px rgba(0,0,0,.15)}
[data-testid="stExpander"]{border:1px solid #263531!important;background:#0e1415!important;border-radius:17px!important;overflow:hidden}
[data-testid="stExpander"] summary{font-weight:700;color:#eaf4ef;padding:8px 4px}
.sn-panel-head{padding:10px 0 18px;border-bottom:1px solid #25312d;margin-bottom:18px}
.sn-kicker{color:#7de1b5;font-size:10px;letter-spacing:2.3px;font-weight:800;margin-bottom:8px}
.sn-panel-title{font-size:clamp(22px,5vw,30px);font-weight:800;letter-spacing:-.8px;color:#f8faf9;line-height:1.2}
.sn-chip{display:inline-block;background:#113426;color:#5de2a2;border:1px solid #235e42;padding:7px 11px;border-radius:100px;font-size:11px;font-weight:750;margin-top:14px}
.sn-section-title{font-size:19px;font-weight:800;letter-spacing:-.4px;margin:20px 0 18px;color:#f3f8f6}
.sn-prob{margin:0 0 18px}
.sn-prob-top{display:flex;justify-content:space-between;gap:12px;font-size:13px;font-weight:650;margin-bottom:9px;color:#e3ece8}
.sn-prob-top strong{font-variant-numeric:tabular-nums;color:#f8faf9}
.sn-track{height:8px;border-radius:100px;background:#293331;overflow:hidden}
.sn-fill{height:100%;border-radius:100px;background:linear-gradient(90deg,#149e71,#59e6a6)}
.sn-teams{padding:15px 5px 19px!important}
.sn-side{font-size:clamp(12px,3.1vw,16px)!important;color:#f2f7f4}
.sn-side img{width:54px;height:54px;filter:drop-shadow(0 5px 12px rgba(0,0,0,.35))}
.sn-large .sn-side img{width:72px;height:72px}
.sn-center{color:#9caea6!important;font-size:clamp(16px,4vw,22px)!important}
.stat-row{padding:14px 1px!important;border-bottom:1px solid #26312e!important;font-size:13px!important}
.stat-row span{color:#bacac3!important;max-width:70%}
.stat-row strong{color:#f4faf6!important;font-variant-numeric:tabular-nums}
@media(max-width:500px){.block-container{padding-left:13px!important;padding-right:13px!important}.sn-large .sn-side img{width:62px;height:62px}.sn-panel-title{font-size:22px}}

/* Mobile-first premium dashboard */
[data-testid="stSidebar"]{display:none!important}
[data-testid="collapsedControl"]{display:none!important}
.block-container{max-width:940px!important;padding-top:22px!important}
.sn-topbar{padding:7px 2px 21px;border-bottom:1px solid #22292d}
.sn-wordmark{font-weight:900;font-size:23px;letter-spacing:1.1px;color:#f8fafb}
.sn-wordmark span{color:#89949a}
.sn-brand-sub{font-size:9px;letter-spacing:3px;font-weight:800;color:#88949b;margin-top:2px}
.sn-trending{display:flex;align-items:center;gap:14px;overflow:hidden;white-space:nowrap;padding:22px 0 18px;border-bottom:1px solid #22292d;font-size:13px}
.sn-fire{background:#f3f5f6;color:#141718;border-radius:28px;padding:9px 12px;font-weight:800}
.sn-live{color:#f05d70;border:1px solid #b63b50;padding:8px 12px;border-radius:14px;font-weight:800}
.sn-trend-desc{color:#9fa9ad;font-size:12px}
.sn-list-heading{font-size:29px;font-weight:850;margin:13px 0 14px;letter-spacing:-.8px}
.sn-list-heading span{font-size:12px;font-weight:500;color:#9ca7aa;letter-spacing:0}
.sn-sport-label{color:#98a4a8;font-size:10px;font-weight:800;letter-spacing:2px;margin:15px 0 8px}
.sn-competition{color:#9aa8a9;font-size:12px;margin:4px 0 16px}
[data-testid="stRadio"]>div[role="radiogroup"]{display:flex!important;flex-wrap:nowrap!important;overflow-x:auto!important;gap:7px!important;padding:2px 0 10px!important;scrollbar-width:none}
[data-testid="stRadio"]>div[role="radiogroup"] label{border:1px solid #333d42!important;border-radius:12px!important;background:#1a2125!important;padding:9px 12px!important;white-space:nowrap!important;flex-shrink:0!important;margin:0!important}
[data-testid="stRadio"]>div[role="radiogroup"] label:has(input:checked){background:#f3f5f5!important;border-color:#f3f5f5!important}
[data-testid="stRadio"]>div[role="radiogroup"] label:has(input:checked) p{color:#111619!important;font-weight:800!important}
[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p{font-size:13px!important}
[data-testid="stRadio"] [data-baseweb="radio"]>div:first-child{display:none!important}
[data-testid="stDateInput"]{max-width:260px}
[data-testid="stTextInput"] input{background:#141a1d!important;border:1px solid #344046!important;border-radius:13px!important;padding:14px!important}
@media(max-width:550px){.block-container{padding-left:15px!important;padding-right:15px!important}.sn-trending{gap:9px}.sn-wordmark{font-size:21px}.sn-list-heading{font-size:27px}}
</style>
""", unsafe_allow_html=True)

# --------------------------- INTERFAZ PRINCIPAL ---------------------------
st.markdown("""
<div class="sn-topbar"><div class="sn-wordmark">SIMULADOR<span>NY</span></div>
<div class="sn-brand-sub">SPORTS ANALYSIS</div></div>
<div class="sn-trending"><span class="sn-fire">♨ Tendencias</span><span>Hoy</span>
<span class="sn-live">● EN VIVO</span><span class="sn-trend-desc">Predicciones deportivas</span></div>
""", unsafe_allow_html=True)

search = st.text_input("Buscar equipos", placeholder="⌕  Buscar equipos...", label_visibility="collapsed")
st.markdown("<div class='sn-list-heading'>Partidos <span>· Explorar encuentros</span></div>", unsafe_allow_html=True)
status_filter = st.radio("Estado", ["Todos", "En vivo", "Próximos", "Finalizados"],
                         horizontal=True, label_visibility="collapsed", key="status_tabs")
selected_date = st.date_input("Fecha", value=date.today(), label_visibility="collapsed")
st.markdown("<div class='sn-sport-label'>DEPORTES</div>", unsafe_allow_html=True)
sport_label = st.radio("Deporte", list(SPORTS.keys()), horizontal=True,
                       label_visibility="collapsed", key="sport_tabs")
sport = SPORTS[sport_label]
with st.expander("⚙ Liga / competición", expanded=False):
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

    st.caption(f"{len(matches)} partidos  ·  {live} en vivo  ·  {finished} finalizados")

    st.markdown(f"#### {sport_label} · Partidos")
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
