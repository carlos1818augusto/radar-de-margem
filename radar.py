"""Radar de Margem: demo sintética, determinística e sem dependências externas."""
import argparse
import csv
import hashlib
import json
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parent

def generate(seed=42, days=180):
    rng = random.Random(seed)
    rows, truth = [], []
    for day in range(days):
        for category, price, cost in [('Casa', 12000, 7000), ('Tecnologia', 25000, 17000), ('Esporte', 18000, 10000)]:
            units = rng.randint(18, 38)
            discount = rng.randint(2, 8)
            actual_cost = cost + rng.randint(-200, 200)
            scenario = ''
            if day in (65, 95, 125, 155) and category == 'Casa':
                discount, scenario = 32, 'desconto excessivo'
            if day in (75, 105, 135, 165) and category == 'Tecnologia':
                actual_cost, scenario = int(cost * 1.4), 'aumento de custo'
            if day in (85, 115, 145, 175) and category == 'Esporte':
                units, scenario = 3, 'queda de volume'
            row = dict(id=f'{day:03}-{category}', date=str(date(2026, 1, 1)+timedelta(days=day)), category=category, units=units, price_cents=price, discount_pct=discount, unit_cost_cents=actual_cost)
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
        if r['category'] not in ('Casa', 'Tecnologia', 'Esporte'):
            raise ValueError('Categoria inválida')
        for key in ('units', 'price_cents', 'unit_cost_cents', 'discount_pct'):
            if type(r[key]) is not int:
                raise ValueError('Campo deve ser inteiro: '+key)
        if r['units'] <= 0 or r['price_cents'] <= 0 or r['unit_cost_cents'] < 0 or not 0 <= r['discount_pct'] < 100:
            raise ValueError('Valor fora do domínio')

def aggregate(rows):
    db = sqlite3.connect(':memory:')
    db.execute('CREATE TABLE sales (id TEXT PRIMARY KEY, date TEXT, category TEXT, units INTEGER, price_cents INTEGER, discount_pct INTEGER, unit_cost_cents INTEGER)')
    db.executemany('INSERT INTO sales VALUES (:id,:date,:category,:units,:price_cents,:discount_pct,:unit_cost_cents)', rows)
    db.row_factory = sqlite3.Row
    result = [dict(r) for r in db.execute('''SELECT id, date, category, units, discount_pct,
        CAST(ROUND(units * price_cents * (100-discount_pct)/100.0) AS INTEGER) revenue_cents,
        units * unit_cost_cents cost_cents FROM sales ORDER BY date, category''')]
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
    canonical = json.dumps(raw, sort_keys=True, ensure_ascii=False).encode()
    report = dict(seed=42, data_sha256=hashlib.sha256(canonical).hexdigest(), **metrics)
    for name, data in [('sales',raw), ('ground_truth',truth), ('alerts',alerts)]:
        with (output / (name+'.csv')).open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(data[0]), lineterminator='\n'); writer.writeheader(); writer.writerows(data)
    (output/'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    payload = json.dumps(dict(rows=rows, alerts=alerts, report=report), ensure_ascii=False).replace('<', '\\u003c')
    template = (ROOT/'dashboard.html').read_text(encoding='utf-8')
    (output/'index.html').write_text(template.replace('__DATA__', payload), encoding='utf-8')
    print(json.dumps(report, indent=2))
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'demo')
    run(parser.parse_args().output)
