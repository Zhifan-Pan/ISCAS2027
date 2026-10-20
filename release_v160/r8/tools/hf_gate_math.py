"""Frozen R8 ridge, calibration and eligible-window aggregation (CPU only)."""
import numpy as np


def language_weights(lang):
    lang = np.asarray(lang)
    w = np.zeros(len(lang), dtype=float)
    for label in range(5):
        ix = lang == label
        if not ix.any():
            raise ValueError(f'Language {label} is absent from a training/validation population')
        w[ix] = 1. / (5 * int(ix.sum()))
    return w


def ridge_fit(features, labels, lang, train, alpha):
    z = np.asarray(features, float)[train]
    y = np.asarray(labels, float)[train]
    w = language_weights(np.asarray(lang)[train])
    mean = w @ z
    scale = np.sqrt(w @ ((z - mean) ** 2))
    scale[scale < 1e-10] = 1.
    d = np.column_stack([np.ones(len(z)), (z - mean) / scale])
    penalty = np.eye(d.shape[1]) * float(alpha)
    penalty[0, 0] = 0.
    coef = np.linalg.solve(d.T @ (w[:, None] * d) + penalty, d.T @ (w * y))
    return dict(mean=mean.tolist(), scale=scale.tolist(), coef=coef.tolist(), alpha=float(alpha))


def predict(features, model):
    z = (np.asarray(features, float) - model['mean']) / model['scale']
    return np.column_stack([np.ones(len(z)), z]) @ np.asarray(model['coef'])


def select_lambda(losses, alphas):
    losses = np.asarray(losses, float)
    if not np.isfinite(losses).all():
        raise ValueError('Nonfinite CV loss')
    tied = np.flatnonzero(losses == losses.min())
    return int(max(tied, key=lambda i: alphas[i]))


def calibrated_thresholds(scores, eligible, quantiles):
    values = np.asarray(scores)[eligible]
    if not len(values) or not np.isfinite(values).all():
        raise ValueError('Calibration needs finite eligible DEV scores')
    return {str(q): float(np.quantile(values, q, method='linear')) if q < 1 else None for q in quantiles}


def recording_scores(window_scores, eligible, record_index, recordings):
    window_scores = np.asarray(window_scores, float)
    eligible = np.asarray(eligible, bool)
    record_index = np.asarray(record_index, int)
    if not (window_scores.shape == eligible.shape == record_index.shape):
        raise ValueError('Window arrays differ')
    result = np.full(recordings, np.inf)
    np.minimum.at(result, record_index[eligible], window_scores[eligible])
    return result, np.isfinite(result)


def threshold_flags(scores, eligible, threshold, q):
    return np.asarray(eligible, bool) & (np.asarray(scores) < threshold if q < 1 else True)
