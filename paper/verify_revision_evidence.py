#!/usr/bin/env python3
"""Check added baseline/scaling evidence; no fitting or GPU execution."""
import csv
import hashlib
import json
from math import isclose
from pathlib import Path
from statistics import mean


def main():
    paper = Path(__file__).resolve().parent
    audit = paper / 'evidence/acceptance_audit'
    repo = paper.parent
    checks = 0

    def check(ok, name):
        nonlocal checks
        if not ok:
            raise SystemExit('Mismatch: ' + name)
        checks += 1

    def same(a, b, name):
        check(isclose(a, b, rel_tol=0, abs_tol=1e-10), name)

    def rows(path):
        with path.open(newline='') as stream:
            return list(csv.DictReader(stream))

    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    seed_rows = rows(audit / 'PER_LANGUAGE_SEED.csv')
    original = {(r['dataset'], r['checkpoint'], r['language'], r['policy']): r
                for r in rows(paper / 'evidence/language_seed_SDIN.csv')}
    check(len(seed_rows) == 90, 'three policies x two datasets x five languages x three seeds')
    for row in seed_rows:
        same(100 * sum(int(row[k]) for k in ('S', 'D', 'I')) / int(row['N']),
             float(row['WER']), 'SDIN-derived WER')
        if row['policy'] != 'RawTop1':
            old = original[tuple(row[k] for k in ('dataset', 'checkpoint', 'language', 'policy'))]
            check(all(row[k] == old[k] for k in ('S', 'D', 'I', 'N')), 'original SDIN identity')
    table = (paper / 'source/language_scope.tex').read_text()
    means = rows(audit / 'PER_LANGUAGE_MEANS.csv')
    for row in means:
        subset = [r for r in seed_rows if (r['dataset'], r['language']) == (row['dataset'], row['language'])]
        for policy in ('RawTop1', 'B', 'SplusR'):
            values = [r for r in subset if r['policy'] == policy]
            check(len(values) == 3, 'complete seed grid')
            same(mean(float(r['WER']) for r in values), float(row[policy + '_WER']), 'language mean')
        same(float(row['B_WER']) - float(row['SplusR_WER']), float(row['Gain_pp']), 'unrounded gain')
        values = [r for r in subset if r['policy'] == 'B']
        same(100 * sum(int(r['triggers']) for r in values) / sum(int(r['recordings']) for r in values),
             float(row['Calls_pct']), 'pooled calls')
    for language, label in {'ar': 'Arabic', 'fa': 'Persian', 'pl': 'Polish', 'tr': 'Turkish', 'it': 'Italian'}.items():
        values = []
        for dataset in ('FLEURS', 'CV27'):
            row = next(r for r in means if r['language'] == language and r['dataset'] == dataset)
            values.extend(f'{float(row[k]):.2f}' for k in ('B_WER', 'Gain_pp', 'Calls_pct'))
        check(label + ' & ' + ' & '.join(values) + r'\\' in table, 'Table IV ' + label)

    scaling = audit / 'scaling'
    lock = json.loads((scaling / 'MODEL_LOCK.json').read_text())
    fits = 0
    for model, expected in lock.items():
        check(digest(scaling / model / 'model.json') == expected, 'model lock')
        log = [json.loads(line) for line in (scaling / model / 'fit_log.jsonl').read_text().splitlines()]
        check(len(log) == 247 and all(r['success'] for r in log), 'fit convergence')
        fits += len(log)
    summary = json.loads((scaling / 'SUMMARY.json').read_text())
    check(fits == summary['converged_fits'] == 2223, 'total fits')
    results = rows(scaling / 'WER_BY_SEED.csv')
    for row in summary['results']:
        for rule in ('pooled', 'weighted'):
            values = [float(r['WER']) for r in results if
                      all(r[k] == row[k] for k in ('dataset', 'family', 'policy')) and r['scaling'] == rule]
            check(len(values) == 3, 'scaling seed grid')
            same(mean(values), row[rule], 'scaling mean')
        same(row['weighted'] - row['pooled'], row['change_pp'], 'scaling contrast')
    receipt = json.loads((audit / 'EVALUATION_FIX_RECEIPT.json').read_text())
    check(digest(audit / 'scaling_sensitivity.py') == receipt['corrected_script_sha256'], 'evaluation adapter receipt')
    for path, expected in json.loads((audit / 'INPUT_SHA256.json').read_text()).items():
        check(digest(repo / path) == expected, 'frozen input ' + path)
    print(f'Passed {checks} added-evidence checks; original counts and locked CPU models preserved.')


if __name__ == '__main__':
    main()
