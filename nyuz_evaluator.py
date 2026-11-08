"""NYUZ 3.2 - unattended evaluation of *existing* pre-match snapshots.

Run: python nyuz_evaluator.py
Requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in server-side secrets.
No Streamlit import. Never creates/changes a pre-match prediction.
"""
from __future__ import annotations

import json
import math
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import requests

BASE = 'https://site.api.espn.com/apis/site/v2/sports'
METRIC_NAMES = {
    'shots': ('totalshots', 'shots', 'totalshotsattempts'),
    'sot': ('shotsontarget', 'shotsongoal'),
    'corners': ('cornerkicks', 'corners'),
    'yellow': ('yellowcards',),
    'fouls': ('fouls', 'foulscommitted'),
}


def utc(value):
    dt = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    if dt.tzinfo is None:
        raise ValueError('timestamp without timezone')
    return dt.astimezone(timezone.utc)


def finite_number(value):
    try:
        if value is None or isinstance(value, bool):
            return None
        result = float(str(value).replace(',', ''))
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def normalize_probabilities(probabilities):
    if not isinstance(probabilities, dict):
        return None
    vals = [finite_number(probabilities.get(k)) for k in ('home', 'draw', 'away')]
    if any(v is None or v < 0 for v in vals):
        return None
    if max(vals) > 1:
        vals = [v / 100 for v in vals]
    if any(v > 1 for v in vals) or abs(sum(vals) - 1) > 0.03:
        return None
    total = sum(vals)
    return [v / total for v in vals] if total else None


def parse_teams(event):
    comp = (event.get('competitions') or [{}])[0]
    entries = comp.get('competitors') or []
    home = next((t for t in entries if t.get('homeAway') == 'home'), None)
    away = next((t for t in entries if t.get('homeAway') == 'away'), None)
    return home, away


def normalized_stat_name(stat):
    return ''.join(ch for ch in str(stat.get('name') or stat.get('abbreviation') or stat.get('label') or '').lower() if ch.isalnum())


def actual_from_espn(event, summary):
    """Return home/away actuals; unavailable stats are omitted, never invented."""
    home, away = parse_teams(event)
    if not home or not away:
        return None
    hs = finite_number(home.get('score', {}).get('value') if isinstance(home.get('score'), dict) else home.get('score'))
    aws = finite_number(away.get('score', {}).get('value') if isinstance(away.get('score'), dict) else away.get('score'))
    if hs is None or aws is None:
        return None
    metrics = {'goals': [hs, aws]}
    team_ids = [str((x.get('team') or {}).get('id') or '') for x in (home, away)]
    for entry in ((summary or {}).get('boxscore') or {}).get('teams') or []:
        tid = str((entry.get('team') or {}).get('id') or '')
        if not tid or tid not in team_ids:
            continue
        side = team_ids.index(tid)
        for stat in entry.get('statistics') or []:
            if not isinstance(stat, dict):
                continue
            name = normalized_stat_name(stat)
            for metric, aliases in METRIC_NAMES.items():
                if metric == 'goals' or name not in aliases:
                    continue
                val = finite_number(stat.get('value') if stat.get('value') is not None else stat.get('displayValue'))
                if val is not None:
                    metrics.setdefault(metric, [None, None])[side] = val
    return {'home': hs, 'away': aws, 'metrics': metrics}


def evaluate(snapshot, actual):
    payload = snapshot['payload']
    if isinstance(payload, str):
        payload = json.loads(payload)
    if not isinstance(payload, dict):
        raise ValueError('invalid prediction payload')
    pred_metrics = payload.get('metrics') or {}
    metric_errors = {}
    for name, pair in pred_metrics.items():
        observed = actual['metrics'].get(name)
        if not isinstance(pair, (list, tuple)) or len(pair) != 2 or not isinstance(observed, (list, tuple)) or len(observed) != 2:
            continue
        diffs = []
        for prediction, reality in zip(pair, observed):
            p, r = finite_number(prediction), finite_number(reality)
            diffs.append(round(p-r, 6) if p is not None and r is not None else None)
        if any(d is not None for d in diffs):
            metric_errors[name] = diffs
    outcome = {}
    if snapshot['sport'] == 'soccer':
        probs = normalize_probabilities(payload.get('probabilities'))
        if probs:
            idx = 0 if actual['home'] > actual['away'] else (1 if actual['home'] == actual['away'] else 2)
            predicted = max(range(3), key=lambda i: probs[i])
            outcome = {
                'classes': ['home', 'draw', 'away'],
                'actual': ['home', 'draw', 'away'][idx],
                'predicted': ['home', 'draw', 'away'][predicted],
                'correct': predicted == idx,
                'brier': round(sum((p - (i == idx))**2 for i, p in enumerate(probs))/3, 6),
                'log_loss': round(-math.log(max(probs[idx], 1e-15)), 6),
            }
    return {
        'sport': snapshot['sport'], 'league': snapshot['league'],
        'event_id': str(snapshot['event_id']), 'kickoff_utc': snapshot['kickoff_utc'],
        'model_version': snapshot['model_version'],
        'actual_home': actual['home'], 'actual_away': actual['away'],
        'actual_metrics': actual['metrics'], 'errors': metric_errors,
        'outcome': outcome, 'source': 'espn',
    }


class Supabase:
    def __init__(self):
        self.url = os.environ.get('SUPABASE_URL', '').strip().rstrip('/')
        self.key = (os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('SUPABASE_SECRET_KEY') or '').strip()
        if not self.url.startswith('https://') or not self.key:
            raise ValueError('Configure SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY as GitHub Actions secrets')
        self.headers = {'apikey': self.key, 'Authorization': 'Bearer ' + self.key, 'Content-Type': 'application/json'}
        self.session = requests.Session()

    def get(self, table, params):
        response = self.session.get(f'{self.url}/rest/v1/{table}', headers=self.headers, params=params, timeout=20)
        response.raise_for_status()
        return response.json()

    def insert(self, row):
        response = self.session.post(f'{self.url}/rest/v1/nyuz_evaluaciones', headers={**self.headers, 'Prefer': 'resolution=ignore-duplicates,return=minimal'}, params={'on_conflict': 'sport,league,event_id'}, json=row, timeout=20)
        response.raise_for_status()


def fetch_espn(session, sport, league, endpoint, params):
    url = f'{BASE}/{quote(sport, safe="")}/{quote(league, safe=".")}/{endpoint}'
    response = session.get(url, params=params, headers={'User-Agent': 'NYUZ/3.2 historical-evaluation'}, timeout=20)
    response.raise_for_status()
    return response.json()


def evaluate_pending(db, now=None):
    now = now or datetime.now(timezone.utc)
    # Avoid paginating stale records indefinitely; up to 1000 recent predictions.
    predictions = db.get('predictions', {
        'select': 'sport,league,event_id,created_utc,kickoff_utc,model_version,payload',
        'order': 'kickoff_utc.desc', 'limit': '1000',
        'kickoff_utc': 'lt.' + (now-timedelta(hours=2)).isoformat(),
    })
    existing = db.get('nyuz_evaluaciones', {
        'select': 'sport,league,event_id', 'limit': '1000',
        'kickoff_utc': 'gte.' + (now-timedelta(days=45)).isoformat(),
    })
    done = {(x['sport'], x['league'], str(x['event_id'])) for x in existing}
    pending = []
    for row in predictions:
        try:
            if row['sport'] != 'soccer':  # football first; other sports require dedicated evaluation
                continue
            if utc(row['created_utc']) >= utc(row['kickoff_utc']):
                continue
            if utc(row['kickoff_utc']) < now-timedelta(days=45):
                continue
            if (row['sport'], row['league'], str(row['event_id'])) not in done:
                pending.append(row)
        except (ValueError, TypeError, KeyError):
            continue
    # Cap requests per run; remaining records will be retried on the next schedule.
    pending = pending[:150]
    if not pending:
        print('NYUZ Auto-Evaluation: no pending prematch predictions.')
        return 0
    groups = defaultdict(list)
    for row in pending:
        groups[(row['sport'], row['league'], utc(row['kickoff_utc']).date())].append(row)
    session = requests.Session()
    successes = 0
    deferred = 0
    failed = 0
    for (sport, league, day), rows in groups.items():
        # ESPN scoreboard dates can vary with competition timezones: check +/- one day.
        events = {}
        for offset in (0, -1, 1):
            try:
                data = fetch_espn(session, sport, league, 'scoreboard', {'dates': (day+timedelta(days=offset)).strftime('%Y%m%d'), 'limit': 200})
                for e in data.get('events') or []:
                    events[str(e.get('id'))] = e
            except (requests.RequestException, ValueError) as exc:
                print(f'ESPN scoreboard warning: {league} {day} ({type(exc).__name__})')
        for row in rows:
            event = events.get(str(row['event_id']))
            if not event or not ((event.get('status') or {}).get('type') or {}).get('completed'):
                deferred += 1
                continue
            try:
                summary = fetch_espn(session, sport, league, 'summary', {'event': row['event_id']})
            except (requests.RequestException, ValueError):
                summary = {}  # final score is still usable, but missing metrics are not fabricated
            actual = actual_from_espn(event, summary)
            if not actual:
                deferred += 1
                continue
            try:
                result = evaluate(row, actual)
                db.insert(result)
                successes += 1
            except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
                failed += 1
                print(f'Evaluation write warning: {league} event={row["event_id"]} ({type(exc).__name__})')
    print(f'NYUZ Auto-Evaluation: saved={successes}; awaiting verified results={deferred}; errors={failed}')
    return 1 if failed else 0


def main():
    try:
        return evaluate_pending(Supabase())
    except (ValueError, requests.RequestException) as exc:
        print(f'NYUZ Auto-Evaluation ERROR: {type(exc).__name__}. Verify SQL table and server-side secrets.')
        return 2


if __name__ == '__main__':
    sys.exit(main())
