# Independent review of the cached outer-gate comparison

Result: **PASS, with the stated retrospective scope.** No material numerical or implementation issue was found. This review performed no inference, fitting, or GPU work and did not modify the manuscript.

## Checks performed

- Read the extractor, replay, verifier, result protocol, and relevant frozen HF generation and candidate-export source. Ran `python3 paper/evidence/gate_audit/verify_gate_audit.py --repo .`: **423 checks passed**.
- Independently checked all six public panels: `r43` equals the uncentered original top-beam repetition feature exactly. The centered top-beam feature vector is zero and is not used as the gate input. Window ownership equals the recording offsets for every row. Each FLEURS panel contains 3,665 recordings, 3,687 windows and 22 two-window records; CV27 contains 58,514 single-window records per panel.
- The original top beam is selected by the cache mapping `source=B5, rank=0`, not by the HF candidate index. The extractor asserts this mapping for every record. Independently spot-checked the mapping and termination/token-count schema in each of the six original single-window feature files without exposing text or token sequences.
- The replay retains the frozen G4 coefficients and recomputes B and N+R choices with exact assertions against the existing choices and integer counts. The sole counterfactual is the outer gate. A recording receives the OR of its window triggers, and all its windows then use either N+R or B. `score_selected()` uses complete-reference joint alignment counts for the 22 two-window FLEURS recordings; it does not add window WERs.
- The positive-gain retention denominator is the average of language-reference-normalized positive B-to-N+R edits across five languages and three checkpoints. The calculation uses a ratio of the aggregated retained and available gains, not a pooled-edit fraction or a mean of seed retention percentages. Call rates use all seed-recordings; acquired-window counts are separately retained.
- Rehashed the original HF source and model configuration against the extraction receipt and verified that all six exported feature files match its hashes. The recorded private-cache hashing and full extraction assertions were inspected, not redundantly rerun.

## Token compression and EOS

The frozen HF `_retrieve_compression_ratio` serializes each token as `int(log2(vocab_size)/8)+1` little-endian bytes and applies default zlib compression. Vocabulary size 51,865 therefore uses two bytes. HF removes the decoder prefix before fallback assessment, removes padding while preserving one EOS, calls `_need_fallback`, and only then removes the terminal EOS. The candidate exporter stores the generated body without the prefix or terminal EOS and records whether termination was natural or length-capped. Restoring one EOS for `natural_eos` and none for `length_cap` is therefore consistent with the sequence passed to the compression check. The extractor validates every reconstructed ratio against the parsed, hash-verified HF function.

This establishes a compression-only **outer gate on the frozen original beam**. It does not reproduce the combined HF retry/no-speech policy and does not establish script-independent or bias-free gating. Tokenization remains language dependent. Cached stochastic candidate draws remain fixed; this is not a fresh-decoding or latency experiment. These boundaries are correctly stated in the accompanying README and result protocol.

## Numerical conclusion

The original, word-repetition and token-compression gates trigger respectively **10/7/22** FLEURS seed-recordings and **525/322/542** CV27 seed-recordings. The word gate loses some available recovery gain while reducing calls. The token gate retains slightly more CV27 positive gain and all FLEURS positive gain with additional calls. This supports a measured retrospective tradeoff, not a claim of universal optimality of the original threshold.
