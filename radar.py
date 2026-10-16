"""Radar de Margem: demo sintética, determinística e sem dependências externas."""
import argparse
import csv
import hashlib
import json
import random
import math
import sqlite3
from datetime import date, timedelta
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parent

def stable_numbers(value):
    """Quantize serialized floats to avoid irrelevant last-bit OS math differences."""
    if isinstance(value, float):
        return round(value, 6)
    if isinstance(value, list):
        return [stable_numbers(item) for item in value]
    if isinstance(value, dict):
        return {key: stable_numbers(item) for key, item in value.items()}
    return value

def generate(seed=42, days=180):
    rng = random.Random(seed)
    rows, truth = [], []
    for day in range(days):
        for category, price, cost in [('Transferências', 120, 70), ('Cobranças', 250, 170), ('Cartões', 180, 100)]:
            base = {'Transferências': 2700, 'Cobranças': 2300, 'Cartões': 3000}[category]
            units = max(1, round(base + 500*math.sin(2*math.pi*day/7) + 3.5*day + rng.randint(-300, 300)))
            discount = rng.randint(0, 3)
            actual_cost = cost + rng.randint(-2, 2)
            scenario = ''
            if day in (65, 95, 125, 155) and category == 'Transferências':
                discount, scenario = 25, 'pico de falhas'
            if day in (75, 105, 135, 165) and category == 'Cobranças':
                actual_cost, scenario = int(cost * 1.8), 'aumento de custo'
            if day in (85, 115, 145, 175) and category == 'Cartões':
                units, scenario = 300, 'queda de volume'
            row = dict(id=f'{day:03}-{category}', date=str(date(2026, 1, 1)+timedelta(days=day)), category=category, units=units, fee_cents=price, failure_pct=discount, unit_cost_cents=actual_cost)
            rows.append(row)
            if scenario:
                truth.append(dict(id=row['id'], scenario=scenario))
    return rows, truth

def validate(rows):
    if not rows:
        raise ValueError('Base vazia')
    seen, groups = set(), set()
    for r in rows:
        if r['id'] in seen or (r['date'], r['category']) in groups:
            raise ValueError('Chave duplicada')
        seen.add(r['id']); groups.add((r['date'], r['category']))
        date.fromisoformat(r['date'])
        if r['category'] not in ('Transferências', 'Cobranças', 'Cartões'):
            raise ValueError('Categoria inválida')
        for key in ('units', 'fee_cents', 'unit_cost_cents', 'failure_pct'):
            if type(r[key]) is not int:
                raise ValueError('Campo deve ser inteiro: '+key)
        if r['units'] <= 0 or r['fee_cents'] <= 0 or r['unit_cost_cents'] < 0 or not 0 <= r['failure_pct'] < 100:
            raise ValueError('Valor fora do domínio')

def aggregate(rows):
    db = sqlite3.connect(':memory:')
    db.execute('CREATE TABLE operations (id TEXT PRIMARY KEY, date TEXT, category TEXT, units INTEGER, fee_cents INTEGER, failure_pct INTEGER, unit_cost_cents INTEGER)')
    db.executemany('INSERT INTO operations VALUES (:id,:date,:category,:units,:fee_cents,:failure_pct,:unit_cost_cents)', rows)
    db.row_factory = sqlite3.Row
    result = [dict(r) for r in db.execute('''SELECT id, date, category, units, failure_pct,
        CAST(ROUND(units * (100-failure_pct)/100.0) AS INTEGER) successful,
        CAST(ROUND(units * (100-failure_pct)/100.0) AS INTEGER) * fee_cents revenue_cents,
        units * unit_cost_cents cost_cents FROM operations ORDER BY date, category''')]
    db.close()
    for r in result:
        r['profit_cents'] = r['revenue_cents'] - r['cost_cents']
        r['margin'] = r['profit_cents'] / r['revenue_cents']
    return result

def detect(rows, window=28):
    history, alerts = {}, []
    for r in sorted(rows, key=lambda x: (x['date'], x['category'])):
        past = history.setdefault(r['category'], [])
        if len(past) >= window:
            sample = past[-window:]
            baseline = median(x['margin'] for x in sample)
            mad = median(abs(x['margin']-baseline) for x in sample)
            limit = max(0.08, 4 * 1.4826 * mad)
            volume = median(x['units'] for x in sample)
            reasons = []
            failure_baseline=median(x.get('failure_pct',0) for x in sample)
            if r.get('failure_pct',0)-failure_baseline>5:
                reasons.append(f'Falhas {r["failure_pct"]}%; mediana anterior {failure_baseline:g}%; alta acima de 5 p.p.')
            if baseline-r['margin'] > limit:
                reasons.append(f'Margem {r["margin"]:.1%}; mediana anterior {baseline:.1%}; queda acima de {limit*100:.1f} p.p.')
            if r['units'] < volume * 0.45:
                reasons.append(f'Volume {r["units"]}; mediana anterior {volume:g}; abaixo de 45% da referência')
            if reasons:
                alerts.append(dict(**r, reasons=reasons, baseline_margin=baseline, baseline_units=volume))
        past.append(r)
    return alerts

def evaluate(rows, alerts, truth):
    eligible = {r['id'] for r in rows if int(r['id'].split('-')[0]) >= 28}
    expected = {r['id'] for r in truth} & eligible
    found = {r['id'] for r in alerts} & eligible
    tp, fp, fn = len(found & expected), len(found-expected), len(expected-found)
    return dict(rows=len(rows), evaluated_rows=len(eligible), warmup_rows=len(rows)-len(eligible), injected=len(expected), alerts=len(found), true_positives=tp, false_positives=fp, false_negatives=fn, precision=tp/(tp+fp) if tp+fp else None, recall=tp/(tp+fn) if tp+fn else None)

def run(output):
    output.mkdir(parents=True, exist_ok=True)
    raw, truth = generate()
    validate(raw)
    rows = aggregate(raw)
    alerts = detect(rows)
    metrics = evaluate(rows, alerts, truth)
    from forecasting import backtest, future_forecasts
    predictions, scores = backtest(rows)
    future = future_forecasts(rows)
    canonical = json.dumps(raw, sort_keys=True, ensure_ascii=False).encode()
    report = dict(seed=42, data_sha256=hashlib.sha256(canonical).hexdigest(), **metrics)
    for name, data in [('transactions',raw), ('ground_truth',truth), ('alerts',alerts)]:
        data = stable_numbers(data)
        with (output / (name+'.csv')).open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(data[0]), lineterminator='\n'); writer.writeheader(); writer.writerows(data)
    (output/'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    quality = dict(status='aprovado', rows=len(raw), unique_keys=len({r['id'] for r in raw}), categories=3, days=180, missing_cells=sum(v is None for r in raw for v in r.values()), checks=['Base não vazia','Chave única','Categoria/data única','Tipos inteiros','Domínio monetário e falhas','Datas ISO válidas'], data_sha256=report['data_sha256'])
    for name, data in [('backtest',predictions),('forecast_metrics',scores),('future_forecast',future)]:
        data = stable_numbers(data)
        with (output/(name+'.csv')).open('w',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=list(data[0]),lineterminator='\n');writer.writeheader();writer.writerows(data)
    (output/'quality.json').write_text(json.dumps(quality,indent=2,ensure_ascii=False),encoding='utf-8')
    payload = json.dumps(stable_numbers(dict(rows=rows, raw=raw, alerts=alerts, report=report, quality=quality, forecasts=predictions, scores=scores, future=future)), ensure_ascii=False).replace('<', '\\u003c')
    template = (ROOT/'dashboard.html').read_text(encoding='utf-8')
    scripts = '<script>'+ (ROOT/'scenario.js').read_text(encoding='utf-8') + '</script><script>'+ (ROOT/'advanced.js').read_text(encoding='utf-8') + '</script>'
    template = template.replace('</html>', scripts+'</html>')
    (output/'index.html').write_text(template.replace('__DATA__', payload), encoding='utf-8')
    print(json.dumps(report, indent=2))
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'demo')
    run(parser.parse_args().output)
