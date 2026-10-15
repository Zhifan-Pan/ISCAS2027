"""Recompute V119 recovery retention and the fixed retrospective diagnostic."""
from pathlib import Path
import json
import numpy as np

ROOT = Path(__file__).resolve().parent
D = ROOT / 'data'
A = ROOT.parent / 'analyses'


def close(x, y):
    np.testing.assert_allclose(x, y, rtol=0, atol=1e-10)


def macro(c, lang):
    return float(np.mean([100 * c[lang == j, :3].sum() / c[lang == j, 3].sum() for j in range(5)]))


target = json.loads((A / 'helpful_recovery_accounting.json').read_text())['summary']
out = {'status': 'PASS', 'scope': 'Frozen numerical replay; no new predictions or TEST fitting.', 'retention': {}, 'diagnostic': []}
for ds in ['FLEURS', 'CV27']:
    events = missed = lost_edits = 0
    gains, losses, ns, ss = [], [], [], []
    useful_ids = set()
    for seed in [101, 202, 303]:
        with np.load(D / f'COUNTS_{ds}_{seed}.npz', allow_pickle=False) as z, \
             np.load(D / f'NATIVE_RESCORE_COUNTS_{ds}_{seed}.npz', allow_pickle=False) as v:
            np.testing.assert_array_equal(z['ids'], v['ids'])
            b, n, s, lang = z['NoAcquisition'], v['counts'], z['HFFallbackFixed'], z['lang']
            np.testing.assert_array_equal(n[z['flags']], s[z['flags']])
            np.testing.assert_array_equal(b[~z['flags']], s[~z['flags']])
            be, ne, se = [x[:, :3].sum(1) for x in [b, n, s]]
            useful = ne < be
            loss = np.where(useful, np.maximum(se - ne, 0), 0)
            events += int(useful.sum())
            missed += int((loss > 0).sum())
            lost_edits += int(loss.sum())
            useful_ids.update(str(x) for x in z['ids'][useful])
            gains.append(float(np.mean([100 * np.maximum(be - ne, 0)[lang == j].sum() / b[lang == j, 3].sum() for j in range(5)])))
            losses.append(float(np.mean([100 * loss[lang == j].sum() / b[lang == j, 3].sum() for j in range(5)])))
            ns.append(macro(n, lang))
            ss.append(macro(s, lang))
    result = {'useful_events': events, 'missed_events': missed, 'lost_edits': lost_edits,
              'macro_loss_pp': float(np.mean(losses)), 'macro_retention': 1 - float(np.mean(losses)) / float(np.mean(gains)),
              'NplusR_WER': float(np.mean(ns)), 'SplusR_WER': float(np.mean(ss)),
              'distinct_useful_recordings': len(useful_ids)}
    for k, expected_key in [('useful_events', 'useful_event_instances'), ('missed_events', 'useful_missed_instances'),
                            ('lost_edits', 'beneficial_word_edits_lost'), ('macro_loss_pp', 'macro_beneficial_loss_pp'),
                            ('macro_retention', 'macro_weighted_beneficial_edit_retention'),
                            ('NplusR_WER', 'macro_NplusR_WER'), ('SplusR_WER', 'macro_SplusR_WER')]:
        close(result[k], target[ds][expected_key])
    if ds == 'CV27':
        with np.load(D / 'CV27_COMPONENTS.npz', allow_pickle=False) as meta:
            ix = np.isin(meta['ids'], list(useful_ids))
            result['distinct_useful_client_reference_components'] = len(set(zip(meta['lang'][ix].tolist(), meta['components'][ix].tolist())))
    out['retention'][ds] = result

rows = [json.loads(line) for line in (A / 'acceptance_feature_rows.jsonl').open()]
expected = json.loads((A / 'acceptance_score_intervention.json').read_text())
for seed in [101, 202, 303]:
    rs = [r for r in rows if r['checkpoint'] == seed and r['source'] == 'HFFallback']
    with np.load(D / f'COUNTS_CV27_{seed}.npz', allow_pickle=False) as z:
        where = {str(uid): i for i, uid in enumerate(z['ids'])}
        counts = z['NoAcquisition'].copy()
        assert len(rs) == z['flags'].sum()
        for row in rs:
            close(sum(row['contribution']), row['margin'])
            assert row['accepted'] == bool(row['new'] and row['margin'] > 0)
            if row['new'] and row['margin'] - row['contribution'][0] > 0:
                i = where[row['id']]
                counts[i] = z['HFFallbackDirect'][i]
        score = macro(counts, z['lang'])
        match = next(v for v in expected['per_checkpoint'] if v['checkpoint'] == seed)
        close(score, match['diagnostic_WER'])
        out['diagnostic'].append({'seed': seed, 'WER': score})
    if seed == 101:
        rejected = [r for r in rs if r['new'] and not r['accepted'] and r['source_useful']]
        assert len(rejected) == 33 and all(int(np.argmin(r['contribution'])) == 0 for r in rejected)

(ROOT / 'V119_REPLAY.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps(out))
