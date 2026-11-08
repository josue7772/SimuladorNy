
import html
import json
import math
import os
import random
import statistics
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from urllib.parse import quote
from zoneinfo import ZoneInfo

import requests
import streamlit as st

st.set_page_config(
    page_title="NYUZ · Sports Intelligence",
    page_icon="↗",
    layout="wide",
    initial_sidebar_state="collapsed",
)

ESPN = "https://site.api.espn.com/apis/site/v2/sports"
TZ = ZoneInfo("America/Mexico_City")
MODEL_VERSION = "nyuz-unified-2026-11"

LEAGUES = {
    "⚽ Fútbol": {
        "Liga MX": "mex.1",
        "Premier League": "eng.1",
        "LaLiga": "esp.1",
        "Serie A": "ita.1",
        "Bundesliga": "ger.1",
        "Ligue 1": "fra.1",
        "MLS": "usa.1",
        "Champions League": "uefa.champions",
        "Liga Argentina": "arg.1",
        "Brasileirão": "bra.1",
    },
    "🏀 NBA": {"NBA": "nba"},
    "🏈 NFL": {"NFL": "nfl"},
    "🏒 NHL": {"NHL": "nhl"},
}

PATHS = {
    "⚽ Fútbol": "soccer",
    "🏀 NBA": "basketball",
    "🏈 NFL": "football",
    "🏒 NHL": "hockey",
}

# =====================================================
# NYUZ SIGNATURE NAVY
# =====================================================

st.markdown("""
<style>
.stApp {
    background: radial-gradient(
        ellipse at 90% 0%,
        #1b2e54 0%,
        #090f20 32%,
        #050914 75%
    ) !important;
    color: #f7f9ff;
}

.block-container {
    max-width: 960px !important;
    padding: 1rem .85rem 5rem !important;
}

[data-testid="stHeader"] {
    background: transparent !important;
}

[data-testid="stSidebar"],
[data-testid="collapsedControl"] {
    display: none !important;
}

h1, h2, h3, p {
    color: #f4f7ff;
}

h1 {
    letter-spacing: -.05em;
}

.ny-brand {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 12px 0 15px;
}

.ny-logo {
    font-size: 40px;
    color: #bed4ff;
    font-weight: 900;
}

.ny-name {
    font-size: 35px;
    font-weight: 900;
    letter-spacing: -1.5px;
    line-height: 1;
}

.ny-name small {
    display: block;
    font-size: 9px;
    letter-spacing: 2px;
    color: #adc1e2;
    margin-top: 8px;
}

.ny-nav {
    display: flex;
    gap: 7px;
    overflow-x: auto;
    scrollbar-width: none;
    margin: 13px 0 18px;
}

.ny-nav a {
    flex-shrink: 0;
    padding: 10px 12px;
    border: 1px solid #3b5072;
    border-radius: 25px;
    color: #ecf3ff !important;
    text-decoration: none;
    background: #15213a;
    font-size: 12px;
}

.ny-nav a:first-child {
    background: #293e66;
    border-color: #a9c5ff;
}

.ny-hero,
.ny-panel {
    background: linear-gradient(
        135deg, #1b2c4b, #0e192c
    );
    border: 1px solid #385076;
    border-radius: 23px;
    padding: 20px;
    margin: 12px 0 18px;
    box-shadow: 0 10px 25px #0004;
}

.ny-eyebrow {
    font-size: 10px;
    letter-spacing: 2px;
    color: #b7c9e7;
    font-weight: 800;
}

.ny-hero h1 {
    font-size: clamp(26px, 6vw, 38px);
    line-height: 1.1;
    margin: 22px 0;
    color: #fff;
}

.ny-hero p {
    color: #adc0df;
    font-size: 14px;
    line-height: 1.6;
}

.ny-kpis {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 9px;
    margin: 15px 0;
}

.ny-kpi {
    background: #22314b;
    padding: 15px;
    border-radius: 16px;
    border: 1px solid #354766;
}

.ny-kpi strong {
    display: block;
    font-size: 27px;
    color: white;
}

.ny-kpi span {
    color: #bfcee5;
    font-size: 12px;
}

.ny-fixture {
    border: 1px solid #394e72;
    border-radius: 23px;
    background: linear-gradient(
        145deg, #192945, #0d1628
    );
    padding: 17px;
    margin: 13px 0 6px;
}

.ny-meta {
    font-size: 11px;
    color: #b7c8e3;
    margin-bottom: 12px;
}

.ny-teams {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
}

.ny-team {
    flex: 1;
    min-width: 0;
    text-align: center;
    font-size: 14px;
    font-weight: 800;
    overflow-wrap: anywhere;
}

.ny-team img {
    display: block;
    width: 50px;
    height: 50px;
    object-fit: contain;
    margin: 0 auto 10px;
}

.ny-score {
    padding: 9px;
    border-radius: 12px;
    background: #293b5e;
    font-size: 21px;
    font-weight: 900;
    white-space: nowrap;
}

[data-testid="stExpander"] {
    background: #15233b !important;
    border: 1px solid #364966 !important;
    border-radius: 18px !important;
}

[data-testid="stExpander"] summary {
    font-size: 15px !important;
    min-height: 52px;
}

[data-testid="stPills"] [role="group"] {
    display: flex !important;
    flex-wrap: nowrap !important;
    overflow-x: auto !important;
    scrollbar-width: none;
}

[data-testid="stPills"] button {
    white-space: nowrap !important;
    flex: 0 0 auto !important;
    border-radius: 30px !important;
    background: #15233b !important;
    border: 1px solid #364967 !important;
    color: #eff5ff !important;
}

[data-testid="stPills"] button[aria-selected="true"],
[data-testid="stPills"] button[aria-pressed="true"] {
    background: #dce8ff !important;
    color: #101b30 !important;
}

[data-testid="stMetric"] {
    background: #1c2c48;
    padding: 10px;
    border: 1px solid #354967;
    border-radius: 14px;
}

[data-testid="stCaptionContainer"] p {
    color: #a9bfdf !important;
}

.ny-chart {
    width: 100%;
    height: 120px;
}

.ny-chart path {
    fill: none;
    stroke: #f3f6ff;
    stroke-width: 3;
}

@media(max-width:480px) {
    .ny-hero, .ny-panel {
        padding: 16px;
    }

    .ny-team {
        font-size: 12px;
    }

    .ny-team img {
        width: 39px;
        height: 39px;
    }

    .ny-score {
        font-size: 17px;
    }
}
</style>
""", unsafe_allow_html=True)


# =====================================================
# UTILIDADES Y DATOS DE ESPN
# =====================================================

def today():
    return datetime.now(TZ).date()


def utc(value):
    dt = datetime.fromisoformat(
        str(value).replace("Z", "+00:00")
    )
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def numeric(value):
    if isinstance(value, dict):
        value = value.get(
            "value", value.get("displayValue")
        )
    try:
        n = float(value)
        return n if math.isfinite(n) else None
    except (TypeError, ValueError):
        return None


@st.cache_data(ttl=180, show_spinner=False)
def espn(path, league, endpoint="scoreboard", params=None):
    url = (
        f"{ESPN}/{path}/"
        f"{quote(league, safe='.')}/{endpoint}"
    )
    response = requests.get(
        url,
        params=params or {},
        headers={
            "User-Agent": "Mozilla/5.0 NYUZ Sports Intelligence"
        },
        timeout=18,
    )
    response.raise_for_status()
    result = response.json()
    return result if isinstance(result, dict) else {}


def parse_event(raw):
    competition = (
        raw.get("competitions")
        or [raw.get("competition") or {}]
    )[0]

    competitors = competition.get("competitors") or []

    home = next(
        (c for c in competitors
         if c.get("homeAway") == "home"),
        None,
    )
    away = next(
        (c for c in competitors
         if c.get("homeAway") == "away"),
        None,
    )

    if home is None or away is None:
        return None

    status = (
        (raw.get("status") or {}).get("type") or {}
    )

    return {
        "id": str(raw.get("id") or ""),
        "date": raw.get("date"),
        "home": home,
        "away": away,
        "state": status.get("state", "pre"),
        "completed": bool(status.get("completed")),
        "status": (
            status.get("shortDetail")
            or status.get("detail")
            or "Programado"
        ),
    }


def name(team):
    return (
        (team.get("team") or {}).get("displayName")
        or "Equipo"
    )


def tid(team):
    return str(
        (team.get("team") or {}).get("id") or ""
    )


def fixture_html(match, league):

    def block(team):
        logo = (
            (team.get("team") or {}).get("logo")
            or ""
        )

        if str(logo).startswith("https://"):
            img = (
                f'<img src="{html.escape(logo, quote=True)}" '
                'alt="" />'
            )
        else:
            img = ""

        return (
            '<div class="ny-team">'
            + img
            + html.escape(name(team))
            + '</div>'
        )

    if match["state"] == "pre":
        score = "VS"
    else:
        score = (
            f"{match['home'].get('score', '—')} : "
            f"{match['away'].get('score', '—')}"
        )

    return (
        '<div class="ny-fixture">'
        '<div class="ny-meta">'
        + html.escape(league)
        + " · "
        + html.escape(match["status"])
        + '</div><div class="ny-teams">'
        + block(match["home"])
        + '<div class="ny-score">'
        + html.escape(str(score))
        + '</div>'
        + block(match["away"])
        + '</div></div>'
    )


# =====================================================
# HISTORIAL DEPORTIVO
# =====================================================

@st.cache_data(ttl=3600, show_spinner=False)
def prior_events(path, league, day):
    result = {}

    for span in range(0, 100, 10):
        end = day - timedelta(days=span + 1)
        start = end - timedelta(days=9)

        try:
            payload = espn(
                path,
                league,
                params={
                    "dates": (
                        f"{start:%Y%m%d}-"
                        f"{end:%Y%m%d}"
                    ),
                    "limit": 300,
                },
            )

            for event in payload.get("events") or []:
                if event.get("id"):
                    result[str(event["id"])] = event

        except (requests.RequestException, ValueError):
            continue

    return list(result.values())


@st.cache_data(ttl=3600, show_spinner=False)
def nfl_history(day):
    result = {}
    diagnostics = []

    for year in (day.year - 1, day.year):
        try:
            payload = espn(
                "football",
                "nfl",
                params={
                    "dates": str(year),
                    "seasontype": 2,
                    "limit": 500,
                },
            )

            for event in payload.get("events") or []:
                if event.get("id"):
                    result[str(event["id"])] = event

        except (requests.RequestException, ValueError) as ex:
            diagnostics.append(
                f"{year}: {type(ex).__name__}"
            )

    return list(result.values()), diagnostics


@st.cache_data(ttl=3600, show_spinner=False)
def team_schedule(path, league, team_id, year):
    try:
        return espn(
            path,
            league,
            endpoint=f"teams/{team_id}/schedule",
            params={
                "season": year,
                "limit": 200,
            },
        ).get("events") or []

    except (requests.RequestException, ValueError):
        return []


def history(match, events, path, league, cutoff):
    raw = {
        str(e.get("id")): e
        for e in events
        if e.get("id")
    }

    for team in (match["home"], match["away"]):
        team_id = tid(team)

        if not team_id:
            continue

        for year in (
            cutoff.year - 1,
            cutoff.year,
        ):
            for e in team_schedule(
                path, league, team_id, year
            ):
                if e.get("id"):
                    raw[str(e["id"])] = e

    groups = {
        tid(match["home"]): [],
        tid(match["away"]): [],
    }

    start = utc(match["date"])

    for e in raw.values():
        try:
            ev = parse_event(e)

            if not ev:
                continue
            if not ev["completed"]:
                continue
            if utc(ev["date"]) >= start:
                continue
            if ev["id"] == match["id"]:
                continue

            h, a = ev["home"], ev["away"]
            hs = numeric(h.get("score"))
            aws = numeric(a.get("score"))

            if hs is None or aws is None:
                continue

            if tid(h) in groups:
                groups[tid(h)].append(
                    (utc(ev["date"]), hs, aws)
                )

            if tid(a) in groups:
                groups[tid(a)].append(
                    (utc(ev["date"]), aws, hs)
                )

        except (TypeError, ValueError, KeyError):
            continue

    return [
        sorted(
            groups.get(tid(team), []),
            reverse=True,
        )[:10]
        for team in (match["home"], match["away"])
    ]


# =====================================================
# MOTOR MONTE CARLO
# FUTBOL · NBA · NFL · NHL
# =====================================================

def simulate(match, events, path, league, selected_date):

    if path == "football":
        events, warnings = nfl_history(selected_date)
    else:
        warnings = []

    local, visitor = history(
        match, events, path, league, selected_date
    )

    if min(len(local), len(visitor)) < 4:
        st.warning(
            f"Historial insuficiente: "
            f"local {len(local)}/4 y "
            f"visitante {len(visitor)}/4. "
            "No inventaremos estadísticas."
        )

        if warnings:
            st.caption(
                "Diagnóstico NFL: "
                + ", ".join(warnings)
            )

        return None

    def avg(rows, k):
        return sum(r[k] for r in rows) / len(rows)

    mu_h = max(
        .05,
        .57 * avg(local, 1)
        + .43 * avg(visitor, 2),
    )
    mu_a = max(
        .05,
        .57 * avg(visitor, 1)
        + .43 * avg(local, 2),
    )

    if path == "football":
        mu_h += 1.0

    rng = random.Random(
        str(match["id"]) + MODEL_VERSION
    )

    sd_h = max(
        6.0 if path == "football" else 8.0,
        statistics.pstdev(r[1] for r in local),
    )
    sd_a = max(
        6.0 if path == "football" else 8.0,
        statistics.pstdev(r[1] for r in visitor),
    )

    win_h = 0
    win_a = 0
    draw = 0
    totals = [0, 0]

    for _ in range(10000):

        if path in ("basketball", "football"):
            shared = rng.gauss(
                0,
                2 if path == "football" else 3,
            )

            x = max(
                0,
                round(rng.gauss(mu_h, sd_h) + shared),
            )
            y = max(
                0,
                round(rng.gauss(mu_a, sd_a) + shared),
            )

        else:
            def poisson(lam):
                p = 1.0
                k = 0
                limit = math.exp(-min(20, lam))

                while p > limit:
                    k += 1
                    p *= rng.random()

                return k - 1

            x = poisson(mu_h)
            y = poisson(mu_a)

        if path in ("basketball", "hockey") and x == y:
            if rng.random() < mu_h / (mu_h + mu_a):
                x += 1
            else:
                y += 1

        win_h += x > y
        win_a += y > x
        draw += x == y

        totals[0] += x
        totals[1] += y

    return {
        "home": totals[0] / 10000,
        "away": totals[1] / 10000,
        "win_h": win_h / 100,
        "win_a": win_a / 100,
        "draw": draw / 100,
        "games": (
            len(local),
            len(visitor),
        ),
    }


# =====================================================
# SUPABASE
# =====================================================

def cloud_config():

    def get(key):
        try:
            return str(
                st.secrets.get(key, "")
                or os.getenv(key, "")
            ).strip()
        except (
            FileNotFoundError,
            KeyError,
            AttributeError,
        ):
            return os.getenv(key, "").strip()

    return (
        get("SUPABASE_URL").rstrip("/"),
        get("SUPABASE_SERVICE_ROLE_KEY")
        or get("SUPABASE_SECRET_KEY"),
    )


def cloud_get(table, query):
    url, key = cloud_config()

    if not url or not key:
        return [], (
            "Supabase no está configurado "
            "en este entorno."
        )

    try:
        r = requests.get(
            url + f"/rest/v1/{table}",
            headers={
                "apikey": key,
                "Authorization": "Bearer " + key,
            },
            params=query,
            timeout=15,
        )
        r.raise_for_status()
        return r.json(), None

    except (requests.RequestException, ValueError) as ex:
        return [], (
            f"No se pudo consultar {table}: "
            f"{type(ex).__name__}"
        )


def record_prediction(match, path, league, pred):
    if path != "soccer":
        return False

    if match["state"] != "pre":
        return False

    if utc(match["date"]) <= datetime.now(timezone.utc):
        return False

    url, key = cloud_config()

    if not url or not key:
        return False

    now = datetime.now(timezone.utc).isoformat()

    record = {
        "home": name(match["home"]),
        "away": name(match["away"]),
        "kickoff": utc(match["date"]).isoformat(),
        "model_version": MODEL_VERSION,
        "metrics": {
            "goals": [
                pred["home"],
                pred["away"],
            ],
        },
        "probabilities": {
            "home": pred["win_h"],
            "draw": pred["draw"],
            "away": pred["win_a"],
        },
    }

    try:
        r = requests.post(
            url + "/rest/v1/predictions",
            headers={
                "apikey": key,
                "Authorization": "Bearer " + key,
                "Content-Type": "application/json",
                "Prefer": (
                    "resolution=ignore-duplicates,"
                    "return=minimal"
                ),
            },
            params={
                "on_conflict": "sport,league,event_id"
            },
            json={
                "sport": path,
                "league": league,
                "event_id": match["id"],
                "created_utc": now,
                "kickoff_utc": utc(
                    match["date"]
                ).isoformat(),
                "model_version": MODEL_VERSION,
                "payload": record,
            },
            timeout=15,
        )

        r.raise_for_status()
        return True

    except requests.RequestException:
        return False


# =====================================================
# CAPTURA AUTOMATICA GITHUB ACTIONS
# =====================================================

def run_scheduled_capture():
    url, key = cloud_config()

    if not url or not key:
        print(
            "ERROR: Configure SUPABASE_URL y "
            "SUPABASE_SERVICE_ROLE_KEY en "
            "GitHub Actions Secrets."
        )
        return 2

    checked = 0
    saved = 0
    errors = 0

    leagues = (
        "mex.1",
        "eng.1",
        "esp.1",
        "ita.1",
        "ger.1",
        "fra.1",
        "usa.1",
        "uefa.champions",
        "por.1",
        "bra.1",
        "arg.1",
    )

    for league in leagues:
        for day in (
            today(),
            today() + timedelta(days=1),
        ):
            try:
                payload = espn(
                    "soccer",
                    league,
                    params={
                        "dates": f"{day:%Y%m%d}",
                        "limit": 100,
                    },
                )

                matches = [
                    parse_event(e)
                    for e in payload.get("events") or []
                ]
                matches = [
                    m for m in matches
                    if m and m["state"] == "pre"
                ]

                if not matches:
                    continue

                prior = prior_events(
                    "soccer", league, day
                )

                for match in matches:
                    checked += 1

                    lh, la = history(
                        match,
                        prior,
                        "soccer",
                        league,
                        day,
                    )

                    if min(len(lh), len(la)) < 4:
                        continue

                    def avg(rows, k):
                        return (
                            sum(r[k] for r in rows)
                            / len(rows)
                        )

                    ph = max(
                        .05,
                        .57 * avg(lh, 1)
                        + .43 * avg(la, 2),
                    )
                    pa = max(
                        .05,
                        .57 * avg(la, 1)
                        + .43 * avg(lh, 2),
                    )

                    rng = random.Random(
                        match["id"] + MODEL_VERSION
                    )

                    wh = 0
                    wa = 0
                    dr = 0

                    for _ in range(10000):

                        def sample(lam):
                            p = 1.0
                            n = 0
                            threshold = math.exp(
                                -min(20, lam)
                            )
                            while p > threshold:
                                n += 1
                                p *= rng.random()
                            return n - 1

                        x = sample(ph)
                        y = sample(pa)

                        wh += x > y
                        wa += y > x
                        dr += x == y

                    pred = {
                        "home": ph,
                        "away": pa,
                        "win_h": wh / 100,
                        "win_a": wa / 100,
                        "draw": dr / 100,
                    }

                    saved += bool(
                        record_prediction(
                            match,
                            "soccer",
                            league,
                            pred,
                        )
                    )

            except (
                requests.RequestException,
                ValueError,
                KeyError,
                TypeError,
            ) as ex:
                errors += 1
                print(
                    f"Capture warning: {league} "
                    f"{day} {type(ex).__name__}"
                )

    print(
        f"NYUZ: fixtures={checked}; "
        f"snapshots registered or already "
        f"present={saved}; errors={errors}"
    )

    return 4 if errors == 22 else 0


if __name__ == "__main__" and "--capture" in sys.argv:
    raise SystemExit(run_scheduled_capture())


# =====================================================
# PERFORMANCE CENTER
# =====================================================

def performance_center():
    predictions, p_error = cloud_get(
        "predictions",
        {
            "select": (
                "sport,league,event_id,payload,"
                "created_utc,kickoff_utc"
            ),
            "order": "created_utc.desc",
            "limit": 500,
        },
    )

    evaluations, e_error = cloud_get(
        "nyuz_evaluaciones",
        {
            "select": (
                "sport,league,event_id,"
                "evaluated_utc,errors,outcome,"
                "actual_home,actual_away"
            ),
            "order": "evaluated_utc.desc",
            "limit": 1000,
        },
    )

    ids = {
        (
            r["sport"],
            r["league"],
            str(r["event_id"]),
        ): r
        for r in predictions
        if isinstance(r, dict)
    }

    checked = []
    correct = []
    gerr = []
    serr = []
    trend = []

    for e in sorted(
        evaluations,
        key=lambda r: str(
            r.get("evaluated_utc", "")
        ),
    ):
        if not isinstance(e, dict):
            continue

        key = (
            e.get("sport"),
            e.get("league"),
            str(e.get("event_id")),
        )

        original = ids.get(key)

        if not original:
            continue

        try:
            if utc(original["created_utc"]) >= utc(
                original["kickoff_utc"]
            ):
                continue
        except (KeyError, ValueError, TypeError):
            continue

        checked.append((original, e))

        outcome = e.get("outcome") or {}
        errs = e.get("errors") or {}

        if isinstance(outcome, str):
            try:
                outcome = json.loads(outcome)
            except ValueError:
                outcome = {}

        if isinstance(errs, str):
            try:
                errs = json.loads(errs)
            except ValueError:
                errs = {}

        if (
            isinstance(outcome, dict)
            and isinstance(
                outcome.get("correct"), bool
            )
        ):
            correct.append(outcome["correct"])
            trend.append(
                100 * sum(correct) / len(correct)
            )

        for metric, target in (
            ("goals", gerr),
            ("shots", serr),
        ):
            values = (
                errs.get(metric)
                if isinstance(errs, dict)
                else None
            )

            if isinstance(values, list):
                target.extend(
                    abs(numeric(v))
                    for v in values
                    if numeric(v) is not None
                )

    def fmt(nums):
        return (
            f"{sum(nums) / len(nums):.2f}"
            if nums
            else "—"
        )

    accuracy = (
        f"{100 * sum(correct) / len(correct):.1f}%"
        if correct
        else "—"
    )

    cards = (
        ("Partidos evaluados", len(checked)),
        ("Acierto 1X2", accuracy),
        ("MAE de goles", fmt(gerr)),
        ("MAE de tiros", fmt(serr)),
    )

    card_html = "".join(
        '<div class="ny-kpi">'
        f"<strong>{html.escape(str(value))}</strong>"
        f"<span>{label}</span>"
        "</div>"
        for label, value in cards
    )

    st.markdown(
        '<div class="ny-panel" id="ny-performance">'
        '<div class="ny-eyebrow">'
        "NYUZ SPORTS INTELLIGENCE"
        "</div>"
        "<h2>PERFORMANCE CENTER ↗</h2>"
        "<p>Resultados reales · Supabase</p>"
        '<div class="ny-kpis">'
        + card_html
        + "</div></div>",
        unsafe_allow_html=True,
    )

    if p_error or e_error:
        st.info(
            "Datos de rendimiento no disponibles: "
            + str(p_error or e_error)
        )

    if len(trend) >= 2:
        low = min(trend)
        high = max(trend)
        span = max(1.0, high - low)

        coords = " ".join(
            (
                f"{10 + 300 * i / (len(trend)-1):.1f},"
                f"{100 - 80 * (v-low) / span:.1f}"
            )
            for i, v in enumerate(trend)
        )

        st.markdown(
            '<div class="ny-panel">'
            "<b>Historial de rendimiento</b>"
            '<svg class="ny-chart" '
            'viewBox="0 0 320 120">'
            f'<polyline points="{coords}" '
            'fill="none" stroke="#eff4ff" '
            'stroke-width="3"/>'
            "</svg></div>",
            unsafe_allow_html=True,
        )
    else:
        st.caption(
            "La gráfica aparecerá cuando existan "
            "dos evaluaciones verificadas."
        )

    with st.expander(
        "Pronóstico original vs. resultado real"
    ):
        rows = []

        for original, e in reversed(checked[-80:]):
            payload = original.get("payload") or {}

            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except ValueError:
                    payload = {}

            rows.append({
                "Liga": original["league"],
                "Partido": (
                    str(payload.get("home", "?"))
                    + " vs "
                    + str(payload.get("away", "?"))
                ),
                "Real": (
                    f"{e.get('actual_home', '—')} - "
                    f"{e.get('actual_away', '—')}"
                ),
            })

        if rows:
            st.dataframe(
                rows,
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.info(
                "Todavía no hay encuentros evaluados."
            )


# =====================================================
# INTERFAZ PRINCIPAL
# =====================================================

st.markdown(
    '<div class="ny-brand" id="inicio">'
    '<div class="ny-logo">↗</div>'
    '<div class="ny-name">'
    'NYUZ<small>SPORTS INTELLIGENCE</small>'
    "</div></div>",
    unsafe_allow_html=True,
)

st.markdown(
    '<nav class="ny-nav">'
    '<a href="#inicio">⌂ Inicio</a>'
    '<a href="#deportes">◎ Predicciones</a>'
    '<a href="#historial">◷ Historial</a>'
    '<a href="#ny-performance">▥ Performance Center</a>'
    "</nav>",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="ny-hero">'
    '<div class="ny-eyebrow">'
    "NYUZ / INTELIGENCIA CUANTITATIVA"
    "</div>"
    "<h1>Predicciones deportivas"
    "<br>basadas en datos.</h1>"
    "<p>10,000 simulaciones · Historial verificable"
    "<br>Backtesting y evaluación automática</p>"
    "</div>",
    unsafe_allow_html=True,
)

st.markdown(
    '<div id="deportes"></div>',
    unsafe_allow_html=True,
)

st.subheader("Explorar deportes")

sport = (
    st.pills(
        "Deporte",
        list(LEAGUES),
        default="⚽ Fútbol",
        selection_mode="single",
        label_visibility="collapsed",
    )
    or "⚽ Fútbol"
)

path = PATHS[sport]

default_league = next(iter(LEAGUES[sport]))

league_name = (
    st.pills(
        "Liga",
        list(LEAGUES[sport]),
        default=default_league,
        selection_mode="single",
    )
    or default_league
)

league = LEAGUES[sport][league_name]

st.subheader("Partidos del día")

selected = st.date_input(
    "Seleccionar fecha",
    value=today(),
)

filter_state = (
    st.pills(
        "Estado",
        [
            "Todos",
            "En vivo",
            "Próximos",
            "Finalizados",
        ],
        default="Todos",
        selection_mode="single",
    )
    or "Todos"
)

search = st.text_input(
    "Buscar equipo",
    placeholder="Buscar equipos...",
)


# =====================================================
# MODEL LAB
# =====================================================

with st.expander(
    "Model Lab · Backtesting NBA",
    expanded=False,
):
    st.caption(
        "Auditoría retrospectiva con información "
        "anterior a cada partido. "
        "No modifica el modelo en producción."
    )

    if st.button(
        "Evaluar partidos históricos NBA"
    ):
        games = prior_events(
            "basketball",
            "nba",
            today(),
        )

        ordered = sorted(
            [
                m
                for m in (
                    parse_event(g) for g in games
                )
                if m and m["completed"]
            ],
            key=lambda m: str(m["date"]),
        )

        by_team = defaultdict(list)
        results = []

        for game in ordered:
            h, a = game["home"], game["away"]
            hi, ai = tid(h), tid(a)

            hs = numeric(h.get("score"))
            aws = numeric(a.get("score"))

            if hs is None or aws is None:
                continue

            lh = by_team[hi][-10:]
            la = by_team[ai][-10:]

            if len(lh) >= 5 and len(la) >= 5:
                ph = (
                    .55 * statistics.mean(
                        r[0] for r in lh
                    )
                    + .45 * statistics.mean(
                        r[1] for r in la
                    )
                )

                pa = (
                    .55 * statistics.mean(
                        r[0] for r in la
                    )
                    + .45 * statistics.mean(
                        r[1] for r in lh
                    )
                )

                results.append({
                    "Partido": (
                        name(h) + " vs " + name(a)
                    ),
                    "Pronóstico": (
                        f"{ph:.1f} - {pa:.1f}"
                    ),
                    "Real": (
                        f"{hs:.0f} - {aws:.0f}"
                    ),
                    "Error absoluto medio": (
                        abs(ph - hs) + abs(pa - aws)
                    ) / 2,
                })

            by_team[hi].append((hs, aws))
            by_team[ai].append((aws, hs))

        st.session_state["backtest"] = results

    if "backtest" in st.session_state:
        rows = st.session_state["backtest"]

        if rows:
            st.metric(
                "Partidos evaluados",
                len(rows),
            )

            st.metric(
                "MAE de puntos",
                f"{statistics.mean(r['Error absoluto medio'] for r in rows):.2f}",
            )

            st.dataframe(
                rows,
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.warning(
                "La fuente no aportó suficientes "
                "partidos históricos para "
                "una evaluación."
            )


# =====================================================
# HISTORIAL VERIFICABLE
# =====================================================

st.markdown(
    '<div id="historial"></div>',
    unsafe_allow_html=True,
)

try:
    from nyuz_lab3 import render_history

    url, key = cloud_config()

    render_history(
        "simuladorny_predictions.sqlite3",
        url,
        key,
        lambda p, l, d: espn(
            p,
            l,
            params={
                "dates": f"{d:%Y%m%d}"
            },
        ).get("events") or [],
        parse_event,
        numeric,
    )

except (ImportError, AttributeError) as exc:
    st.info(
        "Historial avanzado no disponible. "
        "Revisa nyuz_lab3.py: "
        + type(exc).__name__
    )


# =====================================================
# PERFORMANCE CENTER ACTIVO
# =====================================================

performance_center()


# =====================================================
# CALENDARIO Y PARTIDOS
# =====================================================

try:
    payload = espn(
        path,
        league,
        params={
            "dates": f"{selected:%Y%m%d}",
            "limit": 150,
        },
    )

    matches = [
        parse_event(e)
        for e in payload.get("events") or []
    ]

    matches = [
        m for m in matches if m
    ]

    if search.strip():
        matches = [
            m for m in matches
            if search.casefold() in (
                name(m["home"])
                + " "
                + name(m["away"])
            ).casefold()
        ]

    if filter_state == "En vivo":
        matches = [
            m for m in matches
            if m["state"] == "in"
        ]

    elif filter_state == "Próximos":
        matches = [
            m for m in matches
            if m["state"] == "pre"
        ]

    elif filter_state == "Finalizados":
        matches = [
            m for m in matches
            if m["completed"]
        ]

    st.caption(
        f"{league_name} · "
        f"{len(matches)} partidos · Fuente ESPN"
    )

    if not matches:
        st.info(
            "No hay partidos disponibles para "
            "la fecha y filtros seleccionados."
        )

    else:
        previous = (
            []
            if path == "football"
            else prior_events(
                path, league, selected
            )
        )

        for m in matches:
            st.markdown(
                fixture_html(m, league_name),
                unsafe_allow_html=True,
            )

            with st.expander(
                "Ver análisis y predicciones"
            ):

                if m["state"] == "in":
                    st.caption(
                        "EN VIVO · Los datos pueden "
                        "tener retraso."
                    )

                with st.spinner(
                    "Consultando historial y simulando..."
                ):
                    prediction = simulate(
                        m,
                        previous,
                        path,
                        league,
                        selected,
                    )

                if prediction:
                    c1, c2, c3 = st.columns(3)

                    c1.metric(
                        "Local",
                        f"{prediction['win_h']:.1f}%",
                    )
                    c2.metric(
                        "Empate",
                        f"{prediction['draw']:.1f}%",
                    )
                    c3.metric(
                        "Visitante",
                        f"{prediction['win_a']:.1f}%",
                    )

                    unit = (
                        "Puntos"
                        if path in (
                            "basketball",
                            "football",
                        )
                        else "Goles"
                    )

                    st.markdown(
                        f"**{unit} proyectados:** "
                        f"{prediction['home']:.1f} — "
                        f"{prediction['away']:.1f}"
                    )

                    st.caption(
                        "10,000 simulaciones · "
                        f"Historial "
                        f"{prediction['games'][0]} y "
                        f"{prediction['games'][1]} "
                        "partidos · Modelo experimental"
                    )

                    if path == "football":
                        st.info(
                            "NFL: simulación de puntos "
                            "desde resultados anteriores. "
                            "Yardas y touchdowns requieren "
                            "boxscores históricos "
                            "independientes."
                        )

                    if m["state"] != "pre":
                        st.info(
                            "Análisis retrospectivo; "
                            "no es un pronóstico publicado "
                            "antes del inicio."
                        )

                    if (
                        path == "soccer"
                        and m["state"] == "pre"
                    ):
                        record_prediction(
                            m,
                            path,
                            league,
                            prediction,
                        )

except (
    requests.RequestException,
    ValueError,
    KeyError,
    TypeError,
) as exc:
    st.error(
        "El proveedor deportivo no respondió "
        "correctamente: "
        + type(exc).__name__
    )


st.caption(
    "NYUZ es independiente. ESPN es una fuente "
    "pública no oficial; su disponibilidad puede "
    "cambiar. Las probabilidades son experimentales, "
    "no resultados garantizados."
)
