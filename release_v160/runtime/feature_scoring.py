"""Frozen a/t/r scoring, with an explicit separate four-feature PLL branch.

The no-PLL branch returns three coordinates, never a fabricated zero p value.
This module has no model loader. The caller controls model residency.
"""
import math
from collections import Counter
import numpy as np


def score_raw(engine, normalizer, candidate, window, language, counts,
              mode, pll=None):
    if mode not in ('G4', 'H3'):
        raise ValueError(mode)
    logps, mask = engine.logps(window['feat'], window['mask'], language,
                              candidate['token_ids'], window['enc'])
    counts['teacher_calls'] += 1
    body = np.asarray(logps, dtype=float)[np.asarray(mask, dtype=bool)]
    words = normalizer.words(candidate['text'], language)
    grams = [tuple(words[j:j+4]) for j in range(max(0, len(words)-3))]
    freq = Counter(grams)
    repetition = sum(freq[g] >= 3 for g in grams) / max(1, len(grams))
    a = float(body.mean()) if len(body) else 0.
    t = math.log1p(len(body))
    if mode == 'H3':
        return np.asarray([a, t, float(repetition)], dtype=float)
    if pll is None:
        raise RuntimeError('G4 requires the original PLL scorer')
    p = pll.score_text(candidate['text'])
    counts['PLL_calls'] += 1
    counts['PLL_tokens'] += int(p['ntokens'])
    return np.asarray([a, float(p['pll']), t, float(repetition)], dtype=float)
