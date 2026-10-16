import copy
import unittest
import radar

class RadarTests(unittest.TestCase):
    def test_reproducible(self):
        self.assertEqual(radar.generate(), radar.generate())
        self.assertNotEqual(radar.generate(42), radar.generate(43))

    def test_invalid_inputs(self):
        rows, _ = radar.generate()
        with self.assertRaises(ValueError): radar.validate([])
        with self.assertRaises(ValueError): radar.validate(rows + [rows[0]])
        for key, value in [('units', 0), ('fee_cents', -1), ('unit_cost_cents', -1), ('failure_pct', 100), ('units', 1.5), ('category', 'X'), ('date', 'invalid')]:
            bad = copy.deepcopy(rows); bad[0][key] = value
            with self.assertRaises(ValueError): radar.validate(bad)

    def test_accounting(self):
        row = dict(id='x', date='2026-01-01', category='Transferências', units=100, fee_cents=100, failure_pct=10, unit_cost_cents=50)
        result = radar.aggregate([row])[0]
        self.assertEqual(result['successful'], 90)
        self.assertEqual(result['revenue_cents'], 9000)
        self.assertEqual(result['profit_cents'], 4000)
        self.assertAlmostEqual(result['margin'], 4000/9000)

    def test_no_future_leakage(self):
        raw, _ = radar.generate()
        rows = radar.aggregate(raw)
        prefix = rows[:300]
        before = radar.detect(prefix)
        future = copy.deepcopy(rows[300:])
        for r in future: r['margin'] = -100
        after = radar.detect(prefix + future)
        ids = {r['id'] for r in prefix}
        self.assertEqual(before, [r for r in after if r['id'] in ids])

    def test_warmup_and_known_anomalies(self):
        raw, truth = radar.generate()
        rows = radar.aggregate(raw)
        alerts = radar.detect(rows)
        self.assertTrue(all(int(r['id'].split('-')[0]) >= 28 for r in alerts))
        m = radar.evaluate(rows, alerts, truth)
        self.assertEqual((m['true_positives'],m['false_positives'],m['false_negatives']), (12,0,0))

    def test_normal_series(self):
        rows = [dict(id=str(i), date=f'{i:03}', category='Transferências', margin=.3, units=25) for i in range(60)]
        self.assertEqual(radar.detect(rows), [])

if __name__ == '__main__': unittest.main()
