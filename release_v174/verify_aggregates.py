#!/usr/bin/env python3
"""Recompute descriptive aggregates from V168 counts; no fits or bootstrap."""
from collections import defaultdict
import csv
import json
from math import isclose
from pathlib import Path
from statistics import mean


def main():
    root = Path(__file__).resolve().parent / "evidence"
    summary = json.loads((root / "COUNT_SUMMARY.json").read_text())

    def read_csv(name):
        with (root / name).open(newline="") as stream:
            return list(csv.DictReader(stream))

    checks = 0

    def same(actual, expected, name):
        nonlocal checks
        if not isclose(actual, expected, rel_tol=0, abs_tol=1e-10):
            raise SystemExit(f"Mismatch: {name}: {actual} != {expected}")
        checks += 1

    cells = defaultdict(dict)
    for row in read_csv("language_seed_SDIN.csv"):
        key = (row["dataset"], row["policy"])
        cell = (row["checkpoint"], row["language"])
        if cell in cells[key]:
            raise SystemExit(f"Duplicate cell: {key}, {cell}")
        value = 100 * sum(int(row[k]) for k in ("S", "D", "I")) / int(row["N"])
        same(value, float(row["WER"]), f"WER {key}, {cell}")
        cells[key][cell] = value

    grid = {(str(seed), lang) for seed in (101, 202, 303)
            for lang in ("ar", "fa", "pl", "tr", "it")}
    for dataset, data in summary.items():
        for policy, expected in data["macro_WER"].items():
            values = cells[dataset, policy]
            if set(values) != grid:
                raise SystemExit(f"Incomplete language/seed grid: {dataset}, {policy}")
            same(mean(values.values()), expected, f"macro WER {dataset} {policy}")
            non_persian = mean(v for (_, lang), v in values.items() if lang != "fa")
            same(non_persian, data["non_Persian_macro_WER"][policy],
                 f"non-Persian WER {dataset} {policy}")
        base, selective = cells[dataset, "B"], cells[dataset, "SplusR"]
        gain = mean(base[c] - selective[c] for c in grid)
        same(gain, data["B_to_SplusR_gain_pp"], f"gain {dataset}")
        persian_gain = mean(base[c] - selective[c] for c in grid if c[1] == "fa")
        same(persian_gain, data["Persian_gain_pp"], f"Persian gain {dataset}")
        same(100 * persian_gain / (5 * gain), data["Persian_share_percent"],
             f"Persian share {dataset}")
        for leave in data["leave_one_language_out"]:
            subset = [c for c in grid if c[1] != leave["excluded_language"]]
            same(mean(base[c] for c in subset), leave["B"], f"leave-out B {dataset}")
            same(mean(selective[c] for c in subset), leave["SplusR"],
                 f"leave-out S+R {dataset}")
            same(mean(base[c] - selective[c] for c in subset), leave["gain_pp"],
                 f"leave-out gain {dataset}")
            if leave["excluded_language"] == "fa":
                same(leave["gain_pp"], data["non_Persian_gain_pp"],
                     f"non-Persian gain {dataset}")

    retention = read_csv("retention_denominators.csv")
    instances = read_csv("instances.csv")
    for dataset in ("FLEURS", "CV27"):
        rows = [r for r in retention if r["dataset"] == dataset]
        if len(rows) != len(grid) or {
                (r["checkpoint"], r["language"]) for r in rows} != grid:
            raise SystemExit(f"Incomplete retention grid: {dataset}")
        gain = mean(int(r["beneficial_edits"]) / int(r["reference_words"]) for r in rows)
        loss = mean(int(r["lost_beneficial_edits"]) / int(r["reference_words"]) for r in rows)
        g = sum(int(r["beneficial_edits"]) for r in rows)
        lost = sum(int(r["lost_beneficial_edits"]) for r in rows)
        result = summary[dataset]["retention"]
        for name, value in {
            "macro_gain_pp": 100 * gain, "macro_loss_pp": 100 * loss,
            "macro_retained_gain_pp": 100 * (gain - loss),
            "macro_retention_percent": 100 * (1 - loss / gain),
            "pooled_positive_edits": g, "pooled_lost_edits": lost,
            "pooled_retained_edits": g - lost,
            "pooled_retention_percent": 100 * (1 - lost / g),
        }.items():
            same(value, result[name], f"{dataset} {name}")
        sample = [r for r in instances if r["dataset"] == dataset]
        helpful = sum(int(r["helpful"]) for r in sample)
        missed = sum(int(r["missed_helpful"]) for r in sample)
        same(helpful, result["helpful_instances"], f"{dataset} helpful")
        same(helpful - missed, result["retained_helpful_instances"],
             f"{dataset} retained helpful")
        same(100 * sum(int(r["triggers"]) for r in sample)
             / sum(int(r["instances"]) for r in sample),
             result["call_rate_percent"], f"{dataset} calls")
    print(f"Verified {checks} aggregate arithmetic comparisons.")
    print("No training, inference, bootstrap or timing experiment was run.")


if __name__ == "__main__":
    main()
