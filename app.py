import html
import streamlit as st
import requests
import math
import random
import sqlite3
import json
import os
import bisect
import unicodedata
from collections import Counter
from datetime import date, timedelta, datetime
from zoneinfo import ZoneInfo
from urllib.parse import quote

# ============================================================
# NYUZ — Dashboard deportivo con fuentes gratuitas
# Ejecutar: pip install streamlit requests
#           streamlit run app.py
# ============================================================

st.set_page_config(
    page_title="Nyuz — Analysis AI",
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
    headers = {"User-Agent": "Nyuz/1.0 (Streamlit sports dashboard)"}
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

def estimate_dixon_coles_rho(events, cutoff):
    """Fit a conservative low-score correction on PRE-match league history.

    A pooled Poisson baseline is used for league-level rho estimation; with
    sparse samples the correction is disabled rather than guessed.
    """
    matches = []
    for event in events:
        if event_day(event) is None or event_day(event) >= cutoff:
            continue
        parsed = parse_event(event)
        if not parsed or not parsed["completed"]:
            continue
        hg, ag = numeric_score(parsed["home"]), numeric_score(parsed["away"])
        if hg is None or ag is None or hg < 0 or ag < 0:
            continue
        days = (cutoff - event_day(event)).days
        if days > 365:
            continue
        matches.append((int(hg), int(ag), math.exp(-days / 150)))
    if len(matches) < 35:
        return 0.0, len(matches)
    total_weight = sum(row[2] for row in matches)
    lam = max(.3, min(3.5, sum(h*w for h,a,w in matches)/total_weight))
    mu = max(.3, min(3.5, sum(a*w for h,a,w in matches)/total_weight))
    # Ensure all four Dixon-Coles factors are strictly positive.
    low = max(-.18, -0.95/lam, -0.95/mu)
    high = min(.18, .95, .95/(lam*mu))
    best_rho, best_ll = 0.0, float('-inf')
    for i in range(101):
        rho = low + (high-low)*i/100
        ll = 0.0
        for h,a,w in matches:
            tau = dixon_coles_tau(h,a,lam,mu,rho)
            ll += w * math.log(max(tau, 1e-12))
        # Gaussian regularization prevents unstable fits from small samples.
        ll -= 15.0*rho*rho
        if ll > best_ll:
            best_ll, best_rho = ll, rho
    return best_rho, len(matches)


def dixon_coles_tau(h, a, lam, mu, rho):
    if h == 0 and a == 0:
        return 1 - lam*mu*rho
    if h == 0 and a == 1:
        return 1 + lam*rho
    if h == 1 and a == 0:
        return 1 + mu*rho
    if h == 1 and a == 1:
        return 1 - rho
    return 1.0


def exact_score_distribution(lam, mu, rho, maximum=15):
    """Normalized Dixon-Coles matrix; no sampling noise in score ranking."""
    lam, mu = max(.01,float(lam)), max(.01,float(mu))
    # Clip rho to ensure positive tau for this particular matchup.
    rho = max(-.95/lam, -.95/mu, min(rho, .95, .95/(lam*mu)))
    entries = []
    for h in range(maximum+1):
        for a in range(maximum+1):
            probability = poisson(lam,h)*poisson(mu,a)*dixon_coles_tau(h,a,lam,mu,rho)
            entries.append(((h,a), max(0.0,probability)))
    total = sum(p for _,p in entries)
    return [(score, p/total) for score,p in entries]


def run_monte_carlo(params, iterations=10000, seed=None):
    """Simulación Monte Carlo con parámetros calculados internamente."""
    rng = random.Random(seed)
    scores = Counter()
    score_probs = exact_score_distribution(params["lambda_home"],
                                           params["lambda_away"], params.get("dc_rho", 0.0))
    cumulative, score_keys, acc = [], [], 0.0
    for score, prob in score_probs:
        acc += prob
        cumulative.append(acc)
        score_keys.append(score)
    home_wins = draws = away_wins = both_score = over_25 = 0
    totals = Counter()

    for _ in range(iterations):
        hg, ag = score_keys[min(bisect.bisect_left(cumulative, rng.random()), len(score_keys)-1)]
        hs = sample_poisson(rng, params["shots_home"])
        aws = sample_poisson(rng, params["shots_away"])
        hc = sample_poisson(rng, params["corners_home"])
        ac = sample_poisson(rng, params["corners_away"])
        hy = sample_poisson(rng, params["yellow_home"])
        ay = sample_poisson(rng, params["yellow_away"])
        hf = sample_poisson(rng, params["fouls_home"])
        af = sample_poisson(rng, params["fouls_away"])
        hst = sample_binomial(rng, hs, params.get("sot_ratio_home",0.36))
        ast = sample_binomial(rng, aws, params.get("sot_ratio_away",0.36))

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

    # Exact-score selection uses the full probability distribution, not
    # a noisy 10,000-sample mode. Monte Carlo remains for other projections.
    ranked_scores = sorted(score_probs, key=lambda item: item[1], reverse=True)
    best_score, best_probability = ranked_scores[0]
    metric_keys = ("shots_home", "shots_away", "sot_home", "sot_away",
                   "corners_home", "corners_away", "yellow_home", "yellow_away",
                   "fouls_home", "fouls_away")
    averages = {key: totals[key] / iterations for key in metric_keys}
    return {
        "iterations": iterations,
        "home_win": home_wins / iterations * 100,
        "draw": draws / iterations * 100,
        "away_win": away_wins / iterations * 100,
        "both_score": both_score / iterations * 100,
        "over_25": over_25 / iterations * 100,
        "score": best_score,
        "score_frequency": best_probability * 100,
        "top_scores": [(score, round(prob*iterations)) for score, prob in ranked_scores[:5]],
        "score_probabilities": ranked_scores[:5],
        "dc_rho": params.get("dc_rho", 0.0),
        "averages": averages,
    }

@st.cache_data(ttl=1800, show_spinner=False)
def historical_events(sport_path, league_code, selected_date):
    if sport_path == "baseball" and league_code == "kbo":
        return []
    # Consulta el historial por semanas para evitar límites del proveedor.
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

@st.cache_data(ttl=3600, show_spinner=False)
def soccer_daily_history(league_code, cutoff):
    """Daily scoreboards fallback when ESPN does not honor range queries."""
    found = {}
    # Recent six weeks; cache shared by all fixtures in the league.
    for back in range(1, 43):
        day = cutoff - timedelta(days=back)
        try:
            for event in get_events("soccer", league_code, day):
                if event.get("id"):
                    found[str(event["id"])] = event
        except (requests.RequestException, ValueError, KeyError):
            continue
    return list(found.values())


def normalize_history_event(event):
    """ESPN team schedules sometimes nest the competition and status differently."""
    if not isinstance(event, dict):
        return None
    if event.get("competitions"):
        return event
    competition = event.get("competition")
    if isinstance(competition, dict):
        return {**event, "competitions": [competition]}
    return event

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
            e = normalize_history_event(e)
            if e and e.get("id"):
                raw[str(e["id"])] = e
    # If range queries returned no completed games, request calendar days explicitly.
    if sport_path == "soccer":
        candidates = [e for e in raw.values() if e.get("competitions")]
        usable = sum(bool((parse_event(e) or {}).get("completed")) for e in candidates)
        if usable < 10:
            for e in soccer_daily_history(league_code, cutoff):
                if e.get("id"):
                    raw[str(e["id"])] = e
    home_games, away_games, h2h = [], [], []
    for e in raw.values():
        day = event_day(e)
        if day is None or day >= cutoff or str(e.get("id")) == str(match["id"]):
            continue
        m = parse_event(e)
        if not m or not (m["completed"] or m["state"] == "post"):
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
    return (sorted(home_games, key=key, reverse=True)[:10],
            sorted(away_games, key=key, reverse=True)[:10],
            sorted(h2h, key=key, reverse=True)[:5])

@st.cache_data(ttl=1800, show_spinner=False)
def nba_recent_scoreboards(cutoff):
    """NBA scoreboard history with date-range retrieval and daily fallback.

    ESPN may cap the number of games in a response; collect several windows,
    then fill with day-specific calls when required.
    """
    found = {}
    # Larger windows reduce requests; fall back to individual days below.
    for offset in range(0, 120, 14):
        finish = cutoff - timedelta(days=offset + 1)
        start = max(cutoff - timedelta(days=120), finish - timedelta(days=13))
        url = league_url("basketball", "nba") + (
            f"?dates={start:%Y%m%d}-{finish:%Y%m%d}&limit=500")
        try:
            for event in fetch_json(url).get("events", []):
                if event.get("id"):
                    found[str(event["id"])] = event
        except (requests.RequestException, ValueError, KeyError):
            pass
    # Some ESPN endpoints ignore date ranges or return only partial windows.
    for days_back in range(1, 76):
        day = cutoff - timedelta(days=days_back)
        try:
            for event in get_events("basketball", "nba", day):
                if event.get("id"):
                    found[str(event["id"])] = event
        except (requests.RequestException, ValueError, KeyError):
            continue
    return list(found.values())


def nba_history_for_match(match, events, cutoff):
    """Merge season schedules and NBA scoreboard games without duplicates."""
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


SOCCER_STAT_NAMES = {
    "totalshots":"shots", "shots":"shots", "totalshotsattempts":"shots",
    "shotsontarget":"sot", "shotsongoal":"sot", "shotson target":"sot",
    "cornerkicks":"corners", "corners":"corners",
    "yellowcards":"yellow", "fouls":"fouls", "foulscommitted":"fouls",
}

@st.cache_data(ttl=86400, show_spinner=False)
def historical_soccer_boxscore(league_code, event_id):
    """Cache one ESPN summary per completed fixture; never use future games."""
    try:
        payload = sport_boxscore("soccer", league_code, event_id)
        result = {}
        for entry in (payload.get("boxscore") or {}).get("teams") or []:
            tid = str((entry.get("team") or {}).get("id") or "")
            if not tid:
                continue
            stats = {}
            for item in entry.get("statistics") or []:
                if not isinstance(item,dict):
                    continue
                for field in ("name","abbreviation","label"):
                    normalized = ''.join(c for c in str(item.get(field) or '').lower() if c.isalnum())
                    key = SOCCER_STAT_NAMES.get(normalized)
                    if key:
                        value = _num_stat(item.get("value",item.get("displayValue")))
                        if value is not None and 0 <= value <= 100:
                            stats[key] = value
                        break
            result[tid] = stats
        return result
    except (requests.RequestException, ValueError, KeyError, TypeError):
        return {}


def enrich_soccer_history(games, league_code, team_id):
    """Add observed metrics to history, keeping absent fields truly absent."""
    enriched=[]
    for game in games[:10]:
        item=dict(game)
        if game.get("id"):
            item["observed"] = historical_soccer_boxscore(league_code,game["id"]).get(str(team_id),{})
        enriched.append(item)
    return enriched


def fit_observed_metrics(params, home_games, away_games):
    """Shrink recent, venue-aware team boxscore averages toward baseline.

    Returns which metrics were genuinely fitted; do not label missing data as fitted.
    """
    evidence={}
    for metric, lower, upper in (("shots",1,35),("sot",0,20),
                                 ("corners",0,18),("yellow",0,10),("fouls",0,35)):
        evidence[metric]={}
        for side,games,at_home in (("home",home_games,True),("away",away_games,False)):
            values=[]
            for rank,game in enumerate(games[:10]):
                value=(game.get("observed") or {}).get(metric)
                if value is None:
                    continue
                # Time-decay and venue matching: same venue gets more weight.
                weight=(0.88**rank)*(1.35 if game.get("at_home")==at_home else 1.0)
                values.append((float(value),weight))
            evidence[metric][side]=len(values)
            if len(values)<3:
                continue
            total=sum(w for _,w in values)
            mean=sum(v*w for v,w in values)/total
            prior=params[f"{metric}_{side}"]
            # Empirical shrinkage reduces volatility in small samples.
            strength=total/(total+5.0)
            params[f"{metric}_{side}"]=max(lower,min(upper,strength*mean+(1-strength)*prior))
    params["stat_evidence"]=evidence
    # Historical shots on target as share of shots, where supported.
    for side in ("home","away"):
        if evidence["sot"][side]>=3 and evidence["shots"][side]>=3:
            params[f"sot_ratio_{side}"]=max(.08,min(.85,params[f"sot_{side}"]/max(1,params[f"shots_{side}"])))
    return params

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
        "sot_home":(7.5 + 3.5*lamh)*0.36,
        "sot_away":(7.5 + 3.5*lama)*0.36,
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


# Snapshots pre-partido: never overwrite a prediction with post-match information.
MODEL_VERSION = "nyuz-dixon-coles-2026-11"
DB_PATH = os.environ.get("NYUZ_DB_PATH", "simuladorny_predictions.sqlite3")

def snapshot_connection():
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.execute("""CREATE TABLE IF NOT EXISTS predictions (
        sport TEXT NOT NULL, league TEXT NOT NULL, event_id TEXT NOT NULL,
        created_utc TEXT NOT NULL, model_version TEXT NOT NULL,
        kickoff_utc TEXT NOT NULL, payload TEXT NOT NULL,
        PRIMARY KEY (sport, league, event_id)
    )""")
    return connection

def cloud_config():
    def secret(name):
        try:
            return str(st.secrets.get(name, "")).strip() or os.getenv(name, "").strip()
        except (FileNotFoundError, KeyError, AttributeError):
            return os.getenv(name, "").strip()
    return secret("SUPABASE_URL").rstrip("/"), secret("SUPABASE_SERVICE_ROLE_KEY")

def cloud_headers(key):
    return {"apikey": key, "Authorization": "Bearer " + key,
            "Content-Type": "application/json"}

def cloud_snapshot(sport, league, event_id):
    url, key = cloud_config()
    if not url or not key:
        return None
    try:
        response = requests.get(url + "/rest/v1/predictions", headers=cloud_headers(key),
            params={"select":"payload", "sport":"eq."+sport, "league":"eq."+league,
                    "event_id":"eq."+str(event_id), "limit":"1"}, timeout=8)
        response.raise_for_status()
        rows = response.json()
        return rows[0]["payload"] if rows else None
    except (requests.RequestException, ValueError, KeyError, IndexError):
        return None

def cloud_save(sport, league, event_id, now, kickoff, record):
    url, key = cloud_config()
    if not url or not key:
        return None
    try:
        response = requests.post(url + "/rest/v1/predictions",
            headers={**cloud_headers(key), "Prefer":"resolution=ignore-duplicates,return=minimal"},
            params={"on_conflict":"sport,league,event_id"},
            json={"sport":sport,"league":league,"event_id":str(event_id),
                  "created_utc":now,"kickoff_utc":kickoff,
                  "model_version":MODEL_VERSION,"payload":record}, timeout=10)
        response.raise_for_status()
        return True
    except requests.RequestException:
        return False

def get_snapshot(sport, league, event_id):
    url, key = cloud_config()
    if url and key:
        return cloud_snapshot(sport, league, event_id)
    try:
        with snapshot_connection() as db:
            row = db.execute(
                "SELECT payload FROM predictions WHERE sport=? AND league=? AND event_id=?",
                (sport, league, str(event_id))).fetchone()
        return json.loads(row[0]) if row else None
    except (sqlite3.Error, ValueError, OSError):
        return None

def save_prematch_snapshot(match, sport, league, projections, probabilities):
    """Save once, only before actual kickoff; completed games cannot backfill."""
    try:
        kickoff = datetime.fromisoformat(str(match["date"]).replace("Z", "+00:00"))
        now = datetime.now(ZoneInfo("UTC"))
        if match["state"] != "pre" or kickoff <= now:
            return False
        record = {
            "home": team_name(match["home"]), "away": team_name(match["away"]),
            "metrics": projections, "probabilities": probabilities,
            "kickoff": kickoff.isoformat(), "model_version": MODEL_VERSION
        }
        url, key = cloud_config()
        if url and key:
            return cloud_save(sport, league, match["id"], now.isoformat(),
                              kickoff.isoformat(), record)
        with snapshot_connection() as db:
            db.execute("""INSERT OR IGNORE INTO predictions
                (sport,league,event_id,created_utc,model_version,kickoff_utc,payload)
                VALUES (?,?,?,?,?,?,?)""",
                (sport,league,str(match["id"]),now.isoformat(),MODEL_VERSION,
                 kickoff.isoformat(),json.dumps(record,ensure_ascii=False)))
        return True
    except (ValueError, TypeError, sqlite3.Error, OSError):
        return False

def real_soccer_statistics(match, league):
    """Read real ESPN summary; unavailable metrics are left blank."""
    actual = {}
    home_id = str((match["home"].get("team") or {}).get("id") or "")
    away_id = str((match["away"].get("team") or {}).get("id") or "")
    actual["goals"] = [
        _num_stat(score_of(match["home"])), _num_stat(score_of(match["away"]))
    ]
    try:
        payload = sport_boxscore("soccer", league, match["id"])
        box = payload.get("boxscore") or {}
        for team in box.get("teams") or []:
            tid = str((team.get("team") or {}).get("id") or "")
            idx = 0 if tid == home_id else (1 if tid == away_id else None)
            if idx is None:
                continue
            for stat in team.get("statistics") or []:
                name = str(stat.get("name") or stat.get("abbreviation") or stat.get("label") or "").lower()
                name = "".join(c for c in name if c.isalnum())
                mapping = {
                    "totalshots":"shots", "shots":"shots", "totalshotsattempts":"shots",
                    "shotsontarget":"sot", "shotsongoal":"sot",
                    "cornerkicks":"corners", "corners":"corners",
                    "yellowcards":"yellow", "fouls":"fouls", "foulscommitted":"fouls"
                }
                key = mapping.get(name)
                if key:
                    val = _num_stat(stat.get("value", stat.get("displayValue")))
                    if val is not None:
                        actual.setdefault(key,[None,None])[idx] = val
    except (requests.RequestException, ValueError, TypeError, KeyError):
        pass
    return actual

def render_prediction_audit(match, league, snapshot):
    """Comparison in the SAME match, with no retroactive predictions."""
    st.markdown('<div class="sn-detail-box"><div class="sn-detail-heading">'
                'Predicción vs. Realidad</div>',unsafe_allow_html=True)
    if not snapshot:
        st.info("No hay una predicción guardada antes del inicio. "
                "No se puede evaluar este partido retroactivamente.")
        return
    actual = real_soccer_statistics(match, league)
    names = {"goals":"Goles", "shots":"Tiros", "sot":"Tiros a puerta",
             "corners":"Córners", "yellow":"Tarjetas amarillas", "fouls":"Faltas"}
    rows = []
    errors = []
    for key, title in names.items():
        predicted = snapshot.get("metrics",{}).get(key)
        observed = actual.get(key)
        if not isinstance(predicted,list) or len(predicted)!=2:
            continue
        for i, side in enumerate(("Local", "Visitante")):
            p = _num_stat(predicted[i])
            r = _num_stat(observed[i]) if observed and len(observed)>i else None
            if p is None:
                continue
            err = abs(p-r) if r is not None else None
            if err is not None:
                errors.append((title,side,err))
            rows.append('<tr><td>'+html.escape(title+' · '+side)+'</td><td>'
                        +f'{p:.1f}</td><td>'+('—' if r is None else f'{r:.1f}')
                        +'</td><td>'+('—' if err is None else f'{err:.1f}')+'</td></tr>')
    st.markdown('<div class="sn-audit-table"><table><thead><tr>'
                '<th>Estadística</th><th>Pred.</th><th>Real</th><th>Error</th>'
                '</tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>',
                unsafe_allow_html=True)
    if errors:
        worst = max(errors,key=lambda x:x[2])
        st.caption(f"Mayor diferencia absoluta: {worst[0]} · {worst[1]} ({worst[2]:.1f}). "
                   "Los errores de distintas estadísticas no son directamente comparables.")
    else:
        st.caption("Esperando estadísticas reales verificables del proveedor.")
    st.caption("Predicción original guardada antes del inicio · "
               +str(snapshot.get("model_version","")))

def record_upcoming_match(match, events, sport_path, league_code, cutoff):
    """Capture a prediction once when the fixture is listed, even if analysis stays closed.

    This runs on page visits, not as a continuously running scheduler.
    """
    if match.get("state") != "pre" or get_snapshot(sport_path,league_code,match["id"]):
        return False
    try:
        kickoff = datetime.fromisoformat(str(match["date"]).replace("Z", "+00:00"))
        if kickoff <= datetime.now(ZoneInfo("UTC")):
            return False
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
        if sport_path == "soccer":
            home_games = enrich_soccer_history(home_games, league_code, str(match["home"].get("team",{}).get("id") or ""))
            away_games = enrich_soccer_history(away_games, league_code, str(match["away"].get("team",{}).get("id") or ""))
            fit_observed_metrics(params, home_games, away_games)
        rho, fitted_matches = estimate_dixon_coles_rho(events, cutoff)
        params["dc_rho"] = rho
        seed = sum((i+1)*ord(ch) for i,ch in enumerate(str(match["id"])))
        result = run_monte_carlo(params, 10000, seed=seed)
        av = result["averages"]

        snapshot_metrics = {
            "goals": [params["lambda_home"], params["lambda_away"]],
            "shots": [av["shots_home"], av["shots_away"]],
            "sot": [av["sot_home"], av["sot_away"]],
            "corners": [av["corners_home"], av["corners_away"]],
            "yellow": [av["yellow_home"], av["yellow_away"]],
            "fouls": [av["fouls_home"], av["fouls_away"]],
        }
        snapshot_probabilities = {
            "home":result["home_win"],"draw":result["draw"],"away":result["away_win"]
        }
        if match["state"] == "pre":
            save_prematch_snapshot(match,sport_path,league_code,
                                  snapshot_metrics,snapshot_probabilities)
        return get_snapshot(sport_path,league_code,match["id"]) is not None
    except (ValueError, TypeError, KeyError, IndexError, ZeroDivisionError):
        return False

def render_monte_carlo_panel(match, events, sport_path, league_code, cutoff):
    """Panel premium: presentation only; preserves the original Monte Carlo model."""
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
    home_games = enrich_soccer_history(home_games, league_code, str(match["home"].get("team",{}).get("id") or ""))
    away_games = enrich_soccer_history(away_games, league_code, str(match["away"].get("team",{}).get("id") or ""))
    fit_observed_metrics(params, home_games, away_games)
    rho, fitted_matches = estimate_dixon_coles_rho(events, cutoff)
    params["dc_rho"] = rho
    seed = sum((i+1)*ord(ch) for i,ch in enumerate(str(match["id"])))
    result = run_monte_carlo(params, 10000, seed=seed)
    av = result["averages"]

    snapshot_metrics = {
        "goals": [params["lambda_home"], params["lambda_away"]],
        "shots": [av["shots_home"], av["shots_away"]],
        "sot": [av["sot_home"], av["sot_away"]],
        "corners": [av["corners_home"], av["corners_away"]],
        "yellow": [av["yellow_home"], av["yellow_away"]],
        "fouls": [av["fouls_home"], av["fouls_away"]],
    }
    snapshot_probabilities = {
        "home":result["home_win"],"draw":result["draw"],"away":result["away_win"]
    }
    if match["state"] == "pre":
        save_prematch_snapshot(match,sport_path,league_code,
                              snapshot_metrics,snapshot_probabilities)
    saved_snapshot = get_snapshot(sport_path,league_code,match["id"])

    # Match Intelligence: original layout adapted to actual match data.
    st.markdown('<div class="sn-mi-eyebrow">NYUZ · MATCH INTELLIGENCE</div>',unsafe_allow_html=True)
    st.markdown('<div class="sn-mi-heading">Análisis del partido</div>',unsafe_allow_html=True)
    st.markdown('<div class="sn-mi-subtitle">Proyecciones estadísticas · '+html.escape(str(cutoff))+'</div>',unsafe_allow_html=True)
    st.markdown('<div class="sn-mi-match">'+team_pair_html(match["home"],match["away"],"VS",large=True)+'</div>',unsafe_allow_html=True)

    probs = [(home_name,float(result["home_win"])),("Empate",float(result["draw"])),(away_name,float(result["away_win"]))]
    cards = "".join('<div class="sn-mi-prob"><span>'+html.escape(name)+'</span>'
                    +f'<strong>{value:.1f}%</strong><i><b style="width:{max(0,min(100,value)):.1f}%"></b></i></div>'
                    for name,value in probs)
    st.markdown('<div class="sn-mi-section">Probabilidades del modelo</div>'
                '<div class="sn-mi-probs">'+cards+'</div>',unsafe_allow_html=True)

    def form_symbols(games):
        symbols=[]
        for game in games[:5]:
            gf,ga=game.get("gf"),game.get("ga")
            if gf is None or ga is None:
                continue
            symbols.append("W" if gf>ga else ("D" if gf==ga else "L"))
        return symbols

    def form_html(name,games):
        symbols=form_symbols(games)
        pills=''.join('<span class="sn-mi-form sn-mi-form-'+sym.lower()+'">'+sym+'</span>' for sym in symbols)
        if not symbols:
            pills='<span class="sn-mi-form-none">Sin resultados verificados</span>'
        elif len(symbols)<5:
            pills += ''.join('<span class="sn-mi-form sn-mi-form-missing">—</span>' for _ in range(5-len(symbols)))
        return '<div class="sn-mi-form-team"><span>'+html.escape(name)+'</span><div class="sn-mi-form-pills">'+pills+'</div></div>'
    st.markdown('<div class="sn-mi-section">Forma reciente</div>'
                '<div class="sn-mi-form-grid">'+form_html(home_name,home_games)
                +form_html(away_name,away_games)+'</div>',unsafe_allow_html=True)
    if len(home_games)<5 or len(away_games)<5:
        st.caption(f"Historial verificado: {len(home_games)}/5 de {home_name} "
                   f"y {len(away_games)}/5 de {away_name}. Las casillas vacías no representan derrotas.")
        st.warning("Datos históricos incompletos: las probabilidades y proyecciones "
                   "dependen parcialmente de promedios generales. No deben "
                   "interpretarse como estimaciones personalizadas fiables.", icon="⚠️")

    evidence=params.get("stat_evidence",{})
    fitted=[]; limited=[]
    for label,key in (("Tiros","shots"),("Tiros a puerta","sot"),
                      ("Córners","corners"),("Tarjetas","yellow"),("Faltas","fouls")):
        count=evidence.get(key,{})
        if min(count.get("home",0),count.get("away",0))>=3:
            fitted.append(label)
        else:
            limited.append(label)
    if fitted:
        st.caption("Basadas parcialmente en estadísticas históricas verificadas: " + ", ".join(fitted) + ".")
    if limited:
        st.caption("Estimaciones con datos históricos insuficientes (utilizan valores base): " + ", ".join(limited) + ".")

    metrics=[
        ("Goles esperados",params["lambda_home"],params["lambda_away"]),
        ("Tiros",av["shots_home"],av["shots_away"]),
        ("Tiros a puerta",av["sot_home"],av["sot_away"]),
        ("Córners",av["corners_home"],av["corners_away"]),
        ("Tarjetas amarillas",av["yellow_home"],av["yellow_away"]),
        ("Faltas",av["fouls_home"],av["fouls_away"]),
    ]
    rows=[]
    for label,left,right in metrics:
        left,right=max(0,float(left)),max(0,float(right))
        maximum=max(left,right,0.01)*1.25
        rows.append('<div class="sn-mi-stat"><div class="sn-mi-stat-label">'
                    f'<strong>{left:.1f}</strong><span>{html.escape(label)}</span><strong>{right:.1f}</strong>'
                    '</div><div class="sn-mi-stat-pair"><div class="sn-mi-left">'
                    f'<i style="width:{left/maximum*100:.1f}%"></i></div>'
                    '<div class="sn-mi-right">'
                    f'<i style="width:{right/maximum*100:.1f}%"></i></div></div></div>')
    st.markdown('<div class="sn-mi-section">Estadísticas proyectadas</div>'
                '<div class="sn-mi-stat-wrap">'+''.join(rows)+'</div>',unsafe_allow_html=True)

    st.markdown('<div class="sn-mi-audit-title">▥ &nbsp; Predicción vs. Realidad</div>',unsafe_allow_html=True)
    if match["completed"]:
        render_prediction_audit(match,league_code,saved_snapshot)
    elif match["state"]=="in":
        st.caption("El partido está en curso. La comparación final aparecerá al terminar.")
    else:
        st.caption("Se activa al finalizar el partido, si existe una predicción guardada antes del inicio.")
    if match["state"]=="pre" and not saved_snapshot:
        st.caption("No se pudo guardar la predicción previa; revisa la configuración de almacenamiento.")
    st.caption("Modelo experimental · 10,000 simulaciones Monte Carlo. "
               "Los datos históricos observados se combinan con valores base cuando existen. "
               "Aún se requiere validación retrospectiva para demostrar mayor precisión.")


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



# NBA Intelligence: dynamic history only; no fixed season/team ratings or betting advice.
NBA_METRICS = {
    "rebounds": ("Rebotes", ["totalrebounds", "rebounds", "reb", "trb"]),
    "assists": ("Asistencias", ["assists", "ast"]),
    "threes": ("Triples anotados", ["threepointfieldgoalsmade", "threepointfieldgoals", "3pm"]),
    "turnovers": ("Pérdidas de balón", ["turnovers", "to"]),
}


def nba_team_observations(games, team_id):
    observations = {key: [] for key in NBA_METRICS}
    pace_observations = []
    for game in games[:10]:
        eid = game.get("id")
        if not eid:
            continue
        try:
            data = boxscore_team_metrics(sport_boxscore("basketball", "nba", str(eid)))
            stats = data.get(str(team_id), {})
        except (requests.RequestException, ValueError, KeyError, TypeError):
            continue
        for key, (_, aliases) in NBA_METRICS.items():
            value = get_stat(stats, aliases)
            if value is not None and 0 <= value < 200:
                observations[key].append(float(value))
        fga = get_stat(stats, ["fieldgoalattempts", "fga"])
        fta = get_stat(stats, ["freethrowattempts", "fta"])
        orb = get_stat(stats, ["offensiverebounds", "orb"])
        tov = get_stat(stats, ["turnovers", "to"])
        if all(x is not None for x in (fga, fta, orb, tov)):
            poss = fga + .44 * fta - orb + tov
            if 75 <= poss <= 125:
                pace_observations.append(poss)
    return observations, pace_observations


def nba_intelligence_prediction(home_games, away_games, home_obs, away_obs, seed):
    if len(home_games) < 3 or len(away_games) < 3:
        return None
    rng = random.Random(seed)
    def weighted_mean(games, field):
        recent = games[:10]
        weights = [1.0 / (1 + i * .17) for i in range(len(recent))]
        return sum(float(g[field]) * w for g, w in zip(recent, weights)) / sum(weights)
    # Score model is grounded in the actual recent points for/against.
    mu_h = .55 * weighted_mean(home_games, "gf") + .45 * weighted_mean(away_games, "ga")
    mu_a = .55 * weighted_mean(away_games, "gf") + .45 * weighted_mean(home_games, "ga")
    def std(games):
        values = [float(g["gf"]) for g in games[:10]]
        mean = sum(values) / len(values)
        return max(8.0, min(22.0, (sum((x - mean)**2 for x in values) / max(1, len(values)-1))**.5))
    sh, sa = std(home_games), std(away_games)
    # Shared game-tempo noise introduces positive correlation; residuals remain independent.
    common_sd = 3.5
    sums = [0.0, 0.0]
    home_wins = 0
    for _ in range(10000):
        common = rng.gauss(0, common_sd)
        h = max(0, round(rng.gauss(mu_h + common, max(1, (sh*sh-common_sd*common_sd)**.5))))
        a = max(0, round(rng.gauss(mu_a + common, max(1, (sa*sa-common_sd*common_sd)**.5))))
        if h == a:
            # Overtime approximation: break tie without claiming a calibrated OT model.
            if rng.random() < .5: h += 1
            else: a += 1
        sums[0] += h
        sums[1] += a
        home_wins += h > a
    metrics = {}
    for key in NBA_METRICS:
        values = [home_obs[0][key], away_obs[0][key]]
        metrics[key] = [sum(rng.choice(v) for _ in range(10000))/10000 if len(v) >= 3 else None for v in values]
    pace_values = home_obs[1] + away_obs[1]
    pace = sum(pace_values)/len(pace_values) if len(pace_values) >= 6 else None
    return {"home":sums[0]/10000, "away":sums[1]/10000,
            "total":sum(sums)/10000, "win_h":home_wins/100,
            "win_a":100-home_wins/100, "pace":pace, "metrics":metrics,
            "history_count":(len(home_games),len(away_games))}


def nba_audit_db():
    conn = sqlite3.connect("simuladorny_nba_audit.sqlite3", timeout=5)
    conn.execute("""CREATE TABLE IF NOT EXISTS nba_predictions (
        event_id TEXT PRIMARY KEY, kickoff TEXT NOT NULL, saved_at TEXT NOT NULL,
        payload TEXT NOT NULL)""")
    conn.commit()
    return conn


def nba_prediction_snapshot(match, prediction):
    # Never overwrite pre-game predictions, and never create a retroactive snapshot.
    event_id = str(match["id"])
    try:
        with nba_audit_db() as conn:
            row = conn.execute("SELECT payload FROM nba_predictions WHERE event_id=?", (event_id,)).fetchone()
            if row:
                return json.loads(row[0])
            if match["state"] != "pre":
                return None
            payload = {"home":prediction["home"], "away":prediction["away"],
                       "total":prediction["total"], "metrics":prediction["metrics"]}
            conn.execute("INSERT OR IGNORE INTO nba_predictions VALUES (?,?,?,?)",
                         (event_id, str(match.get("date") or "unknown"),
                          datetime.now(ZoneInfo("UTC")).isoformat(), json.dumps(payload)))
            conn.commit()
            return payload
    except (sqlite3.Error, ValueError, TypeError):
        return None


def render_nba_intelligence(match, events, cutoff):
    home_name, away_name = team_name(match["home"]), team_name(match["away"])
    home_games, away_games, _ = nba_history_for_match(match, events, cutoff)
    ids = [str(match[side].get("team", {}).get("id") or "") for side in ("home", "away")]
    if len(home_games) < 3 or len(away_games) < 3:
        st.info(f"Datos insuficientes para NBA: {home_name} ({len(home_games)} partidos), "
                f"{away_name} ({len(away_games)} partidos). No se inventan proyecciones. ESPN no devolvió suficiente historial; revisa la cobertura del proveedor.")
        return
    obs_h = nba_team_observations(home_games, ids[0])
    obs_a = nba_team_observations(away_games, ids[1])
    seed = sum((i+1)*ord(c) for i,c in enumerate(str(match["id"])))
    pred = nba_intelligence_prediction(home_games, away_games, obs_h, obs_a, seed)
    if pred is None: return
    st.markdown('<div class="sn-nba-wrap"><div class="sn-nba-eyebrow">NYUZ · NBA INTELLIGENCE</div>'
                '<div class="sn-nba-title">Análisis NBA</div>'
                '<div class="sn-nba-subtitle">10,000 simulaciones · Datos históricos disponibles</div></div>',
                unsafe_allow_html=True)
    st.markdown('<div class="sn-nba-teamline">'+team_pair_html(match["home"],match["away"],"VS",large=True)+'</div>',unsafe_allow_html=True)
    cards = ''.join('<div class="sn-nba-score"><div>'+html.escape(name)+'</div>'
                    +f'<strong>{val:.1f}</strong><span>Puntos proyectados</span></div>'
                    for name,val in ((home_name,pred["home"]),(away_name,pred["away"])))
    st.markdown('<div class="sn-nba-scores">'+cards+'</div>',unsafe_allow_html=True)
    items=[("Puntos totales",f'{pred["total"]:.1f}'),
           ("Posesiones estimadas", f'{pred["pace"]:.1f}' if pred["pace"] is not None else "No disponible")]
    for key,(label,_) in NBA_METRICS.items():
        left,right=pred["metrics"][key]
        items.append((label,f"{left:.1f} / {right:.1f}" if left is not None and right is not None else "Datos insuficientes"))
    rows=''.join('<div class="sn-nba-stat"><span>'+html.escape(label)+'</span><strong>'
                 +html.escape(value)+'</strong></div>' for label,value in items)
    st.markdown('<div class="sn-nba-section">Estadísticas proyectadas</div>'
                '<div class="sn-nba-stats">'+rows+'</div>',unsafe_allow_html=True)
    st.markdown('<div class="sn-nba-audit">▥ &nbsp; Predicción vs. Realidad'
                '<small>Evaluación al finalizar el partido</small></div>',unsafe_allow_html=True)
    snap = nba_prediction_snapshot(match, pred)
    if match.get("completed") and snap:
        # Real score is always sourced from the completed event; no invented boxscore.
        try:
            actual_h=float(score_of(match["home"]))
            actual_a=float(score_of(match["away"]))
            st.table({"Estadística":["Puntos local","Puntos visitante","Puntos totales"],
                      "Pronosticado":[round(snap["home"],1),round(snap["away"],1),round(snap["total"],1)],
                      "Real":[actual_h,actual_a,actual_h+actual_a],
                      "Error absoluto":[round(abs(snap["home"]-actual_h),1),
                                        round(abs(snap["away"]-actual_a),1),
                                        round(abs(snap["total"]-actual_h-actual_a),1)]})
        except (ValueError, TypeError):
            st.caption("Marcador final aún no disponible en la fuente.")
    elif match.get("completed"):
        st.caption("No hay una predicción guardada antes del partido para comparar.")
    elif match["state"] == "pre":
        st.caption("La comparación aparecerá al finalizar, si se guardó la predicción previa.")
    else:
        st.caption("Partido en curso. La comparación se activará al finalizar.")
    st.caption(f"Historial: {len(home_games)} partidos de {home_name} y {len(away_games)} de {away_name}. "
               "Las métricas sin al menos tres boxscores reales se ocultan. "
               "Modelo experimental, sin apuestas ni cuotas. SQLite local no es almacenamiento permanente en Streamlit Cloud.")

def render_other_sport_panel(match, events, sport_path, league_code, cutoff):
    if sport_path == "basketball":
        render_nba_intelligence(match, events, cutoff)
        return
    names = (team_name(match["home"]), team_name(match["away"]))
    st.markdown("<div class='sn-panel-head'><div class='sn-kicker'>NYUZ / PREDICTION ENGINE</div>"
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

def trend_score(match):
    """Editorial visibility heuristic, not actual audience or betting volume."""
    score = 100 if match["state"] == "in" else (30 if match["state"] == "pre" else 0)
    score += 15 if match.get("broadcast") else 0
    # Recognizable teams are a transparent heuristic, not measured popularity.
    famous = ("real madrid", "barcelona", "atletico", "atlético", "manchester",
              "liverpool", "arsenal", "chelsea", "bayern", "dortmund", "psg",
              "paris saint", "inter", "juventus", "milan", "américa", "america",
              "chivas", "guadalajara", "cruz azul", "tigres", "monterrey",
              "pumas", "boca juniors", "river plate")
    for team in (match["home"], match["away"]):
        if any(name in team_name(team).lower() for name in famous):
            score += 18
    return score

def render_match_card(match, sport_label, league_name, historical_data, sport_path, league_code, selected_date):
    home, away = match["home"], match["away"]
    hname, aname = team_name(home), team_name(away)
    hlogo, alogo = safe_logo(home), safe_logo(away)
    if match["state"] == "pre":
        shown = "VS"
    else:
        shown = f"{score_of(home)} : {score_of(away)}"
    st.markdown(
        '<div class="sn-fixture-card">'
        f'<div class="sn-fixture-meta">{html.escape(league_name)} · {html.escape(str(match["status"]))}</div>'
        + team_pair_html(home, away, shown)
        + '</div>', unsafe_allow_html=True
    )
    with st.expander("Ver análisis y predicciones", expanded=False):
        if sport_label == "⚽ Fútbol":
            render_monte_carlo_panel(
                match, historical_data, sport_path, league_code, selected_date)
        else:
            render_other_sport_panel(match, historical_data, sport_path, league_code, selected_date)

def run_scheduled_capture():
    """Call via python app.py --capture; suitable for GitHub Actions cron."""
    successes = 0
    today = local_today()
    # Scan major leagues; keep requests bounded and report failures.
    leagues = ["mex.1","eng.1","esp.1","ita.1","ger.1","fra.1",
               "usa.1","uefa.champions","por.1","bra.1","arg.1"]
    for league in leagues:
        for day in (today, today + timedelta(days=1)):
            try:
                fixtures = get_events("soccer", league, day)
                upcoming = [m for m in (parse_event(e) for e in fixtures)
                            if m and m["state"] == "pre"]
                if not upcoming:
                    continue
                historical = historical_events("soccer", league, day)
                for match in upcoming:
                    if record_upcoming_match(match, historical, "soccer", league, day):
                        successes += 1
            except (requests.RequestException, ValueError, KeyError) as exc:
                print(f"Capture warning {league} {day}: {exc}")
    print(f"Snapshots registered or already present: {successes}")

if __name__ == "__main__" and "--capture" in __import__("sys").argv:
    run_scheduled_capture()
    raise SystemExit(0)

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

/* NYUZ / OBSIDIAN: premium compact mobile-first presentation */
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

/* NYUZ MINIMAL / MOBILE-FIRST */
.stApp{background:#0b0c0e!important}
.block-container{max-width:960px!important;padding-top:10px!important}
[data-testid="stVerticalBlock"]{gap:.43rem!important}
.sn-header{padding:3px 0 6px!important;margin:0!important}
.sn-logo{width:36px!important;height:36px!important;border-radius:11px!important;font-size:22px!important}
.sn-wordmark{font-size:clamp(19px,5vw,25px)!important;letter-spacing:-.9px!important}
.sn-brand-sub{font-size:8px!important;letter-spacing:2px!important}
.sn-header-tag{display:none!important}
.sn-list-heading{font-size:clamp(23px,6vw,29px)!important;margin:5px 0 7px!important;letter-spacing:-.9px!important}
.sn-list-heading span{display:none!important}
.sn-date-title,.sn-section-label{font-size:10px!important;letter-spacing:1.3px!important;margin:8px 0 3px!important;color:#a5a9ae!important}
[data-testid="stRadio"]>div[role="radiogroup"]{gap:5px!important;padding:1px 0 5px!important}
[data-testid="stRadio"]>div[role="radiogroup"] label{padding:8px 11px!important;border-radius:11px!important;min-height:38px!important;background:#1b1d20!important;border:1px solid #30343a!important;box-shadow:none!important}
[data-testid="stRadio"]>div[role="radiogroup"] label:has(input:checked){background:#f0f0f0!important;border-color:#f0f0f0!important}
[data-testid="stRadio"]>div[role="radiogroup"] label:has(input:checked) *{color:#101113!important}
[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p{font-size:12px!important;font-weight:650!important}
/* Radio dots are unnecessary in segmented controls. */
[data-testid="stRadio"] label [data-testid="stWidgetLabel"]{display:none!important}
[data-testid="stRadio"] label>div:first-child:has(input[type="radio"]){position:absolute!important;opacity:0!important;width:0!important;height:0!important;overflow:hidden!important}
[data-testid="stRadio"] label{position:relative!important}
/* Date strip is horizontal, scrollable, and touch-friendly. */
[data-testid="stRadio"] [role="radiogroup"]{display:flex!important;flex-direction:row!important;flex-wrap:nowrap!important;overflow-x:auto!important;-webkit-overflow-scrolling:touch;scrollbar-width:none}
[data-testid="stRadio"] [role="radiogroup"]>label{flex:0 0 auto!important;min-width:max-content!important}
[data-testid="stTextInput"] input{min-height:42px!important;border-radius:12px!important}
[data-testid="stPopover"] button{min-height:35px!important;border-radius:10px!important;background:#1b1d20!important;border-color:#373a40!important;font-size:12px!important}
[data-testid="stExpander"]{border-radius:12px!important}
.sn-section-title{margin:8px 0!important;font-size:17px!important}
.sn-competition{margin:4px 0!important}
[data-testid="stCaptionContainer"]{margin:0!important}
@media(max-width:500px){.block-container{padding:9px 13px 65px!important}.sn-header{margin-bottom:2px!important}.sn-list-heading{margin-top:3px!important}}

/* NYUZ STUDIO — true minimal navigation, no radio controls */
.stApp {background:#0b0c0e!important;}
.block-container {max-width:900px!important;padding-top:7px!important;}
.sn-header {padding:0 0 4px!important;}
.sn-logo {width:32px!important;height:32px!important;border-radius:9px!important;}
.sn-wordmark {font-size:20px!important;letter-spacing:-.65px!important;}
.sn-brand-sub {font-size:8px!important;letter-spacing:1.4px!important;}
.sn-list-heading {font-size:23px!important;margin:0 0 4px!important;}
[data-testid="stVerticalBlock"] {gap:.30rem!important;}
[data-testid="stPills"] [role="group"] {
  display:flex!important;flex-wrap:nowrap!important;overflow-x:auto!important;
  overflow-y:hidden!important;gap:6px!important;padding:3px 0 7px!important;
  scrollbar-width:none!important;-webkit-overflow-scrolling:touch!important;
}
[data-testid="stPills"] [role="group"]::-webkit-scrollbar {display:none!important;}
[data-testid="stPills"] button {
  flex:0 0 auto!important;white-space:nowrap!important;min-height:36px!important;
  padding:7px 12px!important;border-radius:10px!important;
  background:#202226!important;border:1px solid #34373c!important;
  color:#d2d4d7!important;box-shadow:none!important;font-size:12px!important;
}
[data-testid="stPills"] button[aria-pressed="true"] {
  background:#f0f0f0!important;color:#121314!important;
  border-color:#f0f0f0!important;font-weight:750!important;
}
[data-testid="stPills"] button[aria-selected="true"] {
  background:#f0f0f0!important;color:#121314!important;border-color:#f0f0f0!important;
}
[data-testid="stPills"] [data-testid="stWidgetLabel"] {display:none!important;}
[data-testid="stTextInput"] input {min-height:39px!important;}
[data-testid="stPopover"] button {min-height:34px!important;}
[data-testid="stExpander"] {margin:0 0 5px!important;}
[data-testid="stCaptionContainer"] p {font-size:11px!important;color:#9da1a8!important;}
@media(max-width:600px) {
 .block-container {padding:7px 13px 70px!important;}
 [data-testid="stPills"] button {min-height:35px!important;padding:7px 11px!important;}
}


/* STUDIO REFINEMENT: airy header, single-row date rail, compact fixtures */
.sn-header{padding:10px 0 19px!important;margin-bottom:3px!important}
.sn-list-heading{margin:6px 0 11px!important;font-size:25px!important}
[data-testid="stPills"]{width:100%!important;min-width:0!important;overflow:hidden!important}
[data-testid="stPills"] > div{max-width:100%!important;min-width:0!important}
[data-testid="stPills"] [role="group"]{
  width:100%!important;max-width:100%!important;min-width:0!important;
  display:flex!important;flex-flow:row nowrap!important;
  justify-content:flex-start!important;align-items:center!important;
  overflow-x:auto!important;overflow-y:hidden!important;
  overscroll-behavior-x:contain!important;scrollbar-width:none!important;
  -webkit-overflow-scrolling:touch!important;
}
[data-testid="stPills"] [role="group"] > *{flex:0 0 auto!important}
[data-testid="stPills"] [role="group"]::-webkit-scrollbar{display:none!important}
[data-testid="stPills"] button{
  border-radius:9px!important;border:1px solid #35383d!important;
  color:#d5d6d8!important;background:#1e2023!important;
  padding:9px 13px!important;font-weight:500!important;
}
[data-testid="stPills"] button[aria-pressed="true"],
[data-testid="stPills"] button[aria-selected="true"],
[data-testid="stPills"] button[data-selected="true"]{
  color:#111214!important;background:#f3f3f3!important;
  border:1px solid #f3f3f3!important;box-shadow:none!important;
}
[data-testid="stPills"] button:focus-visible{outline:2px solid #aaa!important;outline-offset:2px}
[data-testid="stPills"] button:focus:not(:focus-visible){outline:none!important;box-shadow:none!important}
.sn-fixture-card{
  background:#151618;border:1px solid #34363a;border-radius:15px;
  padding:13px 14px 5px;margin:12px 0 3px;
}
.sn-fixture-meta{font-size:11px;color:#a6a9ae;letter-spacing:.15px}
.sn-fixture-card .sn-teams{padding:7px 0 9px!important;min-height:76px!important}
.sn-fixture-card .sn-side{gap:4px!important;font-size:13px!important}
.sn-fixture-card .sn-side img{width:40px!important;height:40px!important;filter:none!important}
.sn-fixture-card .sn-center{font-size:20px!important}
[data-testid="stExpander"]{border-radius:12px!important}
[data-testid="stExpander"] summary{padding:10px 14px!important}
[data-testid="stTextInput"]{margin-top:10px!important}
@media(max-width:600px){
  .block-container{padding:12px 15px 70px!important}
  .sn-header{padding:9px 0 20px!important}
  [data-testid="stPills"] [role="group"]{flex-wrap:nowrap!important}
  .sn-fixture-card{margin-top:9px!important}
}

/* NYUZ SIGNATURE — rounded, monochrome, breathable controls */
.sn-header{padding:13px 0 24px!important}
.sn-logo{border-radius:50%!important;width:39px!important;height:39px!important}
.sn-list-heading{margin:9px 0 16px!important}
[data-testid="stPills"]{width:100%!important;min-width:0!important;overflow:hidden!important}
[data-testid="stPills"] div[data-baseweb="button-group"],
[data-testid="stPills"] div[role="group"],
[data-testid="stPills"] div[role="radiogroup"],
[data-testid="stPills"] div:has(> button){
  display:flex!important;flex-direction:row!important;flex-wrap:nowrap!important;
  align-items:center!important;justify-content:flex-start!important;
  gap:8px!important;min-width:0!important;max-width:100%!important;
  overflow-x:auto!important;overflow-y:hidden!important;
  scrollbar-width:none!important;-webkit-overflow-scrolling:touch!important;
}
[data-testid="stPills"] div:has(> button)::-webkit-scrollbar{display:none!important}
[data-testid="stPills"] button{
  flex:0 0 auto!important;white-space:nowrap!important;
  border-radius:999px!important;background:#1b1c1f!important;
  border:1px solid #44464a!important;color:#dedfe1!important;
  min-height:38px!important;padding:9px 15px!important;
  box-shadow:none!important;
}
[data-testid="stPills"] button[aria-pressed="true"],
[data-testid="stPills"] button[aria-selected="true"],
[data-testid="stPills"] button[data-selected="true"],
[data-testid="stPills"] button[kind="primary"]{
  background:#f2f2f2!important;border-color:#f2f2f2!important;
  color:#111214!important;box-shadow:none!important;
}
[data-testid="stPills"] button:focus:not(:focus-visible){outline:none!important;box-shadow:none!important}
[data-testid="stPills"] button:hover{border-color:#8c8e92!important}
[data-testid="stPopover"] button,
[data-testid="stExpander"],[data-testid="stTextInput"] input{
  border-radius:22px!important;
}
[data-testid="stExpander"] summary{border-radius:22px!important}
.sn-fixture-card{
  border-radius:25px!important;background:#151618!important;
  border:1px solid #3a3b3f!important;padding:14px 16px 7px!important;
  margin:14px 0 0!important;
}
.sn-fixture-card .sn-teams{padding:8px 0 11px!important;min-height:76px!important}
[data-testid="stExpander"]{margin-top:5px!important;margin-bottom:17px!important}
[data-testid="stVerticalBlock"]{gap:.55rem!important}
@media(max-width:600px){
  .block-container{padding:15px 16px 85px!important}
  .sn-header{padding:10px 0 23px!important}
  [data-testid="stPills"] button{padding:8px 13px!important}
}

/* Definitive one-row calendar: ordinary HTML links, not Streamlit pills. */
.sn-date-caption{font-size:10px;letter-spacing:2px;color:#aeb0b4;font-weight:750;margin:15px 0 9px}
.sn-date-rail{display:flex!important;flex-flow:row nowrap!important;gap:9px!important;
  width:100%!important;max-width:100%!important;overflow-x:auto!important;
  overflow-y:hidden!important;scrollbar-width:none!important;-webkit-overflow-scrolling:touch!important;
  padding:5px 0 14px!important;overscroll-behavior-x:contain}
.sn-date-rail::-webkit-scrollbar{display:none}
.sn-date-rail .sn-day{display:flex!important;flex:0 0 65px!important;min-width:65px!important;
  flex-direction:column!important;justify-content:center!important;align-items:center!important;
  gap:3px!important;padding:10px 4px!important;border-radius:21px!important;
  border:1px solid #3b3d40!important;background:#1c1d20!important;color:#b8bbc0!important;
  text-decoration:none!important;box-sizing:border-box!important}
.sn-date-rail .sn-day strong{font-size:20px;line-height:1.2;color:#f3f3f3}
.sn-date-rail .sn-day span{font-size:11px;line-height:1.2}
.sn-date-rail .sn-day.selected{background:#f2f2f2!important;border-color:#f2f2f2!important;color:#141414!important}
.sn-date-rail .sn-day.selected strong{color:#141414!important}
.sn-date-rail .sn-day:focus-visible{outline:2px solid #fff;outline-offset:2px}
[data-testid="stPills"] button[aria-checked="true"],
[data-testid="stPills"] button[aria-pressed="true"],
[data-testid="stPills"] button[aria-selected="true"],
[data-testid="stPills"] button[data-state="active"]{
 background:#f2f2f2!important;color:#111!important;border-color:#f2f2f2!important;
}
[data-testid="stPills"] button{border-radius:999px!important}

/* Premium prediction detail, matched to the user-selected monochrome reference */
.sn-detail-title{font-size:22px;font-weight:800;letter-spacing:-.7px;margin:12px 0 3px}
.sn-detail-sub{font-size:11px;color:#a6a9ae;margin-bottom:12px}
.sn-detail-match,.sn-detail-box,.sn-detail-tile{
  background:linear-gradient(145deg,#191a1d,#111214);
  border:1px solid #383a3e;border-radius:24px;
}
.sn-detail-match{padding:10px 12px;margin:8px 0 12px}
.sn-detail-match .sn-teams{padding:9px 0!important}
.sn-detail-tabs{display:flex;gap:7px;overflow-x:auto;white-space:nowrap;
  scrollbar-width:none;margin:12px 0}
.sn-detail-tabs span{padding:9px 13px;background:#222326;border:1px solid #424448;
  border-radius:999px;font-size:11px;color:#ddd}
.sn-detail-tabs span.active{background:#f1f1f1;color:#111;border-color:#f1f1f1;font-weight:700}
.sn-detail-box{padding:17px 14px;margin:12px 0}
.sn-detail-heading{font-weight:800;font-size:16px;letter-spacing:-.3px;margin-bottom:17px}
.sn-detail-probs{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px}
.sn-detail-prob{display:flex;flex-direction:column;align-items:center;gap:8px;min-width:0}
.sn-detail-prob span{font-size:11px;color:#c6c8ca;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.sn-detail-prob strong{font-size:22px}
.sn-detail-prob i{width:100%;height:7px;border-radius:9px;background:#44464b;overflow:hidden}
.sn-detail-prob i b{display:block;height:100%;background:#f0f0f0;border-radius:9px}
.sn-detail-two{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:12px 0}
.sn-detail-tile{padding:14px 10px;display:flex;flex-direction:column;align-items:center;
  text-align:center;justify-content:center;gap:10px;min-height:125px}
.sn-detail-tile span{font-size:12px;font-weight:700}
.sn-detail-tile strong{font-size:27px}
.sn-detail-tile strong.sn-detail-winner{font-size:17px;overflow-wrap:anywhere}
.sn-detail-tile small{font-size:10px;color:#b5b7ba;line-height:1.4}
.sn-detail-odds{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}
.sn-detail-odd{background:#26272a;border-radius:14px;border:1px solid #424448;
  padding:12px 3px;display:flex;flex-direction:column;align-items:center;gap:7px}
.sn-detail-odd span{font-size:10px;color:#c4c5c8;white-space:nowrap;overflow:hidden;
  text-overflow:ellipsis;max-width:100%}
.sn-detail-odd strong{font-size:20px}
.sn-detail-foot{color:#999da3;font-size:10px;margin-top:12px}
.sn-detail-statnames{display:flex;justify-content:space-between;color:#b6b8bb;font-size:11px;margin-bottom:13px}
.sn-detail-statnames span{color:#75787d}
.sn-detail-stat{margin:13px 0}
.sn-detail-stat-label{display:flex;justify-content:space-between;gap:8px;align-items:center}
.sn-detail-stat-label strong{font-size:14px;min-width:36px}
.sn-detail-stat-label strong:last-child{text-align:right}
.sn-detail-stat-label span{font-size:12px;color:#d2d4d6;text-align:center}
.sn-detail-bars{display:flex;gap:4px;height:7px;margin-top:7px}
.sn-detail-bars i,.sn-detail-bars b{display:block;border-radius:9px;background:#6e7176}
.sn-detail-bars b{background:#ededee}

.sn-score-options{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}
.sn-score-option{display:flex;flex-direction:column;align-items:center;gap:7px;
 padding:13px 5px;border:1px solid #424449;border-radius:17px;background:#242528}
.sn-score-option strong{font-size:19px;color:#f4f4f4}
.sn-score-option span{font-size:12px;color:#bfc1c5}

.sn-audit-table{overflow-x:auto;width:100%;border-radius:14px;border:1px solid #34363a}
.sn-audit-table table{border-collapse:collapse;width:100%;font-size:11px;color:#f1f1f1}
.sn-audit-table th,.sn-audit-table td{padding:11px 8px;border-bottom:1px solid #34363a;text-align:right;white-space:nowrap}
.sn-audit-table th:first-child,.sn-audit-table td:first-child{text-align:left}
.sn-audit-table th{background:#242528;color:#bfc0c3;font-weight:600}
.sn-pick-muted{background:#1e2024;border:1px solid #3a3d43;border-radius:18px;padding:15px 17px;display:flex;flex-direction:column;gap:6px;margin:12px 0}
.sn-pick-muted strong{color:#f2f3f5;font-size:14px}
.sn-pick-muted span{color:#b6bac1;font-size:12px;line-height:1.5}

/* Match Intelligence — compact premium dark design */
.sn-mi-eyebrow{font-size:10px;font-weight:800;letter-spacing:2px;color:#aaaeb6;margin:16px 0 8px}
.sn-mi-heading{font-size:23px;font-weight:800;color:#f6f6f7}
.sn-mi-subtitle{font-size:12px;color:#9b9da2;margin:4px 0 14px}
.sn-mi-match{border:1px solid #393b40;border-radius:20px;padding:15px 10px;background:#17181b;margin:12px 0 18px}
.sn-mi-section{font-size:15px;font-weight:750;color:#f3f3f4;margin:21px 0 11px}
.sn-mi-probs{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}
.sn-mi-prob{min-width:0;border-radius:14px;background:#222328;padding:14px 7px;display:flex;align-items:center;flex-direction:column;gap:12px}
.sn-mi-prob span{color:#b8bac0;font-size:11px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%}
.sn-mi-prob strong{font-size:22px;color:#f5f5f6}
.sn-mi-prob i{height:5px;width:100%;background:#42444a;border-radius:6px;overflow:hidden}
.sn-mi-prob b{display:block;height:100%;background:#f1f1f1;border-radius:6px}
.sn-mi-form-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.sn-mi-form-team{min-width:0}.sn-mi-form-team>span{font-size:12px;color:#b6b8bd}
.sn-mi-form-pills{display:flex;gap:4px;margin-top:10px}
.sn-mi-form{flex:1;text-align:center;padding:7px 0;border-radius:7px;font-weight:750;font-size:11px;color:#f4f4f4}
.sn-mi-form-w{background:#315c4b}.sn-mi-form-d{background:#5a5140}.sn-mi-form-l{background:#633b40}
.sn-mi-form-none{color:#92959a;font-size:11px}.sn-mi-form-missing{background:#35363b;color:#8b8d92}
.sn-mi-stat-wrap{border-radius:18px;background:#17181b;padding:14px 12px;border:1px solid #33353a}
.sn-mi-stat{margin:10px 0 17px}.sn-mi-stat:last-child{margin-bottom:5px}
.sn-mi-stat-label{display:grid;grid-template-columns:1fr 2fr 1fr;gap:4px;align-items:center;margin-bottom:8px}
.sn-mi-stat-label strong{font-size:13px;color:#f5f5f5}.sn-mi-stat-label strong:last-child{text-align:right}
.sn-mi-stat-label span{font-size:11px;color:#b8bac0;text-align:center}
.sn-mi-stat-pair{display:grid;grid-template-columns:1fr 1fr;gap:7px}
.sn-mi-stat-pair>div{height:7px}.sn-mi-stat-pair i{display:block;height:7px;border-radius:5px}
.sn-mi-left{display:flex;justify-content:flex-end}.sn-mi-left i{background:#d5d5d5}
.sn-mi-right i{background:#777a80}
.sn-mi-audit-title{font-size:15px;font-weight:750;padding:16px 0 6px;border-top:1px solid #393b40;margin-top:20px}
@media(max-width:420px){.sn-mi-prob strong{font-size:19px}.sn-mi-prob{padding:12px 5px}.sn-mi-prob span{font-size:10px}}

/* NBA Intelligence: screenshot-matched minimalist mobile panel */
.sn-nba-wrap{margin:14px 0 20px}.sn-nba-eyebrow{font-size:12px;font-weight:750;letter-spacing:1.5px;color:#b7b8be}
.sn-nba-title{font-size:27px;font-weight:800;color:#fff;margin:16px 0 13px}
.sn-nba-subtitle{color:#a4a5ac;font-size:14px;padding-bottom:20px;border-bottom:1px solid #393a40}
.sn-nba-teamline{margin:12px 0 18px}.sn-nba-scores{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin:18px 0 24px}
.sn-nba-score{background:#25262b;border-radius:18px;padding:17px 13px;min-width:0;display:flex;flex-direction:column;gap:7px}
.sn-nba-score>div{color:#b5b6bb;font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.sn-nba-score strong{color:#fff;font-size:35px;font-weight:800;letter-spacing:-1px}
.sn-nba-score span{color:#b0b1b8;font-size:11px}
.sn-nba-section{font-size:18px;font-weight:800;color:#fff;margin:24px 0 16px}
.sn-nba-stats{display:flex;flex-direction:column;gap:19px;margin-bottom:24px}
.sn-nba-stat{display:flex;align-items:baseline;justify-content:space-between;gap:10px}
.sn-nba-stat span{color:#b2b3bb;font-size:14px}.sn-nba-stat strong{color:#fff;font-size:17px;white-space:nowrap}
.sn-nba-audit{border-top:1px solid #393a40;padding-top:23px;font-size:18px;font-weight:800;color:#fff;margin-top:18px}
.sn-nba-audit small{display:block;color:#a9abb2;font-size:13px;font-weight:400;margin:7px 0 16px}
@media(max-width:420px){.sn-nba-score strong{font-size:30px}.sn-nba-stat span{font-size:12px}.sn-nba-stat strong{font-size:15px}}

/* NYUZ Signature — monochrome mobile-first redesign */
.stApp{background:#08090b!important;color:#f6f6f7!important}
.block-container{max-width:790px!important;padding:25px 18px 120px!important}
.ny-brand{display:flex;align-items:center;gap:12px;margin:10px 0 23px}
.ny-monogram{font-size:39px;font-weight:950;letter-spacing:-6px;transform:skew(-13deg);background:linear-gradient(145deg,#fff,#85888e);color:transparent;background-clip:text;line-height:1}
.ny-brand-name{font-size:35px;font-weight:850;letter-spacing:-1.8px;line-height:.91}
.ny-brand-name small{display:block;font-size:8px;letter-spacing:3px;color:#b9bac0;margin-top:10px;font-weight:750}
.ny-header-actions{margin-left:auto;display:flex;gap:10px}.ny-header-actions span{width:42px;height:42px;border:1px solid #303136;border-radius:13px;background:#17181b;display:grid;place-items:center;font-size:24px}
.ny-hero{border:1px solid #33353a;background:radial-gradient(ellipse at 95% 60%,#34363b 0%,#16171a 40%,#0c0d0f 75%);border-radius:24px;min-height:202px;display:flex;align-items:center;justify-content:space-between;overflow:hidden;padding:24px 23px;margin:0 0 22px;position:relative}
.ny-hero-copy{position:relative;z-index:1}.ny-hero h1{font-size:clamp(29px,6.8vw,42px);font-weight:850;line-height:1.04;letter-spacing:-1.5px;margin:0 0 12px}.ny-hero p{color:#b7b7bc;font-size:15px;line-height:1.45;margin:0}
.ny-hero-art{position:absolute;right:-30px;bottom:-35px;font-size:210px;font-weight:950;font-style:italic;letter-spacing:-25px;line-height:1;color:#65686f;opacity:.33;text-shadow:-14px -12px 35px #fff3;transform:rotate(-13deg)}
.ny-lab-heading{border:1px solid #393a40;background:linear-gradient(135deg,#242529,#161719);padding:18px 17px;border-radius:19px;margin:15px 0 6px;font-size:21px;line-height:1.15}
.ny-lab-heading small{display:block;font-size:13px;color:#adaeb3;margin:6px 0 0 32px}
.ny-section-heading{font-size:clamp(28px,7vw,36px);font-weight:850;letter-spacing:-1.2px;margin:27px 0 12px}
[data-testid="stPills"] button{font-size:15px!important;min-height:47px!important;border-radius:16px!important;padding:9px 14px!important;background:#17181b!important;border:1px solid #393a3f!important;color:#f2f2f3!important}
[data-testid="stPills"] button[aria-selected="true"]{background:#f4f4f5!important;color:#111214!important;border-color:#f4f4f5!important}
[data-testid="stExpander"]{border-radius:20px!important;background:#17181b!important}
[data-testid="stExpander"] summary{font-size:16px!important;min-height:52px!important}
.sn-fixture-card{border-radius:21px!important;background:linear-gradient(155deg,#1c1d20,#111214)!important;padding:17px 14px!important;margin-top:17px!important}
.sn-fixture-meta{font-size:13px!important;color:#aeb0b6!important}
.sn-fixture-card .sn-side{font-size:16px!important;font-weight:800!important}
.sn-fixture-card .sn-side img{width:51px!important;height:51px!important}
.sn-fixture-card .sn-teams{min-height:95px!important}
.sn-fixture-card .sn-center{font-size:19px!important;background:#292a2e;border-radius:100px;padding:7px 10px}
.sn-date-rail{margin-bottom:14px!important}
.sn-day{min-width:56px!important}
[data-testid="stCaptionContainer"] p{font-size:12px!important}
.ny-bottom-nav{display:flex;justify-content:space-around;gap:7px;background:linear-gradient(180deg,#191a1d,#101113);border:1px solid #303136;border-radius:26px;padding:15px 5px 13px;margin-top:38px}
.ny-bottom-nav .nav-item{flex:1;text-align:center;color:#aeb0b7;font-size:12px;font-weight:650;text-decoration:none;display:flex;align-items:center;flex-direction:column;gap:8px}
.ny-bottom-nav .nav-item strong{font-size:23px;font-weight:650;line-height:1;color:#f5f5f6}
.ny-bottom-nav .nav-item.active{color:#fff}
.ny-bottom-nav .nav-item.active strong{filter:drop-shadow(0 0 6px #fff5)}
@media(max-width:420px){.ny-hero{min-height:184px;padding:20px 17px}.ny-hero h1{font-size:31px}.ny-hero-art{font-size:170px;right:-27px}.ny-brand-name{font-size:31px}.ny-brand-name small{font-size:7px}.sn-fixture-card .sn-side{font-size:14px!important}}

</style>

""",unsafe_allow_html=True)

st.markdown("""
<div class="ny-brand" id="ny-inicio"><div class="ny-monogram">N</div><div class="ny-brand-name">NYUZ<small>SPORTS INTELLIGENCE</small></div>
<div class="ny-header-actions"><span>⌕</span><span>♧</span></div></div>
<div class="ny-hero"><div class="ny-hero-copy"><h1>Análisis y<br>predicciones<br>deportivas</h1><p>Simulaciones, estadísticas y<br>backtesting avanzado.</p></div><div class="ny-hero-art">N</div></div>
""",unsafe_allow_html=True)

# Sports selection moved above match status, visually matching reference.
sport_label = st.pills("Deporte", list(SPORTS.keys()), selection_mode="single", default="⚽ Fútbol", label_visibility="collapsed", key="sport_tabs") or "⚽ Fútbol"
sport = SPORTS[sport_label]

st.markdown('<div class="ny-lab-heading" id="ny-lab">♧ &nbsp; <b>Model Lab</b><small>Backtesting y evaluación de modelos</small></div>',unsafe_allow_html=True)
with st.expander("🧪 Nyuz Model Lab · Backtesting NBA", expanded=(st.query_params.get("sn_view") == "lab")):
    st.caption("Prueba retrospectiva: solo utiliza partidos anteriores a cada encuentro. "
               "Compara un promedio simple contra un modelo que pondera la forma reciente. "
               "Este laboratorio no modifica automáticamente el motor en producción.")
    if st.button("Evaluar últimos 60 partidos NBA", key="nyuz_backtest"):
        with st.spinner("Recuperando historial y evaluando partidos NBA..."):
            historical = nba_recent_scoreboards(selected_date + timedelta(days=1))
            rows = backtest_nba_history(historical, 60)
        if len(rows) < 15:
            st.warning(f"Solo se pudieron evaluar {len(rows)} partidos con al menos cinco "
                       "antecedentes por equipo. Se necesitan más datos para comparar modelos.")
        else:
            split = max(1, int(len(rows)*.8))
            validation, test = rows[:split], rows[split:]
            def mae(items, prefix):
                return sum(abs(r[f"{prefix}_home"]-r["actual_home"])+
                           abs(r[f"{prefix}_away"]-r["actual_away"]) for r in items)/(2*len(items))
            st.metric("Partidos evaluados", len(rows))
            st.caption(f"Validación: {len(validation)} partidos anteriores · "
                       f"Prueba final: {len(test)} partidos posteriores.")
            st.markdown("**Error absoluto medio por equipo (puntos; menor es mejor)**")
            st.table([
                {"Modelo":"Promedio simple", "Validación":round(mae(validation,"base"),2),
                 "Prueba final":round(mae(test,"base"),2)},
                {"Modelo":"Forma reciente ponderada", "Validación":round(mae(validation,"candidate"),2),
                 "Prueba final":round(mae(test,"candidate"),2)}
            ])
            st.caption("Evaluación preliminar de proyección de puntos, no de rebotes, "
                       "asistencias o triples. El backtesting utiliza medias analíticas "
                       "equivalentes a la expectativa de una simulación Monte Carlo, "
                       "sin ejecutar 10,000 muestras por partido. "
                       "No se ha optimizado ni calibrado el modelo con estos resultados.")
            st.dataframe([{"Fecha":r["date"],"Partido":r["match"],
                           "Real":f'{r["actual_home"]:.0f} - {r["actual_away"]:.0f}',
                           "Base":f'{r["base_home"]:.1f} - {r["base_away"]:.1f}',
                           "Ponderado":f'{r["candidate_home"]:.1f} - {r["candidate_away"]:.1f}'}
                          for r in reversed(test)], hide_index=True, use_container_width=True)

st.markdown('<div class="ny-section-heading" id="ny-partidos">Partidos de hoy</div>',unsafe_allow_html=True)
status_filter = st.pills(
    "Estado", ["Todos", "En vivo", "Próximos", "Finalizados"],
    selection_mode="single", default="Todos",
    label_visibility="collapsed", key="status_tabs",
) or "Todos"
# Navegación real por enlaces: una sola fila desplazable incluso en iPhone.
# Los enlaces actualizan la fecha mediante query params, sin depender de st.pills.
if "sn_selected_date" not in st.session_state:
    st.session_state.sn_selected_date = local_today()
incoming = st.query_params.get("sn_date")
if incoming:
    try:
        requested = date.fromisoformat(str(incoming))
        if abs((requested - local_today()).days) <= 3650:
            st.session_state.sn_selected_date = requested
    except (TypeError, ValueError):
        pass
selected_date = st.session_state.sn_selected_date
short_days = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
week_days = [selected_date + timedelta(days=i) for i in range(-3, 4)]
st.markdown('<div class="sn-date-caption">SELECCIONA UNA FECHA</div>', unsafe_allow_html=True)
with st.popover("▦  Elegir fecha", use_container_width=False):
    chosen = st.date_input("Ir a fecha", value=selected_date)
    if chosen != selected_date:
        st.session_state.sn_selected_date = chosen
        st.query_params["sn_date"] = chosen.isoformat()
        st.rerun()

# HTML anchors ensure the browser keeps all seven days on one scrollable row.
# The selected date is an actual URL parameter, so clicking it refreshes fixtures.
date_links = []
for day in week_days:
    selected = day == selected_date
    label = "Hoy" if day == local_today() else short_days[day.weekday()]
    css_class = " selected" if selected else ""
    date_links.append(
        f'<a class="sn-day{css_class}" href="?sn_date={day.isoformat()}" '
        f'aria-label="Ver partidos del {day.isoformat()}">'
        f'<span>{html.escape(label)}</span><strong>{day.day}</strong></a>'
    )
st.markdown('<nav class="sn-date-rail" aria-label="Seleccionar día">'
            + "".join(date_links) + '</nav>', unsafe_allow_html=True)

def backtest_nba_history(events, max_games=60):
    """Walk-forward score evaluation. No game sees its own or later scores."""
    ordered = sorted(
        (m for m in (parse_event(e) for e in events) if m and m["completed"]),
        key=lambda m: str(m.get("date") or ""))
    by_team = {}
    evaluated = []
    for match in ordered:
        hid = str(match["home"].get("team", {}).get("id") or "")
        aid = str(match["away"].get("team", {}).get("id") or "")
        hs, aws = numeric_score(match["home"]), numeric_score(match["away"])
        if not hid or not aid or hs is None or aws is None:
            continue
        hg = by_team.get(hid, [])[-10:]
        ag = by_team.get(aid, [])[-10:]
        if len(hg) >= 5 and len(ag) >= 5:
            def wavg(rows, key, decay):
                values = list(reversed(rows))
                weights = [1 / (1 + i * decay) for i in range(len(values))]
                return sum(float(r[key])*w for r,w in zip(values,weights))/sum(weights)
            def projection(decay):
                return (
                    .55*wavg(hg,"gf",decay)+.45*wavg(ag,"ga",decay),
                    .55*wavg(ag,"gf",decay)+.45*wavg(hg,"ga",decay))
            base = projection(0)
            candidate = projection(.17)
            evaluated.append({"date":str(match["date"])[:10],
                "match":f'{team_name(match["home"])} vs {team_name(match["away"])}',
                "actual_home":hs,"actual_away":aws,
                "base_home":base[0],"base_away":base[1],
                "candidate_home":candidate[0],"candidate_away":candidate[1]})
        by_team.setdefault(hid, []).append({"gf":hs,"ga":aws})
        by_team.setdefault(aid, []).append({"gf":aws,"ga":hs})
    return evaluated[-max_games:]


if sport_label == "⚾ KBO":
    st.info("KBO: la fuente ESPN utilizada no ofrece un endpoint válido para esta liga. "
            "Se ha desactivado esa consulta para evitar el error HTTP 400. "
            "Los partidos y las predicciones KBO requieren integrar otra fuente verificable.")
st.toggle("Destacados primero ✦", value=True, key="sn_trending",
          help="Orden editorial: partidos en vivo, transmisiones y equipos reconocidos. No son tendencias medidas por audiencia.")
search = st.text_input("Buscar equipos", placeholder="⌕  Buscar equipos...", label_visibility="collapsed")
with st.expander("Liga o competición", expanded=False):
    league_options = list(sport["leagues"].keys())
    # st.pills renders actual touch buttons, avoiding the iOS keyboard that
    # st.selectbox may open when its searchable dropdown receives focus.
    league_name = st.pills(
        "Selecciona una liga",
        options=league_options,
        default=league_options[0],
        selection_mode="single",
        key=f"nyuz_league_{sport_label}",
    ) or league_options[0]


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
    if st.session_state.get("sn_trending", True):
        matches.sort(key=lambda m: (-trend_score(m), str(m.get("date") or "")))
    else:
        matches.sort(key=lambda m: str(m.get("date") or ""))
    live = sum(1 for m in matches if m["state"] == "in")
    finished = sum(1 for m in matches if m["completed"])
    upcoming = len(matches) - live - finished

    st.caption(f"{league_name} · {len(matches)} partidos · {live} en vivo")
    if st.session_state.get("sn_trending", True):
        st.caption("✦ Destacados primero · orden orientativo, no popularidad en tiempo real")



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
        # Automatically capture visible upcoming football fixtures before kickoff.
        # Does not depend on the user expanding the match analysis.
        if sport_label == "⚽ Fútbol":
            for upcoming_match in matches:
                record_upcoming_match(upcoming_match, historical_data,
                                      sport["path"], league_code, selected_date)
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
    "Nyuz es un proyecto independiente. ESPN y las ligas mencionadas "
    "pertenecen a sus respectivos titulares. Los datos pueden retrasarse, "
    "cambiar o no estar disponibles. No se generan estadísticas inexistentes."
)

# Section links scroll to real sections in the same page.
st.markdown("""<nav class="ny-bottom-nav" aria-label="Navegación NYUZ">
<a class="nav-item active" href="#ny-inicio"><strong>⌂</strong>Inicio</a>
<a class="nav-item" href="#ny-partidos"><strong>▦</strong>Partidos</a>
<a class="nav-item" href="#ny-lab"><strong>▥</strong>Model Lab</a>
<a class="nav-item" href="#ny-partidos"><strong>⌕</strong>Explorar</a>
</nav>""",unsafe_allow_html=True)
