# Manuscript revision audit

This audit uses frozen numeric caches and CPU fitting only. No audio decoding, GPU timing or confirmation refitting was run. Original Tables I–III results, Table IV gains/call rates and all confidence intervals remain unchanged. Added values are per-language baseline WERs derived from the original counts and a separately identified retrospective RMS sensitivity analysis.

## Per-language baseline and selective WER

These are equal averages over seeds 101, 202 and 303. Gain is computed before rounding, so subtracting the displayed WERs can differ by 0.01 pp. Calls pool seed–recordings. The 60 language/seed B and S+R SDIN rows agree exactly with the existing manuscript evidence. Full precision, including Raw top-1, is in [PER_LANGUAGE_MEANS.csv](evidence/acceptance_audit/PER_LANGUAGE_MEANS.csv) and [PER_LANGUAGE_SEED.csv](evidence/acceptance_audit/PER_LANGUAGE_SEED.csv).

| TEST | Language | Raw top-1 WER % | B WER % | S+R WER % | Gain pp | Calls % |
|---|---|---:|---:|---:|---:|---:|
| FLEURS | Arabic | 26.50 | 24.84 | 24.20 | 0.64 | 0.23 |
| FLEURS | Persian | 32.44 | 31.08 | 29.88 | 1.20 | 0.27 |
| FLEURS | Polish | 15.16 | 13.57 | 13.57 | 0.00 | 0.00 |
| FLEURS | Turkish | 13.20 | 11.67 | 11.67 | 0.00 | 0.00 |
| FLEURS | Italian | 7.19 | 6.11 | 6.11 | 0.00 | 0.00 |
| CV27 | Arabic | 54.60 | 52.12 | 50.71 | 1.40 | 0.11 |
| CV27 | Persian | 71.61 | 69.02 | 59.97 | 9.05 | 1.15 |
| CV27 | Polish | 17.27 | 14.57 | 14.27 | 0.30 | 0.33 |
| CV27 | Turkish | 22.98 | 20.52 | 20.02 | 0.51 | 0.03 |
| CV27 | Italian | 15.60 | 13.66 | 13.44 | 0.23 | 0.02 |

The supplied draft patch had Arabic FLEURS gain and call rate reversed. Cached counts support **0.64 pp gain and 0.23% calls**, as retained in Table IV. Persian starts at **71.61%** raw CV27 WER and **69.02%** B WER. High WER alone does not establish the cause or frequency of repetition. The script sensitivity of UTF-8/zlib and acoustic causes are not experimentally separated.

## RMS rule and controlled CPU sensitivity

For non-top training-fold differences, the implementation uses

$$s_d^2 = \frac{\sum_{(i,k)\in\mathcal D}\omega_{ik}x_{ik,d}^2}{\sum_{(i,k)\in\mathcal D}\omega_{ik}}.$$

G4 uses $\omega_{ik}=1/[N_\ell(|C_i|-1)]$. Original HF refits use $\omega_{ik}=1$. The original H4/HR4/HWR4 comparisons share HF banks, folds and pooled scaling. G4 versus H4 changes both fitting banks and scaling, so it is not a single-factor source intervention.

The new sensitivity applies G4's **scaling rule** to the HF banks, recomputing it within each training fold. It does not transfer numerical scales from greedy banks. It preserves five folds, the 49-value penalty grid, stronger-penalty tie breaking, objectives, pair weights, zero initialization and L-BFGS-B options. Nine pooled models replayed successfully. All nine weighted models were selected on DEV and locked before TEST evaluation. The run contains **2,223 converged fits**, including nine baseline replays and 2,214 weighted fits. It is retrospective and does not extend confirmation status.

| CV27 complete selective policy | Original pooled RMS WER % | Weighted RMS WER % | Change pp |
|---|---:|---:|---:|
| H4 | 31.523514889571334 | 31.567806373687588 | +0.044291484116254 |
| HR4 | 32.304545986869677 | 32.247960889620778 | -0.056585097248899 |
| HWR4 | 31.439447625870461 | 31.442316350960994 | +0.002868725090533 |

The mean order remains HWR4, H4, HR4. The evidence does **not** support a claim that all changes are below 0.01 pp. The main text reports +0.044, −0.057 and +0.003 pp; [SUMMARY.json](evidence/acceptance_audit/scaling/SUMMARY.json) includes FLEURS, B, complete selective and triggered comparisons. [WER_BY_SEED.csv](evidence/acceptance_audit/scaling/WER_BY_SEED.csv) preserves seed results.

The first TEST evaluation used a wrong cache field (`counts`) and stopped after fitting. It was corrected to the existing `score_selected()` evaluator, which handles `single_counts` and multi-window accounting, then resumed with `--evaluate-only`. No fitting was repeated. The original protocol hash is preserved; the corrected script hash and model-lock hash are recorded in [EVALUATION_FIX_RECEIPT.json](evidence/acceptance_audit/EVALUATION_FIX_RECEIPT.json). Both the failed log and successful evaluation log are retained.

## Checkpoint mechanism

The [fitted coefficients and scales](evidence/acceptance_audit/FITTED_WEIGHTS.csv) contain all four feature weights for G4, H4, HR4 and HWR4 in every checkpoint. The [case-level diagnostic](evidence/acceptance_audit/CHECKPOINT_DIAGNOSTICS.json) contains anonymous IDs, features, edit differences and score contributions, with no transcript or audio content.

| Seed | DEV triggers | TEST triggers | Contrast on triggers | Different selections | Better / worse / equal edits | CV27 change pp |
|---|---:|---:|---|---:|---|---:|
| 101 | 136 | 169 | Direct_minus_G4 | 39 | 33 / 4 / 2 | -0.684509441494694 |
| 101 | 136 | 169 | HWR4_minus_H4 | 0 | 0 / 0 / 0 | +0.000000000000000 |
| 202 | 64 | 105 | Direct_minus_G4 | 2 | 1 / 1 / 0 | +0.001642235372321 |
| 202 | 64 | 105 | HWR4_minus_H4 | 11 | 11 / 0 / 0 | -0.253467494031635 |
| 303 | 241 | 251 | Direct_minus_G4 | 9 | 5 / 4 / 0 | +0.017786890602939 |
| 303 | 241 | 251 | HWR4_minus_H4 | 2 | 1 / 1 / 0 | +0.008452941979330 |

For seed 101, Direct improves 33 of 39 different selections. In all 33 improvements, G4 selects a repetitive beam with a decoder/PLL advantage large enough to override length and repetition penalties. The HF candidate is shorter in 32 of those cases. Thus the evidence does not support the proposed explanation that longer valid recoveries were penalized. Seed 202 accounts for HWR4's −0.25 pp triggered gain over H4: all 11 changed selections replace repetitive beams with shorter HF outputs and fewer edits. These two effects occur on different checkpoints. DEV trigger counts are descriptive, not proof of a causal calibration mechanism.

## Gate, hardware and timing scope

The [provenance receipt](evidence/acceptance_audit/GATE_HARDWARE_PROVENANCE.json) records upstream Whisper URLs, file hashes and exact source excerpts. Whisper's standard text compression threshold is 2.4, with UTF-8 bytes divided by zlib-compressed bytes. HF's 1.35 internal threshold checks serialized token-ID bytes and is a distinct retry criterion. The paper retains log-probability −1 and no-speech 0.6. Recovery was checked on DEV before confirmation, but no threshold-search claim is made.

Historical supervisors expose one GPU UUID to each worker. Runtime tensors use `cuda:0`; CUDA synchronization brackets measurement and allocator peaks are reset per path. Each paired recording block runs on one NVIDIA A40 (48 GB) on the four-card server. Different blocks can use different cards. Reported latency is not a four-GPU model-parallel result; peak memory is the per-process whole-call maximum across recordings and rounds.

Study A and Study B retain distinct sampling scopes. Triggered N+R and S+R perform identical algorithmic operations, but the count shares of later unsampled triggers do not prove a deterministic wall-clock error bound. The manuscript reports Study B's full trigger coverage and the empirical agreement of savings, without inventing a <0.01 pp or <0.2 ms guarantee.

## Source changes and final layout

- `main.tex`: identify the standard fixed gate; explain script-sensitive compression; state the exact RMS rule and explicit RankNet loss; distinguish policies and acceptors; clarify fixed-gate DEV checking and per-block single-GPU execution. Numbered Equations (1)–(3) are unchanged; RankNet is unnumbered.
- `primary.tex`: visually separate the oracle and locked-confirmation panels. Existing numeric cells and reference numbers are unchanged.
- `acceptors.tex`: label the main panel as complete-policy results; define complete versus triggered comparisons in the method. Original numbers and intervals are unchanged.
- `language_scope.tex`: add B baseline WER columns to both datasets. All original gain/call/SDI values are preserved.
- `results.tex`: explain observed score mechanisms, report the CPU scaling sensitivity and Persian baselines, and retain the empty-output insertion/deletion tradeoff and calibration limits.
- Repeated wording was shortened to accommodate the methods without changing IEEEtran, margins, body sizes, baselines, figure size or table row spacing. The conclusion still has two paragraphs. Authors, affiliations, acknowledgment grants, figure and bibliography are unchanged.

The PDF has **five US Letter pages**. Main text and acknowledgment finish on page 4; page 5 starts with REFERENCES and contains references [1]–[33] only. Poppler word-box bottoms for the first seven columns are 718.597–719.292 pt; page 4 right ends at 703.824 pt. No Overfull/Underfull hbox or vbox messages remain. All fonts are embedded, no Type 3 font is used, and hyperlinks/bookmarks remain disabled. Local checks do not replace IEEE PDF eXpress certification.

## Reproduction

Run from the repository root using the documented NumPy/SciPy environment:

```sh
python3 paper/evidence/acceptance_audit/extract_evidence.py --repo . --output /tmp/iscas-evidence-replay
python3 paper/evidence/acceptance_audit/scaling_sensitivity.py --repo . --output /tmp/iscas-rms-replay
```

Use a fresh output directory for the fitting command. It performs the CPU sensitivity experiment; it does not run GPU decoding or modify the original models. The preserved evidence includes the protocol, model lock, all fit logs, OOF picks and final models. Lightweight file, arithmetic and layout checks are reported separately in `CHECKS.json`.

