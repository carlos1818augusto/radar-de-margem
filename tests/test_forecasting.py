import copy
import unittest
from forecasting import MODELS, predict, backtest, interval_radius, metrics, solve
import radar

class ForecastTests(unittest.TestCase):
    def test_solver(self):
        x=solve([[3,2],[1,2]],[7,5])
        self.assertAlmostEqual(x[0],1); self.assertAlmostEqual(x[1],2)

    def test_seasonal_baseline(self):
        history=[10,20,30,40,50,60,70]*8
        self.assertEqual(predict(history,14,MODELS[0]),history[-14:])
        self.assertEqual(interval_radius(history,MODELS[0]),0)

    def test_temporal_isolation(self):
        raw,_=radar.generate();rows=radar.aggregate(raw)
        before,_=backtest(rows)
        changed=copy.deepcopy(rows)
        cutoff=sorted({r['date'] for r in rows})[84]
        for r in changed:
            if r['date']>=cutoff:r['units']=9999
        after,_=backtest(changed)
        for a,b in zip([r for r in before if r['origin']==84],[r for r in after if r['origin']==84]):
            self.assertEqual((a['prediction'],a['lower'],a['upper']),(b['prediction'],b['lower'],b['upper']))
            self.assertLess(a['train_end'],a['date'])

    def test_metrics_by_hand(self):
        m=metrics([dict(actual=10,prediction=12,lower=8,upper=14),dict(actual=20,prediction=16,lower=14,upper=18)])
        self.assertEqual(m['mae'],3);self.assertEqual(m['wape'],.2)
        self.assertEqual(m['bias'],-1);self.assertEqual(m['coverage'],.5)

    def test_backtest_dimensions(self):
        raw,_=radar.generate();p,s=backtest(radar.aggregate(raw))
        self.assertEqual(len(p),3*3*2*28);self.assertEqual(len(s),18)
        self.assertTrue(all(r['lower']<=r['prediction']<=r['upper'] for r in p))

    def test_invalid_model(self):
        with self.assertRaises(ValueError):predict([1]*28,3,'unknown')
        with self.assertRaises(ValueError):predict([1]*5,3,MODELS[0])
