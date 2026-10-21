# R8: HF-supervised gate comparison

This completed retrospective study fits HF12 and HF9 on full-DEV HF benefit
labels under the original Shared acceptor. Original arrays, fitted gates,
results and strict assertions are retained. No confirmation or timing is added.

From `experiments/`, with Python 3.10 and NumPy 2.2.6, choose a fresh output:

```bash
python r8/tools/replay_hf_supervised.py --out ../../r8_generated
```

This optional replay refits six ridge gates, reproduces 108 DEV-threshold TEST
cells and matched-count controls, checks count/window-flag reconstructions,
and recomputes the original bootstrap. It was not rerun for v160. Outputs must
remain separate from inherited `expected/` files.

The original study covers 58,171 DEV recordings at each of three checkpoints.
See [features](feature_definition.json), [protocol](protocol.json) and
[expected results](expected/results.json). Historical source-identity CSV and
private execution archives are excluded from this public snapshot.

At q=0.003 the HF12-minus-matched-CR CV27 interval crosses zero; it establishes
neither equivalence nor universal superiority. Exact-K uses whole-panel
rankings and does not equate online thresholds or time. All quantiles and HF9
results remain in `expected/`.

The intermediate `1e-12` assertion is unchanged; see [environment notes](../ENVIRONMENT.md)
before using a different Python/NumPy environment.
