import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from candidate_objectives import Banks,risk_value_grad,rank_value_grad,rank_pairs,relative_features_and_rms,hard_macro_wer
from audit_effect_scope import validate_counts,mwer

class TestObjectives(unittest.TestCase):
    def setUp(self):
        self.b=Banks(np.array([[0.,0.],[1.,-2.],[-1.,.5],[0.,0.],[.7,1.],[0.,0.]]),np.array([0,3,5,6]),np.array([5,2,4,2,1,0]),np.array([6,5,4]),np.array([0,0,1]))
        self.t=np.array([.2,-.4])
    def numerical(self,fn,t):
        h=1e-6;g=[]
        for j in range(len(t)):
            a=t.copy();b=t.copy();a[j]+=h;b[j]-=h;g.append((fn(a)[0]-fn(b)[0])/(2*h))
        return np.array(g)
    def test_risk_gradient(self):
        fn=lambda x:risk_value_grad(x,self.b,.03)
        np.testing.assert_allclose(fn(self.t)[1],self.numerical(fn,self.t),rtol=1e-6,atol=1e-9)
    def test_rank_gradient(self):
        d,w=rank_pairs(self.b);fn=lambda x:rank_value_grad(x,d,w,.03)
        np.testing.assert_allclose(fn(self.t)[1],self.numerical(fn,self.t),rtol=1e-6,atol=1e-9)
    def test_risk_bank_translation(self):
        x=self.b.features.copy();x[:3]+=[10,5];x[3:5]+=[-2,9]
        other=Banks(x,self.b.offsets,self.b.edits,self.b.words,self.b.languages)
        a=risk_value_grad(self.t,self.b,.03);b=risk_value_grad(self.t,other,.03)
        self.assertAlmostEqual(a[0],b[0]);np.testing.assert_allclose(a[1],b[1],atol=1e-12)
    def test_constant_error_shift(self):
        other=Banks(self.b.features,self.b.offsets,self.b.edits+3,self.b.words,self.b.languages)
        np.testing.assert_allclose(risk_value_grad(self.t,self.b,.03)[1],risk_value_grad(self.t,other,.03)[1],atol=1e-12)
    def test_ties_follow_bank_order(self):
        self.assertAlmostEqual(hard_macro_wer(np.zeros(2),self.b),100*.5*7/11)
    def test_zero_pair_bank(self):
        b=Banks(np.zeros((2,2)),np.array([0,2]),np.array([1,1]),np.array([3]),np.array([0]));d,w=rank_pairs(b)
        self.assertEqual(d.shape,(0,2));v,g=rank_value_grad(self.t,d,w,0.1)
        self.assertAlmostEqual(v,.1*float(self.t@self.t));np.testing.assert_allclose(g,.2*self.t)
    def test_rank_extreme_stable(self):
        v,g=rank_value_grad(np.array([1000.]),np.array([[1000.],[-1000.]]),np.array([.5,.5]),0.)
        self.assertTrue(np.isfinite(v));self.assertTrue(np.isfinite(g).all())
    def test_invalid_offsets(self):
        b=Banks(self.b.features,np.array([0,0,6]),self.b.edits,np.array([5,5]),np.array([0,1]))
        with self.assertRaises(ValueError):b.validate()
    def test_missing_language_reference(self):
        b=Banks(self.b.features,self.b.offsets,self.b.edits,np.array([0,0,4]),self.b.languages)
        with self.assertRaises(ValueError):b.validate()
    def test_negative_count(self):
        with self.assertRaises(ValueError):validate_counts({'S':0,'D':0,'I':-1,'N':1})
    def test_bad_error_bound(self):
        with self.assertRaises(ValueError):validate_counts({'S':2,'D':1,'I':0,'N':2})
    def test_bool_not_integer_counts(self):
        with self.assertRaises(ValueError):validate_counts({'S':True,'D':0,'I':0,'N':2})
    def test_wer_above_100_allowed(self):
        validate_counts({'S':1,'D':0,'I':20,'N':2})
    def test_fold_scales_exclude_validation(self):
        o=np.array([0,2,4]);x=np.array([[0.,0.],[2.,4.],[0.,0.],[1000.,10000.]])
        _,s=relative_features_and_rms(x,o,np.array([True,False]));np.testing.assert_allclose(s,[2.,4.])
    def test_zero_rms_set_one(self):
        _,s=relative_features_and_rms(np.zeros((2,2)),np.array([0,2]),np.array([True]));np.testing.assert_array_equal(s,np.ones(2))
    def test_pair_count_weight(self):
        d,w=rank_pairs(self.b);self.assertEqual(len(d),4);self.assertAlmostEqual(w.sum(),1/11)
    def test_counts_metric(self):
        rows=[{'lang':'a','B':{'S':1,'D':0,'I':0,'N':2}},{'lang':'b','B':{'S':0,'D':0,'I':0,'N':3}}]
        self.assertEqual(mwer(rows,'B'),25.)
    def test_nan_rejected(self):
        x=self.b.features.copy();x[0,0]=np.nan
        with self.assertRaises(ValueError):Banks(x,self.b.offsets,self.b.edits,self.b.words,self.b.languages).validate()
if __name__=='__main__':unittest.main()
