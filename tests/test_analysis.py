"""Hand-reconstructed accounting and invalid-input regression checks."""
from pathlib import Path
import importlib.util, unittest
P=Path(__file__).resolve().parents[1]/'skills/write-innovation-essays/scripts/analysis.py'
spec=importlib.util.spec_from_file_location('studio_analysis',P);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

class AnalysisChecks(unittest.TestCase):
    def baseline(self,lag=0):
        return {'months':3,'units':10,'unit_price':10,'unit_variable_cost':4,'fixed_cost':20,'setup_cost':100,'annual_discount_rate':0,'receipts_lag_months':lag}
    def test_cash_and_sustained_payback(self):
        # 100 receipts - 40 variable - 20 fixed = 40/month; 3*40-100=20.
        r=mod.finance(self.baseline());self.assertEqual(r['npv'],20);self.assertEqual(r['sustained_cash_payback_month'],3);self.assertEqual(r['closing_receivables'],0);self.assertEqual(r['funding_need_including_reserve'],100)
    def test_accrual_is_not_cash(self):
        # Lagged receipts 0,100,100; costs60each; projectcash-160,-120,-80.
        r=mod.finance(self.baseline(1));self.assertEqual(r['total_accrued_revenue'],300);self.assertEqual(r['total_cash_receipts'],200);self.assertEqual(r['closing_receivables'],100);self.assertEqual(r['npv'],-80);self.assertIsNone(r['sustained_cash_payback_month']);self.assertEqual(r['funding_need_including_reserve'],160)
    def test_financing_does_not_create_project_return(self):
        c=self.baseline();c['planned_financing']=1000000;r=mod.finance(c);self.assertEqual(r['npv'],20);self.assertEqual(r['monthly'][0]['cash_with_planned_financing'],999940)
    def test_discount_month_convention(self):
        c=self.baseline();c['annual_discount_rate']=.12;r=mod.finance(c);expected=-100+sum(40/(1.12**(m/12))for m in [1,2,3]);self.assertAlmostEqual(r['npv'],expected,places=10)
    def test_no_silent_score_normalization(self):
        with self.assertRaises(ValueError):mod.weighted({'factors':[{'weight':.8,'rating':3}]})
        r=mod.weighted({'rating_range':[1,4],'factors':[{'factor':'A','weight':.25,'rating':4},{'factor':'B','weight':.75,'rating':2}]});self.assertEqual(r['weighted_total'],2.5)
    def test_bad_distribution_and_correlation(self):
        c=self.baseline();c['uncertainty']={'draws':100,'factors':{'units_factor':{'distribution':'triangular','min':.5,'mode':1,'max':1.5},'price_factor':{'distribution':'uniform','min':.8,'max':1.2}},'latent_correlation':[[1,2],[2,1]]}
        with self.assertRaises(ValueError):mod.simulate(c)
    def test_seeded_run_repeats_and_scope_is_conditional(self):
        c=self.baseline();c['uncertainty']={'draws':100,'seed':42,'factors':{'units_factor':{'distribution':'uniform','min':.5,'max':1.5}}};a=mod.simulate(c);b=mod.simulate(c);self.assertEqual(a,b);self.assertIn('Not probability',a['scope']);self.assertLessEqual(a['quantiles']['npv']['p10'],a['quantiles']['npv']['p90'])
    def test_invalid_horizon_and_array(self):
        c=self.baseline();c['months']=True
        with self.assertRaises(ValueError):mod.finance(c)
    def test_unknown_assumptions_are_not_ignored(self):
        c=self.baseline();c['receipts_lag_month']=1
        with self.assertRaises(ValueError):mod.finance(c)
    def test_unnamed_score_is_rejected(self):
        with self.assertRaises(ValueError):mod.weighted({'factors':[{'weight':1,'rating':3}]})
    def test_large_simulation_requires_smaller_declared_budget(self):
        c=self.baseline();c['months']=1200;c['uncertainty']={'draws':100000,'factors':{'units_factor':{'distribution':'uniform','min':.5,'max':1.5}}}
        with self.assertRaises(ValueError):mod.simulate(c)
        c=self.baseline();c['units']=[1,2]
        with self.assertRaises(ValueError):mod.finance(c)

if __name__=='__main__':unittest.main()
