"""NYUZ Model Lab 3.2: original pre-match snapshots + persisted post-match evaluation.
Historical forecasts are never retroactively invented or rewritten.
"""
import csv
import io
import json
import math
import sqlite3
from datetime import datetime, timezone
import requests
import streamlit as st


METRIC_LABELS = {
    'goals': 'Goles', 'shots': 'Tiros', 'sot': 'Tiros a puerta',
    'corners': 'Córners', 'yellow': 'Amarillas', 'fouls': 'Faltas',
}


def _utc(value):
    dt = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    if dt.tzinfo is None:
        raise ValueError('Missing timezone')
    return dt.astimezone(timezone.utc)


def _rows(db_path, cloud_url, cloud_key, limit=500):
    if cloud_url and cloud_key:
        try:
            response = requests.get(cloud_url.rstrip('/') + '/rest/v1/predictions',
                headers={'apikey': cloud_key, 'Authorization': 'Bearer ' + cloud_key},
                params={'select': 'sport,league,event_id,created_utc,kickoff_utc,model_version,payload',
                        'order': 'created_utc.desc', 'limit': str(limit)}, timeout=15)
            response.raise_for_status()
            return response.json(), None
        except (requests.RequestException, ValueError) as exc:
            return [], f'No se pudo consultar el historial persistente ({type(exc).__name__}).'
    try:
        with sqlite3.connect(db_path, timeout=5) as db:
            db.row_factory = sqlite3.Row
            result = [dict(r) for r in db.execute(
                'SELECT sport,league,event_id,created_utc,kickoff_utc,model_version,payload FROM predictions ORDER BY created_utc DESC LIMIT ?', (limit,))]
        return result, 'Almacenamiento local temporal: Streamlit Cloud puede borrar este historial al reiniciar.'
    except (sqlite3.Error, OSError):
        return [], 'Todavía no existen predicciones guardadas en esta instancia.'


def _evaluations(cloud_url, cloud_key, limit=1000):
    if not cloud_url or not cloud_key:
        return [], 'Para mostrar evaluaciones persistentes necesitas Supabase.'
    try:
        response = requests.get(cloud_url.rstrip('/') + '/rest/v1/nyuz_evaluaciones',
            headers={'apikey': cloud_key, 'Authorization': 'Bearer ' + cloud_key},
            params={'select': 'sport,league,event_id,evaluated_utc,actual_home,actual_away,actual_metrics,errors,outcome,source',
                    'order': 'evaluated_utc.desc', 'limit': str(limit)}, timeout=15)
        response.raise_for_status()
        return response.json(), None
    except requests.RequestException as exc:
        status = getattr(getattr(exc, 'response', None), 'status_code', None)
        if status in (400, 404):
            return [], 'Falta crear la tabla nyuz_evaluaciones. Ejecuta el SQL incluido en el paquete 3.2.'
        return [], f'No se pudieron consultar las evaluaciones ({type(exc).__name__}).'
    except ValueError:
        return [], 'La respuesta de Supabase no contiene evaluaciones válidas.'


def _num(value):
    try:
        n = float(value)
        return n if math.isfinite(n) else None
    except (TypeError, ValueError):
        return None


def render_history(db_path, cloud_url, cloud_key, get_events=None, parse_event=None, numeric_score=None):
    st.markdown('<div id="ny-historial"></div>', unsafe_allow_html=True)
    with st.expander('Historial verificable · Predicciones originales', expanded=False):
        st.caption('Pronósticos registrados antes del inicio. Resultados y evaluaciones se guardan por separado; nunca se fabrican predicciones retroactivas.')
        rows, notice = _rows(db_path, cloud_url, cloud_key)
        if cloud_url and cloud_key and not notice:
            st.success('Supabase conectado · Historial persistente activo')
        if notice:
            st.info(notice)
        valid = []
        for r in rows:
            try:
                payload = r['payload'] if isinstance(r['payload'], dict) else json.loads(r['payload'])
                created, kickoff = _utc(r['created_utc']), _utc(r['kickoff_utc'])
                if created >= kickoff or not isinstance(payload, dict):
                    continue
                valid.append({**r, 'payload': payload, 'created': created, 'kickoff': kickoff})
            except (ValueError, TypeError, KeyError):
                continue
        st.metric('Pronósticos previos al inicio registrados', len(valid))
        if not valid:
            st.caption('Aún no hay registros válidos. La captura automática se ejecuta mediante GitHub Actions.')
            return
        leagues = sorted({r['league'] for r in valid})
        league = st.selectbox('Competición', ['Todas'] + leagues, key='ny_lab3_league')
        selected = [r for r in valid if league == 'Todas' or r['league'] == league]
        evaluated, error = _evaluations(cloud_url, cloud_key)
        if error:
            st.info(error)
        by_id = {(r['sport'], r['league'], str(r['event_id'])): r for r in evaluated}
        combined = []
        metric_abs = {}
        metric_sq = {}
        correct = []
        brier = []
        log_loss = []
        for r in selected:
            p = r['payload']
            ev = by_id.get((r['sport'], r['league'], str(r['event_id'])))
            outcome = (ev or {}).get('outcome') or {}
            if isinstance(outcome, str):
                try:
                    outcome = json.loads(outcome)
                except ValueError:
                    outcome = {}
            actual = 'Pendiente de evaluación'
            verdict = '—'
            if ev:
                ah, aa = _num(ev.get('actual_home')), _num(ev.get('actual_away'))
                if ah is not None and aa is not None:
                    actual = f'{ah:g} – {aa:g}'
                if isinstance(outcome, dict) and isinstance(outcome.get('correct'), bool):
                    is_correct = outcome['correct']
                    correct.append(is_correct)
                    verdict = 'Acertó' if is_correct else 'Falló'
                    b = _num(outcome.get('brier'))
                    ll = _num(outcome.get('log_loss'))
                    if b is not None:
                        brier.append(b)
                    if ll is not None:
                        log_loss.append(ll)
                errors = ev.get('errors') or {}
                if isinstance(errors, str):
                    try:
                        errors = json.loads(errors)
                    except ValueError:
                        errors = {}
                if isinstance(errors, dict):
                    for name, values in errors.items():
                        if not isinstance(values, list):
                            continue
                        for value in values:
                            n = _num(value)
                            if n is not None:
                                metric_abs.setdefault(name, []).append(abs(n))
                                metric_sq.setdefault(name, []).append(n*n)
            combined.append({
                'Fecha': r['kickoff'].strftime('%Y-%m-%d'),
                'Partido': f"{p.get('home','?')} vs {p.get('away','?')}",
                'Liga': r['league'],
                'Pronóstico registrado': r['created'].strftime('%Y-%m-%d %H:%M UTC'),
                'Resultado real': actual,
                'Favorito 1X2': verdict,
                'Modelo': r.get('model_version', ''),
            })
        st.markdown('#### NYUZ Auto-Evaluation 1.0')
        evaluated_count = sum('Pendiente' not in r['Resultado real'] for r in combined)
        c1, c2 = st.columns(2)
        c1.metric('Partidos evaluados', evaluated_count)
        c2.metric('Pendientes', len(combined) - evaluated_count)
        if correct:
            c1, c2 = st.columns(2)
            c1.metric('Acierto 1X2', f'{sum(correct)/len(correct):.1%}')
            if brier:
                c2.metric('Brier medio (3 clases)', f'{sum(brier)/len(brier):.3f}')
            st.caption(f'1X2: {len(correct)} encuentros con probabilidades válidas. El Brier menor es mejor; no representa garantía de acierto.')
        else:
            st.caption('La precisión 1X2 aparecerá cuando haya partidos finalizados y evaluados con probabilidades válidas.')
        if metric_abs:
            st.markdown('**Errores de estadísticas proyectadas**')
            st.dataframe([{
                'Estadística': METRIC_LABELS.get(k, k), 'Valores comparados': len(metric_abs[k]),
                'MAE': round(sum(metric_abs[k])/len(metric_abs[k]), 3),
                'RMSE': round(math.sqrt(sum(metric_sq[k])/len(metric_sq[k])), 3),
            } for k in METRIC_LABELS if k in metric_abs], hide_index=True, use_container_width=True)
            st.caption('Solo se comparan estadísticas que ESPN realmente proporciona. Las ausentes no se convierten en ceros.')
        st.dataframe(combined, hide_index=True, use_container_width=True)
        out = io.StringIO()
        writer = csv.DictWriter(out, fieldnames=list(combined[0]))
        writer.writeheader()
        writer.writerows(combined)
        st.download_button('Exportar historial y resultados CSV', out.getvalue().encode('utf-8-sig'),
                           file_name='nyuz_historial_evaluado.csv', mime='text/csv', key='ny_lab3_csv')
        st.caption('Las evaluaciones son registros operativos de una fuente externa; todavía no constituyen una auditoría criptográfica inmutable.')


def render_lab3_metrics(rows):
    """Supplement existing walk-forward NBA evaluation with out-of-sample metrics."""
    if not rows or len(rows) < 15:
        return
    split = max(1, int(len(rows)*.8))
    test = rows[split:]
    st.markdown('#### Model Lab 3.0 · Diagnóstico fuera de muestra')
    st.caption('Prueba cronológica final del backtest. Pronósticos reconstruidos, no registros publicados previamente.')
    for key, name in [('base', 'Promedio simple'), ('candidate', 'Forma ponderada')]:
        errors = []
        totals = []
        for r in test:
            ph, pa = float(r[key+'_home']), float(r[key+'_away'])
            ah, aa = float(r['actual_home']), float(r['actual_away'])
            errors.extend([ph-ah, pa-aa])
            totals.append(abs(ph+pa-ah-aa))
        mae = sum(abs(e) for e in errors)/len(errors)
        rmse = (sum(e*e for e in errors)/len(errors))**.5
        st.markdown(f'**{name}** · MAE {mae:.2f} pts · RMSE {rmse:.2f} pts · Error total {sum(totals)/len(totals):.2f} pts')
    st.caption('No se despliega automáticamente el modelo ganador: requiere más validación independiente.')
