"""NYUZ Model Lab 3.0: evaluation and immutable prematch ledger viewer.
This module intentionally never generates historical 'verified' forecasts.
"""
import csv
import io
import json
import sqlite3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import requests
import streamlit as st


def _rows(db_path, cloud_url, cloud_key, limit=250):
    if cloud_url and cloud_key:
        try:
            r = requests.get(cloud_url.rstrip('/') + '/rest/v1/predictions',
                headers={'apikey':cloud_key,'Authorization':'Bearer '+cloud_key},
                params={'select':'sport,league,event_id,created_utc,kickoff_utc,model_version,payload',
                        'order':'created_utc.desc','limit':str(limit)},timeout=12)
            r.raise_for_status()
            return r.json(), None
        except (requests.RequestException,ValueError) as exc:
            return [], f'No se pudo consultar el historial persistente: {exc}'
    try:
        with sqlite3.connect(db_path, timeout=5) as db:
            db.row_factory=sqlite3.Row
            result=[dict(r) for r in db.execute(
                'SELECT sport,league,event_id,created_utc,kickoff_utc,model_version,payload FROM predictions ORDER BY created_utc DESC LIMIT ?', (limit,))]
        return result, 'Almacenamiento local temporal: Streamlit Cloud puede borrar este historial al reiniciar. Configura Supabase para conservarlo.'
    except (sqlite3.Error,OSError):
        return [], 'Todavía no existen predicciones guardadas en esta instancia.'


def _utc(s):
    return datetime.fromisoformat(str(s).replace('Z','+00:00')).astimezone(ZoneInfo('UTC'))


def render_history(db_path, cloud_url, cloud_key, get_events, parse_event, numeric_score):
    st.markdown('<div id="ny-historial"></div>',unsafe_allow_html=True)
    with st.expander('Historial verificable · Predicciones originales',expanded=False):
        st.caption('Solo registros capturados antes del inicio. No se crean pronósticos retroactivos.')
        rows, notice = _rows(db_path,cloud_url,cloud_key)
        if notice: st.info(notice)
        valid=[]
        for r in rows:
            try:
                payload=r['payload'] if isinstance(r['payload'],dict) else json.loads(r['payload'])
                created,kickoff=_utc(r['created_utc']),_utc(r['kickoff_utc'])
                if created >= kickoff: continue
                valid.append({**r,'payload':payload,'created':created,'kickoff':kickoff})
            except (ValueError,TypeError,KeyError):
                continue
        st.metric('Pronósticos previos al inicio registrados',len(valid))
        if not valid:
            st.caption('Las predicciones aparecerán aquí después de capturarse antes de cada partido. La captura automática requiere visitas o una tarea programada.')
            return
        league_options=sorted(set(r['league'] for r in valid))
        league=st.selectbox('Competición', ['Todas']+league_options,key='ny_lab3_league')
        selected=[r for r in valid if league=='Todas' or r['league']==league]
        # Query actual results only for a small number of unique dates/leagues.
        lookup={}
        queries={(r['sport'],r['league'],r['kickoff'].date()) for r in selected[:40]}
        for sport,lg,day in list(queries)[:16]:
            try:
                for raw in get_events(sport,lg,day):
                    m=parse_event(raw)
                    if m: lookup[(sport,lg,str(m['id']))]=m
            except (requests.RequestException,ValueError,KeyError):
                continue
        display=[]; scored=0; correct=0; brier=[]
        for r in selected:
            p=r['payload']; m=lookup.get((r['sport'],r['league'],str(r['event_id'])))
            actual='Pendiente / no consultado'; verdict='—'
            probs=p.get('probabilities',{}) if isinstance(p,dict) else {}
            if m and m.get('completed'):
                hs,aws=numeric_score(m['home']),numeric_score(m['away'])
                if hs is not None and aws is not None:
                    actual=f'{hs:g}–{aws:g}'
                    if r['sport']=='soccer' and all(k in probs for k in ('home','draw','away')):
                        try:
                            v=[float(probs[k]) for k in ('home','draw','away')]
                            if max(v)>1: v=[x/100 for x in v]
                            if all(0<=x<=1 for x in v) and abs(sum(v)-1)<.03:
                                idx=0 if hs>aws else (1 if hs==aws else 2)
                                correct+=int(v.index(max(v))==idx); scored+=1
                                brier.append(sum((v[i]-int(i==idx))**2 for i in range(3))/3)
                                verdict='Acertó' if v.index(max(v))==idx else 'Falló'
                        except (ValueError,TypeError): pass
            display.append({'Fecha':r['kickoff'].strftime('%Y-%m-%d'),
                'Partido':f"{p.get('home','?')} vs {p.get('away','?')}",
                'Liga':r['league'],'Pronóstico registrado':r['created'].strftime('%Y-%m-%d %H:%M UTC'),
                'Resultado':actual,'Favorito 1X2':verdict,'Modelo':r.get('model_version','')})
        if scored:
            c1,c2=st.columns(2)
            c1.metric('Acierto 1X2 verificado',f'{correct/scored:.1%}')
            c2.metric('Brier medio (3 clases)',f'{sum(brier)/len(brier):.3f}')
            st.caption(f'Muestra: {scored} partidos finalizados con resultado y probabilidades válidas. Menor Brier es mejor; no equivale a precisión garantizada.')
        else:
            st.caption('Aún no hay suficientes resultados verificables para calcular precisión. Los partidos no consultados no se cuentan como fallos.')
        st.dataframe(display,hide_index=True,use_container_width=True)
        out=io.StringIO(); writer=csv.DictWriter(out,fieldnames=list(display[0]));writer.writeheader();writer.writerows(display)
        st.download_button('Exportar historial CSV',out.getvalue().encode('utf-8-sig'),file_name='nyuz_historial_verificable.csv',mime='text/csv',key='ny_lab3_csv')


def render_lab3_metrics(rows):
    """Supplement existing walk-forward evaluation with out-of-sample metrics."""
    if not rows or len(rows)<15:return
    split=max(1,int(len(rows)*.8)); test=rows[split:]
    st.markdown('#### Model Lab 3.0 · Diagnóstico fuera de muestra')
    st.caption('Prueba cronológica final del backtest. Estos son pronósticos reconstruidos, no registros publicados previamente.')
    for key,name in [('base','Promedio simple'),('candidate','Forma ponderada')]:
        errors=[]; winner=0; totals=[]
        for r in test:
            ph,pa=float(r[key+'_home']),float(r[key+'_away'])
            ah,aa=float(r['actual_home']),float(r['actual_away'])
            errors.extend([ph-ah,pa-aa]); totals.append(abs(ph+pa-ah-aa))
            winner+=int((ph>pa)==(ah>aa)) if ah!=aa else 0
        mae=sum(abs(e) for e in errors)/len(errors)
        rmse=(sum(e*e for e in errors)/len(errors))**.5
        st.markdown(f'**{name}** · MAE {mae:.2f} pts · RMSE {rmse:.2f} pts · Error total {sum(totals)/len(totals):.2f} pts')
    st.caption('No se elige ni despliega automáticamente el modelo ganador: primero se necesita una muestra independiente mayor y validación de calibración.')
