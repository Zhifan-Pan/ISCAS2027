#!/usr/bin/env python3
"""Read-only evaluation of frozen gate scores under a common HF backend.

This program does NOT train a gate, create missing HF labels, decode audio,
measure latency, perform a significance test, or assign scientific acceptance.
It evaluates stored DEV-threshold flags and a separately labelled retrospective
exact-invocation-count ranking. Use only after exporting real recording-level
scores with verified eligible-window aggregation and a locked model identity.
Python 3.10+ and NumPy; no network access and no subprocess execution.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
from pathlib import Path
from typing import Any, Sequence

import numpy as np


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def check_counts(value: Any, name: str) -> np.ndarray:
    require(isinstance(value, list) and len(value) == 4, f'{name}: need [S,D,I,N]')
    require(all(type(x) is int and x >= 0 for x in value), f'{name}: nonnegative integers only')
    require(value[0] + value[1] <= value[3], f'{name}: S+D exceeds N')
    return np.asarray(value, dtype=np.int64)


def mix_counts(base: np.ndarray, recovery: np.ndarray, flags: np.ndarray) -> np.ndarray:
    require(base.shape == recovery.shape and base.ndim == 2 and base.shape[1] == 4, 'count shapes differ')
    require(flags.shape == (len(base),) and flags.dtype == np.bool_, 'recording boolean flags required')
    require(np.array_equal(base[:, 3], recovery[:, 3]), 'reference denominators differ')
    return np.where(flags[:, None], recovery, base)


def macro_wer(counts: np.ndarray, languages: Sequence[str], seeds: Sequence[int]) -> float:
    """Equal language and checkpoint weight, corpus WER inside each cell."""
    languages = np.asarray(languages)
    seeds = np.asarray(seeds)
    rates = []
    for language in sorted(set(languages.tolist())):
        for seed in sorted(set(seeds.tolist())):
            c = counts[(languages == language) & (seeds == seed)]
            require(len(c) > 0 and c[:, 3].sum() > 0, 'missing cell or zero total reference words')
            rates.append(float(100.0 * c[:, :3].sum() / c[:, 3].sum()))
    return float(np.mean(rates))


def matched_flags(scores: np.ndarray, eligible: np.ndarray, keys: Sequence[str], k: int, salt: str) -> np.ndarray:
    require(scores.shape == eligible.shape == (len(keys),), 'rank input shapes differ')
    require(eligible.dtype == np.bool_, 'eligibility must be boolean')
    require(type(k) is int and 0 <= k <= int(eligible.sum()), 'invalid K')
    require(len(set(keys)) == len(keys), 'duplicate tie identities')
    require(np.isfinite(scores[eligible]).all(), 'eligible scores must be finite')
    candidates = np.flatnonzero(eligible).tolist()
    # Ties use only identity, never outcomes. Same keys can be used across checkpoints.
    def order(i: int) -> tuple[float, str]:
        digest = hashlib.sha256((salt + '|' + keys[i]).encode('utf-8')).hexdigest()
        return float(scores[i]), digest
    selected = sorted(candidates, key=order)[:k]
    out = np.zeros(len(keys), dtype=bool)
    out[selected] = True
    require(int(out.sum()) == k and not np.any(out & ~eligible), 'rank count invariant failed')
    return out


def validate_protocol(p: dict[str, Any]) -> None:
    require(p.get('status') == 'LOCKED', 'protocol is a draft: no evaluation authorized by this file')
    require(p.get('study_kind') == 'retrospective_comparator', 'study kind must be explicit')
    require(p.get('execution_source') == 'HF', 'this adapter expects HF execution')
    require(p.get('score_direction') == 'lower_requests_first', 'unsupported score direction')
    require(p.get('score_aggregation') == 'min_over_eligible_windows', 'recording scores need verified min-over-eligible-window aggregation')
    for key in ('datasets', 'languages', 'checkpoints', 'gate_names', 'quantile_keys'):
        x = p.get(key)
        require(isinstance(x, list) and len(x) > 0 and len(set(x)) == len(x), f'bad protocol {key}')
    require(p.get('primary_gate') in p['gate_names'], 'primary gate absent')
    require(p.get('primary_quantile') in p['quantile_keys'], 'primary q absent')
    require(all(0 < float(q) <= 1 for q in p['quantile_keys']), 'invalid quantile')
    require(len({float(q) for q in p['quantile_keys']}) == len(p['quantile_keys']), 'duplicate numerical quantiles')
    require(p.get('outputs_are_retrospective_not_online_budget_policy') is True, 'rank-budget scope missing')
    require(isinstance(p.get('tie_salt'), str) and p['tie_salt'], 'fixed tie salt missing')
    for key in ('feature_lineage_sha256', 'fitted_model_lock_sha256'):
        v = p.get(key)
        require(isinstance(v, str) and len(v) == 64 and all(c in '0123456789abcdef' for c in v), f'{key} missing/invalid')


def validate_rows(rows: list[dict[str, Any]], p: dict[str, Any]) -> None:
    require(len(rows) > 0, 'empty rows')
    seen: set[tuple[Any, ...]] = set()
    recordings: dict[tuple[Any, ...], dict[int, dict[str, Any]]] = {}
    cells: set[tuple[Any, ...]] = set()
    for r in rows:
        require(r.get('dataset') in p['datasets'], 'unknown dataset')
        require(r.get('lang') in p['languages'], 'unknown language')
        require(type(r.get('seed')) is int and r['seed'] in p['checkpoints'], 'unknown seed')
        for key in ('id', 'cluster'):
            require(isinstance(r.get(key), str) and r[key], f'{key} must be an opaque nonempty string')
        key = (r['dataset'], r['lang'], r['id'], r['seed'])
        require(key not in seen, 'duplicate recording/checkpoint row')
        seen.add(key)
        for name in ('eligible', 'cr_original', 'cr_matched'):
            require(type(r.get(name)) is bool, f'{name} must be boolean')
        require(r['cr_matched'] == (r['cr_original'] and r['eligible']), 'CR matched eligibility differs')
        b, n, s = [check_counts(r.get(name), name) for name in ('B', 'NplusR', 'SplusR')]
        require(b[3] == n[3] == s[3], 'reference denominators differ')
        require(np.array_equal(s, n if r['cr_original'] else b), 'archived SplusR is not reconstructed')
        gates = r.get('gates')
        require(isinstance(gates, dict) and set(gates) == set(p['gate_names']), 'gate set differs')
        for name in p['gate_names']:
            g = gates[name]
            score = g.get('score')
            require((not r['eligible'] and score is None) or (type(score) in (int, float) and np.isfinite(score)), f'{name}: invalid score')
            flags = g.get('flags')
            require(isinstance(flags, dict) and set(flags) == set(p['quantile_keys']), f'{name}: incomplete grid')
            require(all(type(x) is bool for x in flags.values()), 'non-boolean gate flag')
            require(r['eligible'] or not any(flags.values()), 'gate calls an ineligible record')
            ordered = [flags[q] for q in sorted(p['quantile_keys'], key=float)]
            require(all(int(a) <= int(b) for a, b in zip(ordered, ordered[1:])), 'nonmonotone quantile flags')
            for q in p['quantile_keys']:
                if float(q) == 1.0:
                    require(flags[q] == r['eligible'], 'q=1 must select all eligible recordings')
        rec = (r['dataset'], r['lang'], r['id'])
        recordings.setdefault(rec, {})[r['seed']] = r
        cells.add((r['dataset'], r['lang'], r['seed']))
    wanted = {(d, l, s) for d in p['datasets'] for l in p['languages'] for s in p['checkpoints']}
    require(cells == wanted, 'dataset/language/checkpoint cells incomplete')
    for records in recordings.values():
        require(set(records) == set(p['checkpoints']), 'recording missing a checkpoint')
        require(len({x['cluster'] for x in records.values()}) == 1, 'cluster identity changes across checkpoints')
        require(len({x['B'][3] for x in records.values()}) == 1, 'reference count changes across checkpoints')


def evaluate(rows: list[dict[str, Any]], p: dict[str, Any]) -> dict[str, Any]:
    validate_protocol(p)
    validate_rows(rows, p)
    grid, ranked, cells = [], [], []
    for dataset in p['datasets']:
        rr = [r for r in rows if r['dataset'] == dataset]
        lang = np.asarray([r['lang'] for r in rr])
        seed = np.asarray([r['seed'] for r in rr])
        b = np.asarray([r['B'] for r in rr], dtype=np.int64)
        n = np.asarray([r['NplusR'] for r in rr], dtype=np.int64)
        eligible = np.asarray([r['eligible'] for r in rr], dtype=bool)
        cr = np.asarray([r['cr_matched'] for r in rr], dtype=bool)
        orig = np.asarray([r['cr_original'] for r in rr], dtype=bool)
        cr_wer = macro_wer(mix_counts(b, n, cr), lang, seed)
        def describe(policy: str, flags: np.ndarray, view: str, q: str | None = None) -> dict[str, Any]:
            value = macro_wer(mix_counts(b, n, flags), lang, seed)
            return {'dataset': dataset, 'policy': policy, 'view': view, 'q': q,
                    'recording_checkpoint_instances': len(rr), 'calls': int(flags.sum()),
                    'calls_percent': 100.0 * float(flags.mean()), 'macro_wer_percent': value,
                    'delta_vs_CR_matched_pp': value - cr_wer}
        for policy, flags in [('B', np.zeros(len(rr), dtype=bool)), ('NplusR', np.ones(len(rr), dtype=bool)), ('CR_original', orig), ('CR_matched', cr)]:
            grid.append(describe(policy, flags, 'frozen_control'))
        ranked.append(describe('CR_matched', cr, 'equal_invocation_diagnostic'))
        for gate in p['gate_names']:
            for q in p['quantile_keys']:
                flags = np.asarray([r['gates'][gate]['flags'][q] for r in rr], dtype=bool)
                grid.append(describe(gate, flags, 'DEV_threshold', q))
            flags = np.zeros(len(rr), dtype=bool)
            for cp in p['checkpoints']:
                ix = np.flatnonzero(seed == cp)
                scores = np.asarray([rr[i]['gates'][gate]['score'] if rr[i]['gates'][gate]['score'] is not None else np.nan for i in ix])
                keys = [rr[i]['dataset'] + '|' + rr[i]['lang'] + '|' + rr[i]['id'] for i in ix]
                k = int(cr[ix].sum())
                f = matched_flags(scores, eligible[ix], keys, k, p['tie_salt'])
                flags[ix] = f
                cells.append({'dataset': dataset, 'seed': cp, 'gate': gate, 'eligible': int(eligible[ix].sum()),
                              'CR_calls': k, 'gate_calls': int(f.sum()), 'calls_exactly_equal': int(f.sum()) == k})
            ranked.append(describe(gate, flags, 'equal_invocation_diagnostic'))
    return {'status': 'DESCRIPTIVE_EVALUATION_COMPLETE', 'scientific_acceptance': 'NOT_ASSIGNED',
            'scope': 'Frozen HF outcomes; no training, inference, timing, confidence interval, or independence certification.',
            'ranked_view_caveat': 'Uses complete evaluation-panel feature scores and CR-matched K; not an online DEV threshold and not equal latency.',
            'reconstructed_original_rows': len(rows), 'complete_DEV_threshold_grid': grid,
            'equal_invocation_results': ranked, 'equal_budget_checks': cells}


def run(input_path: Path, protocol_path: Path, model_lock_path: Path, feature_path: Path, out: Path) -> dict[str, Any]:
    files = [x.resolve() for x in (input_path, protocol_path, model_lock_path, feature_path)]
    out = out.resolve()
    require(not out.exists(), 'output directory already exists; use a new path')
    require(all(not f.is_relative_to(out) for f in files), 'output would contain input')
    p = json.loads(files[1].read_text(encoding='utf-8'))
    validate_protocol(p)
    require(sha256(files[2]) == p['fitted_model_lock_sha256'], 'model lock hash differs')
    require(sha256(files[3]) == p['feature_lineage_sha256'], 'feature-definition hash differs')
    rows = []
    with files[0].open(encoding='utf-8') as f:
        for line_number, line in enumerate(f, 1):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(f'invalid JSON at row {line_number}') from exc
    result = evaluate(rows, p)
    result['input_sha256'] = {name: sha256(path) for name, path in zip(('rows', 'protocol', 'model_lock', 'feature_definition'), files)}
    result['environment'] = {'python': platform.python_version(), 'numpy': np.__version__}
    out.mkdir(parents=True)
    (out / 'budget_results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    for name, values in [('dev_threshold_grid.csv', result['complete_DEV_threshold_grid']), ('matched_K_results.csv', result['equal_invocation_results'])]:
        with (out / name).open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(values[0]))
            writer.writeheader()
            writer.writerows(values)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rows', type=Path, required=True)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--model-lock', type=Path, required=True)
    parser.add_argument('--feature-definition', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = run(args.rows, args.protocol, args.model_lock, args.feature_definition, args.out)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, f'ERROR: {exc}\n')
    print(json.dumps({'status': result['status'], 'rows': result['reconstructed_original_rows'],
                      'equal_budget_cells': len(result['equal_budget_checks']),
                      'scientific_acceptance': result['scientific_acceptance']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
