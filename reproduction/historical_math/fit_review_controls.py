"""Finite, DEV-only response controls. No TEST paths are opened here."""
import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['CUDA_VISIBLE_DEVICES'] = ''
from pathlib import Path
import argparse, hashlib, json, time
import numpy as np
from scipy.optimize import minimize, check_grad
import selector_math_full as sm
import selection_core as core
from fit_matched_controls import reduce_design, grid, totals, macro, write

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parents[2]
COLS3 = (0, 10, 2)
load = lambda p: json.loads(Path(p).read_text())
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p, data):
    assert not Path(p).exists(), p
    Path(p).write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')

def objective(theta, x, cost, weight, valid, lam):
    scores = x @ theta
    scores[~valid] = -np.inf
    scores -= scores.max(1, keepdims=True)
    q = np.exp(scores); q /= q.sum(1, keepdims=True)
    expected = (q * cost).sum(1)
    grad = np.einsum('nk,nkj->j', weight[:, None] * q * (cost - expected[:, None]), x)
    return float(weight @ expected + lam * (theta @ theta)), grad + 2 * lam * theta

def prepared(p):
    _, _, s = sm.design(p, np.ones(len(p['k']), int), COLS3)
    x = np.ascontiguousarray(p['x'][:, :, COLS3] / s)
    err = p['counts'][:, :, :3].sum(2).astype(float)
    cost = err - err[:, :1]
    den = np.bincount(p['lang'], weights=p['counts'][:, 0, 3], minlength=5)
    assert np.all(den > 0)
    weight = 1 / (5 * den[p['lang']])
    valid = np.arange(x.shape[1])[None, :] < p['k'][:, None]
    return x, cost, weight, valid, s

def solve(data, lam):
    x, cost, weight, valid, s = data
    opt = minimize(objective, np.zeros(3), args=(x, cost, weight, valid, lam),
                   jac=True, method='L-BFGS-B',
                   options=dict(maxiter=100, ftol=1e-9, gtol=1e-6, maxls=30))
    assert np.isfinite(opt.x).all() and np.isfinite(opt.fun)
    return dict(columns=list(COLS3), raw_beta=(opt.x / s).tolist(),
                theta=opt.x.tolist(), scale=s.tolist(), lambda_value=lam), dict(
                    converged=bool(opt.success), message=str(opt.message),
                    iterations=int(opt.nit), evaluations=int(opt.nfev),
                    objective=float(opt.fun), gradient_max=float(abs(opt.jac).max()))

def validate_math():
    rng = np.random.default_rng(17)
    x = rng.normal(size=(15, 6, 3)); x[:, 0] = 0
    cost = rng.integers(-7, 12, (15, 6)).astype(float); cost[:, 0] = 0
    weight = rng.random(15); weight /= weight.sum()
    valid = np.arange(6)[None, :] < rng.integers(1, 7, (15, 1))
    t = np.asarray([.2, -.6, .7])
    f = lambda v: objective(v, x, cost, weight, valid, .03)[0]
    g = lambda v: objective(v, x, cost, weight, valid, .03)[1]
    error = check_grad(f, g, t)
    assert error < 1e-6, error
    f0, g0 = objective(t, x, cost, weight, valid, .03)
    f1, g1 = objective(t, x, cost + 4, weight, valid, .03)
    np.testing.assert_allclose(g0, g1, atol=1e-12)
    assert abs(f1-f0-4) < 1e-12
    return dict(finite_difference_l2_error=float(error), cost_shift_gradient_invariant=True)

def run(family):
    start = time.monotonic(); protocol = ROOT / 'protocol/REVIEW_RESPONSE_PROTOCOL.json'
    cfg = load(protocol); assert sha(protocol) == protocol.with_suffix('.sha256').read_text().strip()
    src = cfg['DEV_panels'][family]; assert sha(src['path']) == src['sha256']
    p = dict(np.load(src['path'], allow_pickle=False)); assert len(p['k']) == 58171 and p['fit'].all()
    assert np.max(p['duration']) <= 30, 'DEV supervision must use complete single windows'
    folds = np.load(cfg['folds']['path']); assert sha(cfg['folds']['path']) == cfg['folds']['sha256']
    np.testing.assert_array_equal(folds, core.grouped_folds(p, 9297101))
    lambdas = cfg['lambdas']; predictions = np.empty((49, len(p['k'])), np.int16)
    diagnostics = []; coefficients = []
    for f in range(5):
        train = sm.subset(p, folds != f); val = sm.subset(p, folds == f)
        core.assert_disjoint(train, val); data = prepared(train)
        for j, lam in enumerate(lambdas):
            model, info = solve(data, lam)
            predictions[j, folds == f] = sm.choose(val, model)
            diagnostics.append(dict(checkpoint=family, fold=f, index=j, lambda_value=lam, **info))
            coefficients.append(dict(fold=f, index=j, model=model))
        print(json.dumps(dict(checkpoint=family, completed_fold=f, seconds=time.monotonic()-start,
                              nonconverged=sum(not d['converged'] for d in diagnostics))), flush=True)
    sdin = np.asarray([totals(p, picks) for picks in predictions])
    wer = np.asarray([macro(cc) for cc in sdin])
    j = min(range(49), key=lambda j: (wer[j], -lambdas[j]))
    risk, info = solve(prepared(p), lambdas[j])
    baseline = Path(cfg['baseline_root'])
    if family == 'Seamless':
        old = load(PROJECT / 'artifacts/asr_official_splits/20260929_v1/models/official_dev_rep01.json')['full_pool_fits']['Seamless']
    else:
        old = load(PROJECT / f'artifacts/iscas_mechanism_calibration/20261001_v1/models/{family}.json')
    original = old['models']['Recording-B20']; lam = original['lambda_value']
    designs = sm.prepare(p, core.COLS, 'Recording-B20', cfg['bag_seeds'])
    full = sm.fit(designs, core.COLS, lam)
    np.testing.assert_allclose(full['raw_beta'], original['raw_beta'], rtol=1e-10, atol=1e-12)
    cols = tuple(c for c in core.COLS if c != 1)
    fixed = grid(reduce_design(designs, cols), cols, [lam])[0]
    save(ROOT / f'models/REVIEW_{family}.json', dict(checkpoint=family, protocol_sha256=sha(protocol),
        DEV_sha256=src['sha256'], code_sha256=sha(__file__), DEV_only=True,
        Risk3=dict(model=risk, OOF_WER=float(wer[j]), selected_index=j, optimization=info),
        DropBankFixedLambda=dict(model=fixed, original_lambda=lam, original_coefficients_reproduced=True),
        gradient_verification=validate_math(), fold_coefficients=coefficients,
        duration_seconds=time.monotonic()-start))
    np.savez_compressed(ROOT / f'results/RISK_DEV_STATS_{family}.npz', SDIN=sdin, lambdas=lambdas,
                        selected_index=j, training_gram=np.asarray([x[0] for x in designs]),
                        training_rhs=np.asarray([x[1] for x in designs]), training_scale=np.asarray([x[2] for x in designs]))
    np.savez_compressed(ROOT / f'private/RISK_OOF_{family}.npz', picks=predictions[j])
    write(ROOT / f'results/risk_optimizer_{family}.csv', diagnostics)
    write(ROOT / f'results/risk_grid_{family}.csv', [dict(checkpoint=family, index=i,
        lambda_value=lambdas[i], OOF_WER=float(v), selected=i==j) for i,v in enumerate(wer)])
    print(json.dumps(dict(status='COMPLETE', checkpoint=family, OOF_WER=float(wer[j]),
                          lambda_value=lambdas[j], final_converged=info['converged'],
                          seconds=time.monotonic()-start)), flush=True)

if __name__ == '__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--checkpoint', required=True)
    run(parser.parse_args().checkpoint)
