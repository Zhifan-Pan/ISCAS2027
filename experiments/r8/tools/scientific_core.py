"""Exact scientific functions from the executed R8 scripts; portable IO is separate."""

import numpy as np

from hf_gate_math import *

def cross_validate(features, y, lang, fold, eligible, alphas):
    n = len(y)
    predictions = np.full((len(alphas), n), np.nan)
    constants = np.full(n, np.nan)
    fold_models = []
    for heldout in range(5):
        train, valid = eligible & (fold != heldout), eligible & (fold == heldout)
        assert train.any() and valid.any()
        constants[valid] = language_weights(lang[train]) @ y[train]
        for a, alpha in enumerate(alphas):
            model = ridge_fit(features, y, lang, train, alpha)
            predictions[a, valid] = predict(features[valid], model)
            fold_models.append(dict(heldout_fold=heldout, model=model))
    assert np.isfinite(predictions[:, eligible]).all() and np.isfinite(constants[eligible]).all()
    weights = language_weights(lang[eligible])
    loss = (predictions[:, eligible] - y[eligible]) ** 2 @ weights
    constant_loss = float(weights @ ((constants[eligible] - y[eligible]) ** 2))
    return predictions, constants, loss, constant_loss, fold_models

def align_windows(windows, ids, lang, expected_eligible):
    assert len(set(ids)) == len(ids)
    lookup = {v:i for i,v in enumerate(ids)}
    index = np.asarray([lookup[u] for u in windows['ids']])
    np.testing.assert_array_equal(windows['lang'], lang[index])
    counts = np.bincount(index, minlength=len(ids))
    assert (counts > 0).all()
    np.testing.assert_array_equal(counts[index], windows['window_count'])
    assert len(set(zip(index.tolist(), windows['window_index'].tolist()))) == len(index)
    assert (windows['window_index'] >= 0).all()
    assert (windows['window_index'] < counts[index]).all()
    eligible = np.zeros(len(ids), bool)
    np.logical_or.at(eligible, index, windows['eligible'])
    np.testing.assert_array_equal(eligible, expected_eligible)
    return index

def aggregate_verified(scores, windows, index, n, thresholds, qs):
    rec_score, eligible = recording_scores(scores, windows['eligible'], index, n)
    flags = []
    for q in qs:
        f = threshold_flags(rec_score, eligible, thresholds[str(q)], q)
        independent_any = np.zeros(n, bool)
        wf = threshold_flags(scores, windows['eligible'], thresholds[str(q)], q)
        np.logical_or.at(independent_any, index, wf)
        np.testing.assert_array_equal(f, independent_any)
        flags.append(f)
    return rec_score, eligible, np.asarray(flags)

def macro(counts, lang):
    return float(np.mean([100.*counts[lang == j,:3].sum()/counts[lang == j,3].sum() for j in range(5)]))

def paired_interval(delta, words, lang, components, *, draws=2000, seed=8003):
    """Mean delta over checkpoints first; same component draw for every seed."""
    delta = np.asarray(delta,float)
    assert delta.ndim == 2 and delta.shape[1] == len(words)
    mean_edits = delta.mean(0)
    sufficient = []
    for j in range(5):
        mask = lang == j
        _, inverse = np.unique(components[mask],return_inverse=True)
        edits = np.bincount(inverse,weights=mean_edits[mask])
        denominator = np.bincount(inverse,weights=words[mask])
        assert (denominator > 0).all()
        sufficient.append((edits,denominator))
    point = float(sum(20.*e.sum()/n.sum() for e,n in sufficient))
    rng = np.random.default_rng(seed)
    values = np.zeros(draws)
    for b in range(draws):
        for e,n in sufficient:
            take = rng.choice(len(n),len(n),replace=True)
            values[b] += 20.*e[take].sum()/n[take].sum()
    return point, np.quantile(values,[.025,.975]), values
