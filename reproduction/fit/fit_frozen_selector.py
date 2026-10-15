"""Portable DEV-only replay of the final expected-risk fit at locked lambda.

No TEST data, new model selection, or GPU is used. The loss/RMS match the
archived implementation in historical_math; feature columns are preselected.
"""
import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['CUDA_VISIBLE_DEVICES'] = ''
from pathlib import Path
import argparse
import json
import hashlib
import numpy as np
from scipy.optimize import minimize


def objective(theta, x, cost, weight, valid, lam):
    scores = x @ theta
    scores[~valid] = -np.inf
    scores -= scores.max(1, keepdims=True)
    q = np.exp(scores)
    q /= q.sum(1, keepdims=True)
    expected = (q * cost).sum(1)
    grad = np.einsum('nk,nkj->j', weight[:, None] * q * (cost - expected[:, None]), x)
    return float(weight @ expected + lam * (theta @ theta)), grad + 2 * lam * theta


def fit(root, seed):
    cfg = json.loads((root / '../config/FIT_CONFIG.json').read_text())
    locked = json.loads((root / '../config/SELECTORS.json').read_text())['checkpoints'][str(seed)]['F']
    path = root / f'data/DEV_{seed}.npz'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == cfg['fit_sources'][str(seed)]['export_sha256']
    with np.load(path, allow_pickle=False) as z:
        x, counts, lang, k = z['x'], z['counts'], z['lang'], z['k']
    assert x.shape[-1] == 4 and len(k) == 58171
    den = np.bincount(lang, weights=counts[:, 0, 3], minlength=5)
    keep = np.arange(x.shape[1] - 1)[None, :] < (k - 1)[:, None]
    row = np.broadcast_to(np.arange(len(k))[:, None], keep.shape)[keep]
    nonbeam = np.ascontiguousarray(x[:, 1:][keep], dtype=float)
    w = 1. / (den[lang[row]] * (k[row] - 1))
    w /= w.sum()
    scale = np.sqrt((w[:, None] * nonbeam * nonbeam).sum(0))
    scale = np.where(scale > 1e-12, scale, 1.)
    errors = counts[:, :, :3].sum(2)
    scaled = np.ascontiguousarray(x / scale)
    costs = (errors - errors[:, :1]).astype(float)
    weight = 1 / (5 * den[lang])
    valid = np.arange(x.shape[1])[None, :] < k[:, None]
    options = {key: cfg['optimizer'][key] for key in ['maxiter', 'ftol', 'gtol', 'maxls']}
    opt = minimize(objective, np.zeros(4), args=(scaled, costs, weight, valid, locked['lambda_value']),
                   method='L-BFGS-B', jac=True, options=options)
    assert opt.success, opt.message
    beta = opt.x / scale
    np.testing.assert_allclose(scale, locked['scale'], atol=1e-12, rtol=1e-12)
    np.testing.assert_allclose(beta, locked['raw_beta'], atol=1e-8, rtol=1e-7)
    return {'seed': seed, 'rows': len(k), 'status': 'PASS', 'lambda': locked['lambda_value'],
            'scale': scale.tolist(), 'raw_beta': beta.tolist(), 'iterations': int(opt.nit),
            'max_beta_difference': float(abs(beta - locked['raw_beta']).max())}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    args = p.parse_args()
    result = {'status': 'PASS', 'scope': 'Final DEV refits at frozen penalties; grid selection not rerun.',
              'results': [fit(args.root, seed) for seed in (101, 202, 303)]}
    (args.root / 'FINAL_FIT_REPLAY.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
