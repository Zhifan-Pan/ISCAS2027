import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_v147_evidence import inspect_features, validate_counts, split_difference, macro

def bank():
    raw=np.array([[[-1.,-2.,1.,0.],[-2.,-3.,2.,.2]], [[np.nan,np.nan,1.,0.],[np.nan]*4]])
    observed=np.isfinite(raw)
    x=np.zeros_like(raw);x[0]=raw[0]-raw[0,0]
    return dict(raw_features=raw,raw_observed=observed,x=x,k=np.array([2,1]))

class AuditTests(unittest.TestCase):
    def test_singleton_missing_allowed(self):
        self.assertEqual(inspect_features(bank())['unknown_raw_singleton_banks'],1)
    def test_no_imputation(self):
        p=bank();p['raw_features'][1,0,0]=0
        with self.assertRaises(ValueError):inspect_features(p)
    def test_multicandidate_missing_rejected(self):
        p=bank();p['raw_features'][0,1,0]=np.nan;p['raw_observed'][0,1,0]=False
        with self.assertRaises(ValueError):inspect_features(p)
    def test_incorrect_relative_rejected(self):
        p=bank();p['x'][0,1,0]+=.01
        with self.assertRaises(ValueError):inspect_features(p)
    def test_nonzero_singleton_relative_rejected(self):
        p=bank();p['x'][1,0,0]=.1
        with self.assertRaises(ValueError):inspect_features(p)
    def test_genuine_zero_distinct_from_missing(self):
        p=bank();p['raw_features'][0,1]=0;p['x'][0]=p['raw_features'][0]-p['raw_features'][0,0]
        r=inspect_features(p);self.assertEqual(r['genuine_observed_all_zero_candidates'],1)
        self.assertEqual(r['unknown_raw_singleton_banks'],1)
    def test_padded_missing_is_not_active_missing(self):
        p=bank();p['raw_features'][1,0]=[-1.,-2.,1.,0.];p['raw_observed'][1,0]=True
        self.assertEqual(inspect_features(p)['unknown_raw_singleton_banks'],0)
    def test_reference_mismatch_rejected(self):
        with self.assertRaises(ValueError):validate_counts(np.array([[1,0,0,10]]),np.array([11]))
    def test_s_plus_d_constraint(self):
        with self.assertRaises(ValueError):validate_counts(np.array([[6,5,0,10]]))
    def test_insertions_can_exceed_reference(self):
        validate_counts(np.array([[1,0,30,10]]))
    def test_missing_language_not_dropped(self):
        with self.assertRaises(ValueError):macro(np.array([[1,0,0,10]]),np.array([0]))
    def test_branch_uses_full_language_denominators(self):
        l=np.repeat(np.arange(5),2)
        b=np.tile([1,0,0,10],(10,1));a=b.copy();a[::2,0]=3;a[1::2,0]=2
        flags=np.tile([True,False],5)
        r=split_difference(a,b,l,flags)
        self.assertAlmostEqual(r['complete_difference_pp'],15)
        self.assertAlmostEqual(r['trigger_contribution_pp'],10)
        self.assertAlmostEqual(r['nontrigger_contribution_pp'],5)
    def test_split_can_be_negative(self):
        l=np.arange(5);a=np.tile([0,0,0,10],(5,1));b=np.tile([1,0,0,10],(5,1))
        r=split_difference(a,b,l,np.zeros(5,dtype=bool))
        self.assertAlmostEqual(r['complete_difference_pp'],-10)
        self.assertEqual(r['trigger_contribution_pp'],0)
    def test_float_counts_rejected(self):
        with self.assertRaises(ValueError):validate_counts(np.array([[1.,0.,0.,10.]]))

if __name__=='__main__':unittest.main()
