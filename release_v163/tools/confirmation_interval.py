#!/usr/bin/env python3
"""One locked, post-lock Direct-minus-S diagnostic; no inference or fitting."""
import argparse
import collections
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path

import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--protocol', type=Path, required=True)
    ap.add_argument('--output-dir', type=Path, required=True)
    args = ap.parse_args()
    lock = json.loads(args.protocol.read_text())
    for item in lock['inputs']:
        assert sha(item['path']) == item['sha256'], item['path']
    assert sha(__file__) == lock['script_sha256']
    args.output_dir.mkdir(parents=True, exist_ok=False)
    rows = [json.loads(line) for line in Path(lock['scores']).open()]
    assert len(rows) == 22500
    langs_export = ['ar', 'fa', 'pl', 'tr', 'it']
    seeds = lock['checkpoints']
    policies = ['B', 'Native', 'NplusR', 'SplusR', 'Direct_postlock']
    aligned, counts, details = {}, {}, []
    fixed_keys = None
    for seed in seeds:
        rr = sorted((r for r in rows if r['seed'] == seed),
                    key=lambda r: (langs_export.index(r['lang']), r['id']))
        keys = [(r['lang'], r['id'], r['speaker_key']) for r in rr]
        assert len(rr) == len(set(keys)) == 7500
        if fixed_keys is None:
            fixed_keys = keys
        else:
            assert keys == fixed_keys
        with np.load(Path(lock['count_dir']) / f'counts_{seed}.npz', allow_pickle=False) as z:
            c = {key: z[key].copy() for key in z.files}
        np.testing.assert_array_equal(c['ids'], [f'CF{i:05d}' for i in range(7500)])
        np.testing.assert_array_equal(c['lang'], [langs_export.index(r['lang']) for r in rr])
        np.testing.assert_array_equal(c['flags'], [r['outer_trigger'] for r in rr])
        for p in policies[:-1]:
            expected = np.asarray([[r[p][k] for k in ['S', 'D', 'I', 'N']] for r in rr])
            np.testing.assert_array_equal(c[p], expected)
        np.testing.assert_array_equal(c['Direct_postlock'],
                                      np.where(c['flags'][:, None], c['Native'], c['B']))
        np.testing.assert_array_equal(c['SplusR'], c['NplusR'])
        for p in policies:
            assert c[p].shape == (7500, 4) and (c[p] >= 0).all()
            np.testing.assert_array_equal(c[p][:, 3], c['B'][:, 3])
        aligned[seed], counts[seed] = rr, c
        for lang in langs_export:
            mask = c['lang'] == langs_export.index(lang)
            for p in policies:
                sums = c[p][mask].sum(0)
                details.append(dict(checkpoint=seed, language=lang, policy=p,
                                    S=int(sums[0]), D=int(sums[1]), I=int(sums[2]),
                                    N=int(sums[3]), WER=100 * float(sums[:3].sum() / sums[3])))

    # Same language order, sorted speaker groups, and RNG as the original panel
    # analysis. Resampling is synchronized across checkpoints and policies.
    rng = np.random.default_rng(lock['rng_seed'])
    boot = np.zeros(lock['resamples'], dtype=np.float64)
    clusters_per_language = {}
    for lang in sorted(langs_export):
        grouped = collections.defaultdict(list)
        for i, r in enumerate(aligned[seeds[0]]):
            if r['lang'] == lang:
                grouped[r['speaker_key']].append(i)
        groups = [grouped[k] for k in sorted(grouped)]
        n = len(groups)
        clusters_per_language[lang] = n
        draws = rng.integers(0, n, size=(lock['resamples'], n))
        for seed in seeds:
            c = counts[seed]
            deltas = c['Direct_postlock'][:, :3].sum(1) - c['SplusR'][:, :3].sum(1)
            errors = np.asarray([deltas[g].sum() for g in groups])
            tokens = np.asarray([c['SplusR'][g, 3].sum() for g in groups])
            denom = tokens[draws].sum(1)
            assert (denom > 0).all()
            boot += 100 * errors[draws].sum(1) / denom / len(seeds) / len(langs_export)
    means = {p: float(np.mean([d['WER'] for d in details if d['policy'] == p]))
             for p in policies}
    per_seed = []
    for seed in seeds:
        c = counts[seed]
        ed = c['Direct_postlock'][:, :3].sum(1) - c['SplusR'][:, :3].sum(1)
        per_seed.append(dict(checkpoint=seed, triggers=int(c['flags'].sum()),
                             differences_outside_trigger=int(np.count_nonzero(ed[~c['flags']])),
                             direct_improves=int((ed < 0).sum()), direct_worsens=int((ed > 0).sum()),
                             delta_pp=float(np.mean([d['WER'] for d in details if d['checkpoint'] == seed and d['policy'] == 'Direct_postlock']) -
                                            np.mean([d['WER'] for d in details if d['checkpoint'] == seed and d['policy'] == 'SplusR']))))
    assert all(x['differences_outside_trigger'] == 0 for x in per_seed)
    interval = np.percentile(boot, [2.5, 97.5]).tolist()
    result = dict(scope=lock['scope'], comparison=lock['comparison'],
                  protocol_sha256=sha(args.protocol), script_sha256=sha(__file__),
                  inputs=lock['inputs'], completed_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                  validated_seed_recordings=22500, original_policies_SDIN_reconstructed=True,
                  frozen_N_S_exact_SDIN_equal=True, clusters_per_language=clusters_per_language,
                  macro_WER_percent=means, delta_pp=means['Direct_postlock'] - means['SplusR'],
                  interval_95_pp=interval, interval_contains_zero=interval[0] <= 0 <= interval[1],
                  resamples=lock['resamples'], rng_seed=lock['rng_seed'],
                  per_checkpoint=per_seed, new_fits=False, new_model_forward=False,
                  original_statistical_families_changed=False,
                  interpretation='Post-lock, two-sided descriptive paired interval conditional on the observed speaker-clustered panel and three checkpoints; no new confirmation or proof of equivalence.')
    (args.output_dir / 'RESULT.json').write_text(json.dumps(result, indent=2) + '\n')
    with (args.output_dir / 'per_language_SDIN.csv').open('w') as f:
        w = csv.DictWriter(f, fieldnames=list(details[0]))
        w.writeheader()
        w.writerows(details)
    np.savez_compressed(args.output_dir / 'paired_bootstrap.npz', delta_pp=boot)
    print(json.dumps({k: result[k] for k in ['delta_pp', 'interval_95_pp', 'interval_contains_zero', 'per_checkpoint']}, indent=2))


if __name__ == '__main__':
    main()
