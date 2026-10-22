"""CPU-only DEV trigger census and bounded unadapted-model metadata inventory.

DEV inputs are frozen LoRA-adapted caches, not unadapted Whisper outputs.
No model fitting, decoding, or network access is performed.
"""
import argparse
import csv
import hashlib
import json
import os
import re
from pathlib import Path

os.environ["CUDA_VISIBLE_DEVICES"] = ""
import numpy as np


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--history-root", type=Path)
    args = parser.parse_args()
    repo, output = args.repo.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    languages = ["ar", "fa", "pl", "tr", "it"]
    rows, inputs = [], {}
    for seed in (101, 202, 303):
        path = repo / f"experiments/acceptors/inputs/DEV_{seed}.npz"
        inputs[str(path.relative_to(repo))] = sha(path)
        with np.load(path, allow_pickle=False) as data:
            ids, lang, flags = data["ids"], data["lang"], data["flags"]
            assert len(np.unique(ids)) == len(ids)
            assert flags.dtype == bool
            for index, language in enumerate(languages):
                selection = lang == index
                recordings = int(selection.sum())
                triggers = int(flags[selection].sum())
                rows.append(dict(checkpoint=seed, language=language,
                                 recordings=recordings, triggers=triggers,
                                 call_rate_percent=100.0 * triggers / recordings))
            rows.append(dict(checkpoint=seed, language="pooled", recordings=len(ids),
                             triggers=int(flags.sum()),
                             call_rate_percent=100.0 * flags.mean()))
    with (output / "DEV_TRIGGER_RATES.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    means = []
    for language in languages + ["pooled"]:
        selected = [row for row in rows if row["language"] == language]
        n = sum(row["recordings"] for row in selected)
        t = sum(row["triggers"] for row in selected)
        means.append(dict(language=language, seed_recordings=n, trigger_instances=t,
                          pooled_call_rate_percent=100.0 * t / n,
                          mean_seed_call_rate_percent=float(np.mean([
                              row["call_rate_percent"] for row in selected]))))
    provenance = dict(inputs_sha256=inputs, language_order=languages,
                      language_map_source="paper/evidence/acceptance_audit/extract_evidence.py",
                      gate="cached flags: recording-level max of UTF-8 text CR > 2.4",
                      dataset="CV27 DEV", adapted_model=True,
                      denominator="unique recording IDs within language and checkpoint",
                      pooled_unit="seed-recording (three checkpoints)",
                      language_mean_rates=means)
    (output / "DEV_TRIGGER_PROVENANCE.json").write_text(json.dumps(provenance, indent=2) + "\n")
    selectors_path = repo / "reproduction/config/SELECTORS.json"
    selectors = json.loads(selectors_path.read_text())["checkpoints"]
    feature_sources = {str(selectors_path.relative_to(repo)): sha(selectors_path)}
    feature_rows = []
    for dataset in ("DEV", "CV27", "FLEURS"):
        for seed in (101, 202, 303):
            path = repo / f"experiments/acceptors/inputs/{dataset}_{seed}.npz"
            feature_sources[str(path.relative_to(repo))] = sha(path)
            with np.load(path, allow_pickle=False) as data:
                features = data["raw_features"]
                valid = np.arange(features.shape[1])[None, :] < data["k"][:, None]
                observed = valid & data["raw_observed"].all(axis=2)
                positive_length = observed & (features[:, :, 2] > 0)
                zero_length = observed & (features[:, :, 2] == 0)
                zero_vector = observed & ~(features != 0).any(axis=2)
                window_flags = (data["flags"][data["window_owner"]]
                                if "window_owner" in data else data["flags"])
                beta = np.asarray(selectors[str(seed)]["F"]["raw_beta"])
                assert (np.sign(beta) == [1, 1, -1, -1]).all()
                scores = features @ beta
                feature_rows.append(dict(
                    dataset=dataset, checkpoint=seed,
                    valid_candidates=int(valid.sum()),
                    observed_candidates=int(observed.sum()),
                    positive_length_observed=int(positive_length.sum()),
                    positive_a_violations=int((positive_length & (features[:, :, 0] > 0)).sum()),
                    positive_p_violations=int((positive_length & (features[:, :, 1] > 0)).sum()),
                    negative_r_violations=int((positive_length & (features[:, :, 3] < 0)).sum()),
                    negative_t_violations=int((observed & (features[:, :, 2] < 0)).sum()),
                    nonnegative_score_violations=int((positive_length & (scores >= 0)).sum()),
                    largest_positive_length_score=float(scores[positive_length].max()),
                    zero_length_observed=int(zero_length.sum()),
                    zero_vectors_observed=int(zero_vector.sum()),
                    zero_vectors_in_beams=int((zero_vector & (np.arange(features.shape[1])[None, :] < data["k_beam"][:, None])).sum()),
                    zero_vectors_on_triggered_windows=int((zero_vector & window_flags[:, None]).sum()),
                    valid_missing_body_tokens=int((valid & (data["body_tokens"] < 0)).sum()),
                    positive_length_missing_body_tokens=int((positive_length & (data["body_tokens"] < 0)).sum()),
                    zero_vector_missing_body_tokens=int((zero_vector & (data["body_tokens"] < 0)).sum()),
                    beta=beta.tolist()))
    feature_audit = dict(sources_sha256=feature_sources, rows=feature_rows,
                         scope="Only valid, fully observed raw feature vectors are used for feature-sign checks. Skipped singleton scores are not observed evidence.",
                         surface_text_caveat="Numeric cache has no raw transcripts; body_tokens=-1 means missing, not an empty body. Empty normalized text and zero feature vectors must not be assumed equivalent.")
    (output / "EMPTY_ALGEBRA_AUDIT.json").write_text(json.dumps(feature_audit, indent=2) + "\n")
    if args.history_root:
        history = args.history_root.resolve()
        roots = [repo / "experiments", repo / "reproduction",
                 history / "research_archive", history / "acceptor_study_return",
                 history / "final_decision_return"]
        candidates = set(p for p in history.iterdir() if p.is_file())
        excluded = {".git", "__pycache__", "validation", "reviewer_artifact",
                    "paper_source", "review_trio", "review_round_1", "review_round_2"}
        for root in roots:
            for directory, dirs, files in os.walk(root):
                dirs[:] = [d for d in dirs if d not in excluded]
                candidates.update(Path(directory) / name for name in files)
        extensions = {".json", ".csv", ".md", ".log", ".py", ".yaml", ".yml", ".txt"}
        pattern = re.compile(r"unadapted|un[-_ ]?finetuned|zero[-_ ]?shot|zeroshot|pretrained.{0,60}wer|wer.{0,60}pretrained|base.{0,15}whisper|whisper.{0,15}base", re.I)
        scanned, matches, skipped = [], [], []
        for path in sorted(candidates):
            if path.suffix.lower() not in extensions:
                continue
            size = path.stat().st_size
            if size > 2_000_000:
                skipped.append(dict(path=str(path), bytes=size, reason="size limit"))
                continue
            raw = path.read_bytes()
            scanned.append(dict(path=str(path), bytes=size,
                                sha256=hashlib.sha256(raw).hexdigest()))
            for number, line in enumerate(raw.decode("utf-8", errors="replace").splitlines(), 1):
                if pattern.search(line):
                    matches.append(dict(path=str(path), line=number, text=line))
        result = dict(scope_roots=[str(p) for p in roots], root_files=str(history),
                      excluded_directory_names=sorted(excluded),
                      extensions=sorted(extensions), pattern=pattern.pattern,
                      scanned_files=scanned, matches=matches, skipped=skipped,
                      limit="Keyword search of bounded text metadata, not proof that no unadapted run exists anywhere.")
        (output / "BASE_MODEL_SEARCH.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(dict(scanned=len(scanned), matches=len(matches), skipped=len(skipped))))
    print(json.dumps(means, indent=2))


if __name__ == "__main__":
    main()
