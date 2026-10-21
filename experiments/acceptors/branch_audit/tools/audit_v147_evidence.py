"""Read-only V147 singleton/branch audit; NOT model training or a new confirmation.

Inputs are the released acceptors/ arrays. This supplements, never replaces,
acceptors/tools/replay_packaged.py. Writes only to a new external directory.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys
import numpy as np

LANGS = ['ar', 'fa', 'pl', 'tr', 'it']
SEEDS = [101, 202, 303]
FAMILIES = ['G4', 'H4', 'HR4', 'H3']

def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()

def load_npz(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as z:
        return {key: z[key].copy() for key in z.files}

def inspect_features(p: dict[str, np.ndarray]) -> dict:
    x, raw, observed, k = (p[name] for name in ('x', 'raw_features', 'raw_observed', 'k'))
    ensure(x.ndim == 3 and x.shape[-1] == 4 and raw.shape == x.shape, 'Unexpected feature axes')
    ensure(observed.shape == x.shape and observed.dtype.kind == 'b', 'Invalid observation mask')
    ensure(k.shape == (len(x),) and k.dtype.kind in 'iu', 'Invalid bank counts')
    ensure(bool(((k >= 1) & (k <= x.shape[1])).all()), 'Empty or oversized bank')
    valid = np.arange(x.shape[1])[None, :] < k[:, None]
    active = np.broadcast_to(valid[..., None], x.shape)
    ensure(bool(np.isfinite(x[active]).all()), 'Non-finite active relative feature')
    ensure(bool(np.isfinite(raw[active & observed]).all()), 'Observed feature is non-finite')
    ensure(bool(np.isnan(raw[active & ~observed]).all()), 'Unobserved active raw feature was imputed')
    missing = np.any(active & ~observed, axis=(1, 2))
    ensure(bool((k[missing] == 1).all()), 'Missing raw values in a nontrivial bank')
    ensure(bool((x[missing, 0] == 0).all()), 'Missing-score singleton has a nonzero relative vector')
    complete = ~missing
    delta = raw[complete] - raw[complete, :1]
    mask = active[complete]
    max_error = float(np.max(np.abs((delta - x[complete])[mask]))) if mask.any() else 0.0
    ensure(max_error <= 1e-12, 'Observed raw-relative disagreement')
    finite_zero = np.all((raw == 0) & observed, axis=2) & valid
    return {
        'windows': len(k), 'active_candidates': int(k.sum()),
        'singleton_banks': int((k == 1).sum()),
        'unknown_raw_singleton_banks': int(missing.sum()),
        'missing_nontrivial_banks': 0,
        'genuine_observed_all_zero_candidates': int(finite_zero.sum()),
        'max_raw_relative_disagreement': max_error,
        'scope': 'Numeric completeness for selection; not authentication of original neural scoring.'
    }

def validate_counts(c: np.ndarray, ref: np.ndarray | None = None) -> None:
    ensure(c.ndim == 2 and c.shape[1] == 4 and c.dtype.kind in 'iu', 'Counts must be integer SDIN')
    ensure(bool((c >= 0).all()), 'Negative edit counts')
    ensure(bool((c[:, 0] + c[:, 1] <= c[:, 3]).all()), 'S+D exceeds N')
    if ref is not None:
        ensure(bool(np.array_equal(c[:, 3], ref)), 'Mismatched reference denominator')

def macro(c: np.ndarray, language: np.ndarray) -> float:
    validate_counts(c)
    ensure(set(map(int, np.unique(language))) == set(range(5)), 'All five languages required')
    values = []
    for ell in range(5):
        group = c[language == ell]
        denominator = int(group[:, 3].sum())
        ensure(denominator > 0, 'Zero language denominator')
        values.append(100.0 * int(group[:, :3].sum()) / denominator)
    return float(np.mean(values))

def split_difference(a: np.ndarray, b: np.ndarray, language: np.ndarray, flags: np.ndarray) -> dict:
    validate_counts(a); validate_counts(b, a[:, 3])
    ensure(flags.shape == (len(a),) and flags.dtype.kind == 'b', 'Flags must be a bool recording vector')
    difference = a[:, :3].sum(1) - b[:, :3].sum(1)
    pieces = {False: 0.0, True: 0.0}
    for ell in range(5):
        ix = language == ell; den = int(a[ix, 3].sum())
        ensure(den > 0, 'All language denominators required')
        for flag in pieces:
            pieces[flag] += 20.0 * int(difference[ix & (flags == flag)].sum()) / den
    total = macro(a, language) - macro(b, language)
    residual = total - pieces[False] - pieces[True]
    ensure(abs(residual) <= 1e-10, 'Branch decomposition did not close')
    return {'complete_difference_pp': total, 'nontrigger_contribution_pp': pieces[False],
            'trigger_contribution_pp': pieces[True], 'residual_pp': residual}

def run(artifact_root: Path, output: Path) -> dict:
    root = artifact_root.resolve(); acc = root / 'acceptors'; out = output.resolve()
    ensure(acc.is_dir(), 'Pass the reviewer_artifact root containing acceptors/')
    ensure(out != root and root not in out.parents, 'Output must be outside input tree')
    ensure(not out.exists(), 'Refusing existing output directory')
    identity = {}; features = []; units = []; corpus_summaries = []; paired_checks = 0
    def read(path: Path):
        identity[str(path.relative_to(root))] = sha256(path)
        return load_npz(path)
    for ds in ['DEV', 'FLEURS', 'CV27']:
        for seed in SEEDS:
            p = read(acc / 'inputs' / f'{ds}_{seed}.npz')
            features.append({'corpus': ds, 'checkpoint': seed, **inspect_features(p)})
    for ds in ['FLEURS', 'CV27']:
        per_seed = []; ids_ref = None; lang_ref = None; ref_ref = None
        for seed in SEEDS:
            q = read(acc / 'counts' / f'{ds}_{seed}.npz')
            ids, language, flags = q['ids'], q['lang'], q['flags']
            ensure(len(set(ids.tolist())) == len(ids), 'Duplicate recording IDs')
            if ids_ref is None:
                ids_ref, lang_ref, ref_ref = ids, language, q['B_G4'][:, 3]
            else:
                ensure(bool(np.array_equal(ids, ids_ref) and np.array_equal(language, lang_ref)), 'Checkpoint pairing mismatch')
                ensure(bool(np.array_equal(q['B_G4'][:, 3], ref_ref)), 'Checkpoint reference mismatch')
            names = [f'{p}_{a}' for a in FAMILIES for p in ['B', 'N', 'S']] + [f'T_{a}' for a in FAMILIES[1:]] + ['Direct']
            for name in names:
                validate_counts(q[name], ref_ref)
                units.append({'corpus': ds, 'checkpoint': seed, 'policy': name, 'macro_WER': macro(q[name], language)})
            for family in FAMILIES:
                ensure(bool(np.array_equal(q['S_'+family], np.where(flags[:,None],q['N_'+family],q['B_'+family]))), 'S policy reconstruction failed')
                paired_checks += 1
            for family in FAMILIES[1:]:
                ensure(bool(np.array_equal(q['T_'+family], np.where(flags[:,None],q['N_'+family],q['B_G4']))), 'T policy reconstruction failed')
                paired_checks += 1
            branch = split_difference(q['S_H3'],q['S_H4'],language,flags)
            fixed = macro(q['T_H3'],language)-macro(q['T_H4'],language)
            ensure(abs(branch['trigger_contribution_pp']-fixed)<1e-10,'Trigger-only contrast mismatch')
            branch.update(checkpoint=seed,
                whole_B_difference_pp=macro(q['B_H3'],language)-macro(q['B_H4'],language),
                risk_vs_pairwise_trigger_difference_pp=macro(q['T_HR4'],language)-macro(q['T_H4'],language))
            per_seed.append(branch)
        aggregate = {k: float(np.mean([r[k] for r in per_seed])) for k in per_seed[0] if k!='checkpoint'}
        total=aggregate['complete_difference_pp']
        aggregate['nontrigger_fraction_of_net_difference_percent']=100*aggregate['nontrigger_contribution_pp']/total if total else None
        aggregate['whole_B_fraction_of_net_difference_percent']=100*aggregate['whole_B_difference_pp']/total if total else None
        aggregate['recovery_gain_difference_pp']=total-aggregate['whole_B_difference_pp']
        corpus_summaries.append({'corpus':ds,'average':aggregate,'checkpoint':per_seed})
    ensure(len(units)==96 and paired_checks==42,'Incomplete expected policies')
    result={'scope':'Read-only audit and descriptive repartition of existing V147 data. No refitting, new confirmation, profiling, or new significance test.',
        'environment':{'python':sys.version,'numpy':np.__version__,'platform':platform.platform()},
        'inputs_sha256':identity,'feature_panels':features,'policy_unit_count':len(units),
        'S_and_T_reconstructions':paired_checks,'branch_comparisons':corpus_summaries,
        'units':units,'limitations':['Absolute unknown singleton scores remain unknown; their sole-choice output is not missing.',
        'Both H3 and H4 were refitted; this is not a coefficient-only intervention.',
        'A branch decomposition does not measure latency or justify selective PLL execution.',
        'Reference/audiotext history and fit provenance are not reauthenticated by numeric checks.']}
    out.mkdir(parents=True)
    (out/'audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--artifact-root',required=True,type=Path)
    p.add_argument('--output-dir',required=True,type=Path)
    args=p.parse_args()
    try:
        r=run(args.artifact_root,args.output_dir)
    except (ValueError, OSError, KeyError) as exc:
        p.exit(2, f'Audit failed: {exc}\n')
    print(json.dumps({'feature_panels':len(r['feature_panels']),'policies':r['policy_unit_count'],
                      'reconstructions':r['S_and_T_reconstructions'],'output':str(args.output_dir)},ensure_ascii=False))
