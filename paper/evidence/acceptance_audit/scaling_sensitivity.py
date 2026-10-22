"""DEV-selected RMS sensitivity audit. CPU only; existing results are immutable.

Usage: python scaling_sensitivity.py --repo REPO --output OUT
All nine refits are locked before TEST evaluation. The sole intervention is
G4's weighted RMS rule on the existing HF banks, recomputed in each fold.
"""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='', OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
import argparse
import concurrent.futures
import csv
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np
from scipy.optimize import minimize


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def save(p, obj):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n')


def arrays(p):
    with np.load(p, allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


def macro(c, lang):
    return float(np.mean([100 * c[lang == l, :3].sum() / c[lang == l, 3].sum() for l in range(5)]))


def weighted_scale(p, train):
    x, k, counts, lang = (p[q][train] for q in ('x', 'k', 'counts', 'lang'))
    den = np.bincount(lang, weights=counts[:, 0, 3], minlength=5)
    valid = (np.arange(x.shape[1])[None, :] < k[:, None]) & (np.arange(x.shape[1])[None, :] > 0)
    row = np.broadcast_to(np.arange(len(k))[:, None], valid.shape)[valid]
    w = 1.0 / (den[lang[row]] * (k[row] - 1))
    w /= w.sum()
    s = np.sqrt(np.sum(w[:, None] * x[valid] ** 2, axis=0))
    return np.where(s > 1e-12, s, 1.0)


def imports(repo):
    sys.path.insert(0, str(repo / 'experiments/acceptors/tools'))
    sys.path.insert(0, str(repo / 'experiments/extensions/code'))
    from objective_engine import Prepared, scale_from_training, choose
    from fit_hwr4 import WeightedPairs
    return Prepared, scale_from_training, choose, WeightedPairs


def fit_seed(repo_s, out_s, seed):
    repo, out = Path(repo_s), Path(out_s)
    Prepared, pooled_scale, choose, WeightedPairs = imports(repo)
    plan = json.loads((out / 'PROTOCOL.json').read_text())
    src = repo / f'experiments/acceptors/inputs/DEV_{seed}.npz'
    assert sha(src) == plan['DEV_sha256'][str(seed)]
    p = arrays(src)
    n = len(p['k'])
    lambdas, opts = plan['lambdas'], plan['optimizer']
    assert len(lambdas) == 49 and set(p['fold']) == set(range(5))
    for l in range(5):
        for group in np.unique(p['components'][p['lang'] == l]):
            assert len(np.unique(p['fold'][(p['lang'] == l) & (p['components'] == group)])) == 1
    # Validate the weighted scale against the independent frozen greedy fit.
    greedy = arrays(repo / f'reproduction/fit/data/DEV_{seed}.npz')
    g = json.loads((repo / 'reproduction/config/SELECTORS.json').read_text())['checkpoints'][str(seed)]['F']
    np.testing.assert_allclose(weighted_scale(greedy, np.ones(len(greedy['k']), bool)), g['scale'], atol=1e-12, rtol=1e-12)
    results = []
    for family in plan['families']:
        start = time.monotonic()
        folder = out / f'{family}_{seed}'
        folder.mkdir(exist_ok=False)
        oldpath = repo / (f'experiments/extensions/models/{family}_{seed}.json' if family == 'HWR4' else f'experiments/acceptors/models/{family}_{seed}.json')
        old = json.loads(oldpath.read_text())
        lam_old = old.get('lambda', old.get('penalty'))
        kind = 'risk' if family == 'H4' else 'rank'
        klass = WeightedPairs if family == 'HWR4' else Prepared
        def prepared(mask, scale):
            return klass(p['x'][mask], p['k'][mask], p['counts'][mask], p['lang'][mask], [0, 1, 2, 3], scale, kind)
        def fit(data, lam, fold, label):
            opt = minimize(data.value_grad, np.zeros(4), args=(lam,), method='L-BFGS-B', jac=True, options=opts)
            entry = dict(fold=fold, label=label, penalty=lam, success=bool(opt.success), message=str(opt.message), iterations=int(opt.nit), objective=float(opt.fun), gradient_max=float(np.abs(opt.jac).max()), theta=opt.x.tolist())
            with (folder / 'fit_log.jsonl').open('a') as f:
                f.write(json.dumps(entry) + '\n')
            if not opt.success or not np.isfinite(opt.x).all():
                save(folder / 'FAILED.json', entry)
                raise RuntimeError(str(entry))
            return opt.x
        allrows = np.ones(n, bool)
        oldscale = pooled_scale(p['x'], p['k'], allrows, [0, 1, 2, 3])
        np.testing.assert_allclose(oldscale, old['scale'], rtol=1e-12, atol=1e-12)
        oldtheta = fit(prepared(allrows, oldscale), lam_old, 'ALL_DEV', 'baseline_replay')
        np.testing.assert_allclose(oldtheta / oldscale, old['raw_beta'], rtol=1e-7, atol=1e-8)
        oof = np.full((49, n), -1, np.int16)
        folds = []
        for fold in range(5):
            tr, va = p['fold'] != fold, p['fold'] == fold
            scale = weighted_scale(p, tr)
            data = prepared(tr, scale)
            folds.append(dict(fold=fold, train=int(tr.sum()), held=int(va.sum()), scale=scale.tolist()))
            for j, lam in enumerate(lambdas):
                theta = fit(data, lam, fold, 'weighted_RMS')
                oof[j, va] = choose(p['x'][va], p['k'][va], [0, 1, 2, 3], theta / scale)
            save(folder / 'progress.json', dict(completed_folds=fold + 1, elapsed_seconds=time.monotonic() - start))
        assert (oof >= 0).all()
        metrics = [macro(p['counts'][np.arange(n), pick], p['lang']) for pick in oof]
        selected = min(range(49), key=lambda j: (metrics[j], -lambdas[j]))
        scale = weighted_scale(p, allrows)
        theta = fit(prepared(allrows, scale), lambdas[selected], 'ALL_DEV', 'weighted_RMS')
        model = dict(family=family, seed=seed, scale=scale.tolist(), theta=theta.tolist(), raw_beta=(theta / scale).tolist(), penalty=lambdas[selected], selected_index=selected, OOF_WER=metrics[selected], scope='retrospective sensitivity diagnostic; not a replacement for the published models')
        save(folder / 'model.json', model)
        np.savez_compressed(folder / 'oof_picks.npz', picks=oof)
        result = dict(seed=seed, family=family, baseline_model_sha256=sha(oldpath), baseline_replay_max_beta_difference=float(np.max(np.abs(oldtheta / oldscale - old['raw_beta']))), baseline_penalty=lam_old, baseline_scale=oldscale.tolist(), folds=folds, grid=[dict(penalty=l, OOF_WER=w) for l, w in zip(lambdas, metrics)], model=model, converged_fits=247, elapsed_seconds=time.monotonic() - start)
        save(folder / 'RESULT.json', result)
        print(json.dumps(dict(seed=seed, family=family, completed=True, seconds=result['elapsed_seconds'])), flush=True)
        results.append(result)
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--evaluate-only', action='store_true')
    a = ap.parse_args()
    repo, out = a.repo.resolve(), a.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    if a.evaluate_only:
        plan = json.loads((out / 'PROTOCOL.json').read_text())
        lock = json.loads((out / 'MODEL_LOCK.json').read_text())
        for name, digest in lock.items():
            assert sha(out / name / 'model.json') == digest
        evaluate(repo, out, plan)
        return
    assert not (out / 'PROTOCOL.json').exists(), 'Use a fresh output directory; preserve prior evidence.'
    original = json.loads((repo / 'experiments/acceptors/prerefit_plan.json').read_text())
    plan = dict(scope='CPU-only retrospective weighted-RMS sensitivity; all models selected using DEV only; all locked before TEST evaluation', intervention='Use G4 weighted RMS formula on existing HF banks, not numeric scales from different greedy banks.', families=['H4', 'HR4', 'HWR4'], seeds=[101, 202, 303], lambdas=original['lambdas'], optimizer=original['optimizer']['options'], DEV_sha256={str(s): sha(repo / f'experiments/acceptors/inputs/DEV_{s}.npz') for s in (101, 202, 303)}, source_sha256=sha(__file__))
    save(out / 'PROTOCOL.json', plan)
    with concurrent.futures.ProcessPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(fit_seed, [str(repo)] * 3, [str(out)] * 3, plan['seeds']))
    save(out / 'MODEL_LOCK.json', {f'{f}_{s}': sha(out / f'{f}_{s}/model.json') for s in plan['seeds'] for f in plan['families']})
    evaluate(repo, out, plan)


def evaluate(repo, out, plan):
    _, _, choose, _ = imports(repo)
    from evaluate_acceptors import score_selected
    rows = []
    for ds in ('FLEURS', 'CV27'):
        for seed in plan['seeds']:
            p = arrays(repo / f'experiments/acceptors/inputs/{ds}_{seed}.npz')
            owner = p.get('window_owner', np.arange(len(p['k'])))
            for family in plan['families']:
                oldpath = repo / (f'experiments/extensions/models/{family}_{seed}.json' if family == 'HWR4' else f'experiments/acceptors/models/{family}_{seed}.json')
                models = {'pooled': json.loads(oldpath.read_text()), 'weighted': json.loads((out / f'{family}_{seed}/model.json').read_text())}
                for label, model in models.items():
                    b = choose(p['x'], p['k_beam'], [0, 1, 2, 3], model['raw_beta'])
                    full = choose(p['x'], p['k'], [0, 1, 2, 3], model['raw_beta'])
                    picks = {'B': b, 'S': np.where(p['flags'][owner], full, b), 'Triggered': np.where(p['flags'][owner], full, p['B_pick'])}
                    for policy, pick in picks.items():
                        counts = score_selected(p, pick)
                        rows.append(dict(dataset=ds, checkpoint=seed, family=family, scaling=label, policy=policy, WER=macro(counts, p['lang'])))
    with (out / 'WER_BY_SEED.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    summary = []
    for ds in ('FLEURS', 'CV27'):
        for family in plan['families']:
            for policy in ('B', 'S', 'Triggered'):
                means = {label: float(np.mean([r['WER'] for r in rows if r['dataset'] == ds and r['family'] == family and r['policy'] == policy and r['scaling'] == label])) for label in ('pooled', 'weighted')}
                summary.append(dict(dataset=ds, family=family, policy=policy, **means, change_pp=means['weighted'] - means['pooled']))
    save(out / 'SUMMARY.json', dict(status='COMPLETE', converged_fits=9 * 247, GPU_used=False, results=summary))
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
