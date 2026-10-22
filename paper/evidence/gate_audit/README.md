# Retrospective comparison of outer acquisition gates

This audit changes only the outer acquisition gate on the original cached TEST banks. G4, the B and N+R choices, candidate draws, normalization, references, and the original five-language/three-checkpoint aggregation remain fixed. It performs no GPU inference, refitting, runtime measurement, or new confirmation.

| Outer gate | FLEURS calls (%) | FLEURS WER (%) | FLEURS positive-gain retention (%) | CV27 calls (%) | CV27 WER (%) | CV27 positive-gain retention (%) |
|---|---:|---:|---:|---:|---:|---:|
| UTF-8 text CR > 2.4 | 0.0909504320 | 17.0867202362 | 100.0000000000 | 0.2990737259 | 31.6809556946 | 99.9825813678 |
| Word repetition r4,3 > 0 | 0.0636653024 | 17.1111814227 | 93.3414668804 | 0.1834318852 | 31.6953937814 | 99.2076394332 |
| Token-ID byte CR > 1.35 | 0.2000909504 | 17.0867202362 | 100.0000000000 | 0.3087580180 | 31.6806899739 | 99.9941243095 |

The word gate saves calls but misses some of the gains recovered by the original gate. The token-ID gate retains all observed positive gain on FLEURS and slightly more than the original gate on CV27, with additional calls. These results establish a tradeoff on these cached panels, not universal optimality of the original threshold. No threshold was selected or tuned against these TEST outcomes.

## Exact denominators and aggregation

- FLEURS has 10,995 seed-recordings and 11,061 seed-windows. The three gates trigger 10, 7, and 22 seed-recordings, respectively; recording routing acquires 15, 12, and 27 seed-windows.
- CV27 has 175,542 seed-recordings/windows. The three gates trigger 525, 322, and 542, respectively.
- Each recording is triggered when any of its windows satisfies the corresponding gate. All its windows then use N+R choices; otherwise all use B choices. Complete-recording alignments, including the existing joint two-window lookup for FLEURS, determine S/D/I counts.
- WER is computed from summed edits and reference words within each language, then averaged equally across five languages and three fixed checkpoints.
- Positive-gain retention is the ratio of retained to available positive B-to-N+R edit gain after language-reference normalization and equal language/checkpoint weighting. It is **not** the pooled-edit ratio or an unweighted average of seed-level retention percentages. `RESULT.json` records the exact definition.
- On FLEURS the original, word, and token gates retain 10/10, 7/10, and 10/10 beneficial seed-recordings. On CV27 they retain 370/373, 285/373, and 371/373. Positive edit totals and language denominators are in the CSV files.

## Feature provenance and implementation

The feature extractor verifies original feature JSONL hashes against the frozen `CACHE_INDEX.json`, all 132 full-audio window-cache hashes against `FULL_AUDIO_BANKS_READY.json`, and row alignment against the immutable original B/S count caches. It exports no transcripts, token-ID sequences, audio, or references.

Every raw UTF-8 compression ratio exactly matches the previously exported `cr_window`; every raw word-repetition score exactly matches `raw_features[:,0,3]`. Centered `x[:,0,3]` is zero and is **not** used as repetition evidence. The original recording flags and all B/N/S picks and integer counts reproduce exactly for all six panels.

Token compression follows the frozen Transformers 4.57.6 `_retrieve_compression_ratio` function: vocabulary size 51,865 determines two bytes per token, little-endian, with default zlib compression. Cached top-beam token sequences exclude the decoder prefix and terminal EOS. The extractor restores exactly one EOS when `termination=natural_eos` and none when `termination=length_cap`, matching the sequence used by HF before its fallback check. All 186,603 top-beam window records have an explicit supported termination value. The extractor executes the original function parsed from the hash-verified source and checks exact ratio equality for every window.

This is an alternative **outer** gate applying HF's compression calculation to the frozen top beam. It is not the full HF internal policy, which also checks probability/no-speech and later retry candidates. Tokenization itself remains language dependent; token-ID compression must not be described as a proven script-independent or bias-free gate. Cached candidate draws are reused; this experiment does not assume that newly executed stochastic decoding under a different request schedule would reproduce those draws.

## Reproduction

From the repository root, replay using the public numeric exports:

```bash
python3 paper/evidence/gate_audit/compare_gates.py --repo . --output paper/evidence/gate_audit
python3 paper/evidence/gate_audit/verify_gate_audit.py --repo .
```

The optional private-source extraction is reproducible in the author environment:

```bash
python3 paper/evidence/gate_audit/extract_gate_features.py --repo . --author-root /home/mhmt_stu/Code/paper-qwen-projector-icassp2027 --output paper/evidence/gate_audit
```

`PER_LANGUAGE_SEED.csv` contains full language/seed S/D/I/reference counts. `PER_SEED.csv`, `SUMMARY.csv`, and `RESULT.json` contain exact floating-point aggregates, controls, and input hashes. The replay NPZ files hold row-level counts and Boolean gates. `PRIVATE_SOURCE_RECEIPT.json` preserves the input provenance and extraction checks without transcript content.
