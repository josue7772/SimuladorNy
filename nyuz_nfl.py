"""NYUZ NFL Intelligence: modelos descriptivos desde partidos YA terminados.
No usa resultados futuros ni muestra probabilidades sin historial suficiente.
Fuente: JSON público no oficial de ESPN; puede estar incompleto.
"""
import math
import random
import statistics
from datetime import datetime, timedelta, timezone
import requests
import streamlit as st

BASE = 'https://site.api.espn.com/apis/site/v2/sports/football/nfl'

@st.cache_data(ttl=1800, show_spinner=False)
def nfl_past_events(day_iso):
    # Ventana propia de NFL: temporada actual y, si procede, temporada anterior.
    cutoff = datetime.fromisoformat(day_iso).replace(tzinfo=timezone.utc)
    start = (cutoff - timedelta(days=230)).strftime('%Y%m%d')
    end = cutoff.strftime('%Y%m%d')
    r = requests.get(f'{BASE}/scoreboard', params={'dates':f'{start}-{end}', 'limit':'400'},timeout=20)
    r.raise_for_status()
    return r.json().get('events', [])

@st.cache_data(ttl=3600, show_spinner=False)
def nfl_summary(event_id):
    resp = requests.get(f'{BASE}/summary', params={'event':str(event_id)}, timeout=15)
    resp.raise_for_status()
    return resp.json()

def _number(x):
    try:
        if isinstance(x, dict): x=x.get('value',x.get('displayValue'))
        if isinstance(x, str): x=x.replace(',','').strip().split('-')[0]
        v=float(x)
        return v if math.isfinite(v) else None
    except (ValueError,TypeError):return None

def _match(event):
    cs=(event.get('competitions') or [{}])[0].get('competitors') or []
    home=next((c for c in cs if c.get('homeAway')=='home'),None)
    away=next((c for c in cs if c.get('homeAway')=='away'),None)
    if not home or not away: return None
    status=(event.get('status') or {}).get('type') or {}
    return home,away,bool(status.get('completed'))

def _id(t): return str((t.get('team') or {}).get('id') or '')

def _start(ev):
    try: return datetime.fromisoformat(str(ev.get('date')).replace('Z','+00:00')).astimezone(timezone.utc)
    except (ValueError,TypeError): return None

def _observations(events,team_id,cutoff,event_id):
    rows=[]
    for ev in events:
        start=_start(ev)
        if start is None or start >= cutoff or str(ev.get('id')) == str(event_id): continue
        result=_match(ev)
        if not result: continue
        h,a,done=result
        if not done:continue
        hs,aws=_number(h.get('score')),_number(a.get('score'))
        if hs is None or aws is None:continue
        if _id(h)==team_id:rows.append({'event':str(ev.get('id')),'date':start,'pf':hs,'pa':aws})
        elif _id(a)==team_id:rows.append({'event':str(ev.get('id')),'date':start,'pf':aws,'pa':hs})
    return sorted(rows,key=lambda x:x['date'],reverse=True)[:10]

def simulate_nfl(home,away,seed,iterations=10000):
    """Puntos de equipo: mezcla ataque/defensa; dispersión empírica de resultados.
    NO confundir con modelización completa de jugadas ni pronóstico calibrado.
    """
    if min(len(home),len(away))<4:return None
    mean=lambda rows,key: sum(x[key] for x in rows)/len(rows)
    ph=max(1.,.57*mean(home,'pf')+.43*mean(away,'pa') + 1.0)
    pa=max(1.,.57*mean(away,'pf')+.43*mean(home,'pa'))
    std=lambda rows: max(6.,statistics.pstdev(x['pf'] for x in rows))
    sh=max(6.,.5*(std(home)+statistics.pstdev(x['pa'] for x in away)))
    sa=max(6.,.5*(std(away)+statistics.pstdev(x['pa'] for x in home)))
    rng=random.Random(seed)
    hw=aw=ties=over=0
    hp=ap=0
    # Correlación modesta por condiciones compartidas del encuentro.
    for _ in range(iterations):
        common=rng.gauss(0,2.0)
        x=max(0,round(rng.gauss(ph,sh)+common))
        y=max(0,round(rng.gauss(pa,sa)+common))
        hp+=x;ap+=y
        hw+=x>y;aw+=y>x;ties+=x==y
        over+=(x+y)>43.5
    return {'home':hp/iterations,'away':ap/iterations,'win_h':hw/iterations*100,
            'win_a':aw/iterations*100,'draw':ties/iterations*100,
            'over_43_5':over/iterations*100,'samples':iterations,
            'n_h':len(home),'n_a':len(away)}

# ESPN returns names/abbreviations that vary by season: tolerate aliases.
STAT_KEYS={
    'Yardas totales':('totalyards','totalyardage','totaloffensiveyards'),
    'Yardas por pase':('netpassingyards','passingyards','netpassyards'),
    'Yardas terrestres':('rushingyards','rushingyard'),
    'Primeros downs':('firstdowns','totalfirstdowns'),
    'Pérdidas de balón':('turnovers','totalturnovers'),
}
def _normalize(s):return ''.join(ch for ch in str(s).lower() if ch.isalnum())

def _box_team_stats(payload,team_id):
    teams=((payload.get('boxscore') or {}).get('teams') or [])
    for row in teams:
        if str((row.get('team') or {}).get('id') or '')!=team_id:continue
        stats={}
        for s in (row.get('statistics') or []):
            label=_normalize(s.get('name') or s.get('abbreviation') or s.get('label'))
            n=_number(s.get('displayValue',s.get('value')))
            if label and n is not None:stats[label]=n
        return stats
    return {}

def nfl_metrics(games,team_id):
    out={label:[] for label in STAT_KEYS}
    for game in games[:7]:
        try: stats=_box_team_stats(nfl_summary(game['event']),team_id)
        except (requests.RequestException,ValueError,TypeError,KeyError):continue
        for label,aliases in STAT_KEYS.items():
            val=next((stats[_normalize(a)] for a in aliases if _normalize(a) in stats),None)
            if val is not None and val>=0:out[label].append(val)
    return {k:sum(v)/len(v) for k,v in out.items() if len(v)>=3}

def render_nfl(match,day):
    """One match. Separate NFL path; never render soccer xG/cards/corners."""
    def name(c):return (c.get('team') or {}).get('displayName') or (c.get('team') or {}).get('name') or 'Equipo'
    h,a=match['home'],match['away']
    st.markdown('#### 🏈 NFL Intelligence · Modelo especializado')
    st.caption('Proyección experimental con 10,000 simulaciones. No utiliza xG ni estadísticas de fútbol.')
    cutoff=_start({'date':match.get('date')})
    if cutoff is None:
        st.info('No se dispone de la hora de inicio verificable del partido.')
        return
    if match.get('completed') or match.get('state')=='in':
        st.info('Análisis retrospectivo: el modelo solo utiliza partidos anteriores al encuentro; no es una predicción publicada antes del inicio.')
    try:
        history=nfl_past_events(cutoff.date().isoformat())
    except (requests.RequestException,ValueError) as exc:
        st.warning('ESPN NFL no respondió. No se inventarán estadísticas.')
        return
    hid,aid=_id(h),_id(a)
    if not hid or not aid:
        st.info('Sin identificadores verificables de los equipos.')
        return
    hg=_observations(history,hid,cutoff,match['id'])
    ag=_observations(history,aid,cutoff,match['id'])
    seed=sum((i+1)*ord(ch) for i,ch in enumerate(str(match['id'])))
    pred=simulate_nfl(hg,ag,seed)
    if pred is None:
        st.info(f'Historial NFL insuficiente: {name(h)} {len(hg)}/4; {name(a)} {len(ag)}/4 partidos. No se mostrarán pronósticos ficticios.')
        return
    c1,c2,c3=st.columns(3)
    c1.metric('Local',f"{pred['win_h']:.1f}%")
    c2.metric('Empate',f"{pred['draw']:.1f}%")
    c3.metric('Visitante',f"{pred['win_a']:.1f}%")
    x,y=pred['home'],pred['away']
    st.markdown(f"**Puntos esperados:** {name(h)} {x:.1f} · {name(a)} {y:.1f}")
    st.caption(f"Más de 43.5 puntos totales: {pred['over_43_5']:.1f}% · Historial {pred['n_h']} y {pred['n_a']} encuentros")
    st.markdown('**Estadísticas NFL proyectadas (si están disponibles)**')
    hm,am=nfl_metrics(hg,hid),nfl_metrics(ag,aid)
    displayed=0
    for label in STAT_KEYS:
        if label in hm and label in am:
            displayed+=1
            c1,c2=st.columns(2)
            c1.metric(f'{label} · {name(h)}',f'{hm[label]:.1f}')
            c2.metric(f'{label} · {name(a)}',f'{am[label]:.1f}')
    if not displayed:st.caption('No hay suficientes boxscores verificados para proyectar yardas, primeros downs o entregas de balón.')
    st.caption('Puntos simulados mediante distribución normal ajustada a resultados previos y mezcla ataque/defensa. Las métricas adicionales son medias históricas, NO 10,000 simulaciones individuales. Fuente ESPN no oficial; cobertura variable. No es consejo de apuestas.')
