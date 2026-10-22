# Manuscript revision audit

This audit uses frozen caches and CPU analysis only. No audio decoding, GPU timing or confirmation refitting was run. Original Tables I–III results, Table IV gains/call rates and all confidence intervals remain unchanged. Retained evidence comprises per-language baseline WERs from the original counts, retrospective RMS sensitivity, and an offline comparison of acquisition gates. The current editorial revision runs no new fitting or decoding and leaves those evidence files unchanged.

## Cached gate comparison and domain audit

The [gate audit](evidence/gate_audit/README.md) changes only the acquisition gate on six frozen TEST panels. G4 weights, B/N+R picks, candidate draws and complete-recording alignments remain fixed. FLEURS routing uses the maximum window trigger before selecting every window of a recording. No TEST threshold search was conducted. These comparisons are retrospective and do not extend the locked confirmation or timing claims.

| Gate | FLEURS calls % | FLEURS WER % | Positive-gain retention % | CV27 calls % | CV27 WER % | Positive-gain retention % |
|---|---:|---:|---:|---:|---:|---:|
| UTF-8 text CR > 2.4 | 0.0909504320 | 17.0867202362 | 100.0000000000 | 0.2990737259 | 31.6809556946 | 99.9825813678 |
| Word repetition r4,3 > 0 | 0.0636653024 | 17.1111814227 | 93.3414668804 | 0.1834318852 | 31.6953937814 | 99.2076394332 |
| Token-ID byte CR > 1.35 | 0.2000909504 | 17.0867202362 | 100.0000000000 | 0.3087580180 | 31.6806899739 | 99.9941243095 |

The respective recording trigger counts are 10/7/22 of 10,995 FLEURS seed-recordings and 525/322/542 of 175,542 CV27 seed-recordings. The word gate reduces calls but misses some positive recovery gain. The token gate preserves slightly more gain with extra calls; this does not establish universal optimality of either gate. Tokenization remains language dependent. [SUMMARY.csv](evidence/gate_audit/SUMMARY.csv), [PER_LANGUAGE_SEED.csv](evidence/gate_audit/PER_LANGUAGE_SEED.csv) and [RESULT.json](evidence/gate_audit/RESULT.json) retain full precision and exact denominators. The independent review confirmed prefix/EOS handling and the HF two-byte little-endian compression calculation. All 423 route, count, denominator and identity checks passed.

The [domain audit](evidence/domain_audit/README.md) found no verified unadapted Whisper-small evaluation in its bounded search of 533 metadata files. Raw top-1 is the LoRA-adapted baseline, not an unadapted comparator. DEV triggers total 441/174,513 seed-recordings (136, 64 and 241 by checkpoint). Pooled language counts are Arabic 6/30,813, Persian 326/32,265, Polish 83/30,288, Turkish 14/35,592 and Italian 12/45,555. Exact rates are preserved in its CSV and provenance JSON. CV27 tests cross-domain acoustic transfer without CV27 acoustic adaptation, while the selector uses CV27 DEV. Acoustic and orthographic effects have not been causally separated.

Across all nine DEV/TEST caches, the observed positive-length feature vectors satisfy the signs required for strictly negative G4 scores. A zero-feature HF empty therefore wins deterministically whenever it enters the candidate bank. Centering and an ordinary shared intercept cannot change that ranking; the H4+e feature is empty-specific. The complete CV27 banks contain 19 zero-feature proposals, of which 18 are triggered. Reverting those 18 acceptances retains 91.52% of gain. One or two DEV empties per checkpoint limit calibration; no per-instance no-speech branch is inferred.

The current manuscript presents the empty score as an implicit abstention baseline in Section II-B and retains its ordering over nonempty candidates under the fitted signs in Section IV-D. It does not attribute the 18 acceptances to unlogged no-speech or log-probability termination branches. The text reports the insertion/deletion tradeoff, the 91.52% nonempty-guard result and the limited DEV calibration of H4+e.

The gate replay now explains the call–retention tradeoff explicitly. The text gate preserves all FLEURS positive gain at less than half the token-ID gate's calls; the word gate uses fewer calls but loses gain. This supports a parsimonious operating point on the cached panels, not universal gate optimality or a measured latency advantage for the replayed gates. Direct's main gain remains on checkpoint one, whereas HWR4's gain over H4 is on checkpoint two.

Table IV now contains five columns: Language, FLEURS Calls/Gain, and CV27 Calls/Gain. Its 20 original values and S/D/I footer are unchanged. The per-language B and Raw top-1 WERs are retained below and in the complete numeric evidence, rather than repeated in the compact table or results paragraph. G4's weighted and HF refits' pooled RMS remain distinguished by the Section IV-C sensitivity result and the exact definitions below. No experiment has been relabeled as having used a common scaling rule.

The reported `33,98` and `2988.3.` typos were already absent from the baseline source. Final PDF inspection confirms `33.98` and `2988.3`. The table sources are hardcoded; the Table IV evidence verifier was updated for the requested Calls/Gain column order without removing any baseline-WER checks.

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

- `main.tex`: restore the concise Abstract and Conclusion; keep the fixed Whisper text gate, simplify the script-encoding discussion, present the empty score baseline, remove the displayed RankNet loss while retaining its probabilities/edit-gap weights, and clarify DEV use. Numbered Equations (1)–(3), including intact `argmax`, are unchanged.
- `results.tex`: explain the cached gate operating point, retain checkpoint-specific Direct/HWR4 findings and the matched-RMS sensitivity, and present empty-output suppression and non-Persian gains without repeating per-language baseline WERs.
- `language_scope.tex`: restore five columns with Calls before Gain for each dataset. All retained values and the S/D/I footer agree with the existing counts.
- `verify_revision_evidence.py`: check the new Table IV column order against cached means. All per-language Raw top-1/B/S+R, RMS, model-lock and provenance checks remain active.
- Final table presentation: Table I repeats FLEURS/CV27 beside the compact oracle-panel heading and labels both confirmation contrasts in pp. Table II separates comparison families A and B with a thin rule. All data rows are unchanged.
- Tables I–III results, numbered equations, figure, authors, affiliations, grants and all 33 references are unchanged. Repeated wording within the revised paragraphs was shortened to meet the page budget. IEEEtran, margins, body sizes, baselines, figure size and table row spacing are unchanged.

The PDF has **five US Letter pages**. Main text and acknowledgment finish on page 4; page 5 starts with REFERENCES and contains references [1]–[33] only. Poppler word-box bottoms for the first seven columns are 718.597 pt; page 4 right ends at 706.813 pt. All five pages were visually inspected. No Overfull/Underfull hbox or vbox messages remain. All fonts are embedded, no Type 3 font is used, and hyperlinks/bookmarks remain disabled. Local checks do not replace IEEE PDF eXpress certification.

## Reproduction

Run from the repository root using the documented NumPy/SciPy environment:

```sh
python3 paper/evidence/acceptance_audit/extract_evidence.py --repo . --output /tmp/iscas-evidence-replay
python3 paper/evidence/acceptance_audit/scaling_sensitivity.py --repo . --output /tmp/iscas-rms-replay
```

Use a fresh output directory for the fitting command. It performs the CPU sensitivity experiment; it does not run GPU decoding or modify the original models. The preserved evidence includes the protocol, model lock, all fit logs, OOF picks and final models. Lightweight file, arithmetic and layout checks are reported separately in `CHECKS.json`.

