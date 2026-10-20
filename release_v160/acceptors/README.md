# Matched HF candidate-acceptor benchmark

This retrospective study fits H4 (four-feature expected risk), HR4 (four-feature
pairwise RankNet), and H3 (refitted risk on a,t,r) on the same full HF-expanded
CV27 DEV banks. G4 remains the original frozen greedy-bank-fitted beta_F.
Each of the three checkpoints has three final fits. No recognizer, source,
trigger, acquisition gate or confirmation panel changes.

The release contains 58,171 DEV recordings per checkpoint, complete FLEURS
(3,665 recordings, 3,687 windows) and CV27 (58,514 recordings) TEST inputs,
all nine fitted models, all 49 penalties and five-fold optimization records,
96 policy counting cells, 480 per-language rows and the fixed two comparisons.
These are counting cells, not 96 independent experiments.

## Recompute the new evaluation

From the extracted artifact root, with Python 3.10.12, NumPy 2.2.6 and SciPy
1.15.3 available, choose an output directory that does not yet exist:

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python acceptors/tools/replay_packaged.py --acceptor-root acceptors --output-dir ../acceptor_generated
```

The program checks input identities, recomputes selections/counts, means and
2,000 paired component-bootstrap draws, and compares new outputs with
`expected/`. It also checks all released count/pick arrays. It writes only
to the external output directory. No network, GPU, raw transcript or model
weights are used. Expected outputs are references, not generated results.

To optionally reproduce all nine DEV fits, add `--fit-all` and use a different
fresh destination. This executes all 2,214 optimizations again and reports
coefficient/OOF differences separately. This option was not run again during
delivery. The historical CV logs and models are the actual original run.
The optional replay creates an explicitly post-result input-transport plan;
it does not replace the original scientific lock or register a new study.

## Inputs and policies

[Schema](candidate_export_schema.json) defines every array and axis.
[Folds and scaling](folds_and_scaling.json) specifies weighting and selection.
[The locked plan](prerefit_plan.json) retains the original settings and hashes;
[packaging identity](PACKAGING_IDENTITY.json) maps original hashes to released
aliases. Aliasing preserves numbers, candidate order and component partitions.

All multi-candidate banks have measured raw features. Some final singleton
banks lack absolute neural scores, retained as NaN with observation masks.
Their sole selected output and genuine relative x=0 remain known. No score
is fabricated; they remain in all denominators and evaluation. See
[availability](candidate_availability.json) for exact coverage. This is a
qualification of absolute-feature completeness, not missing selection outcomes.

Each acceptor has its own B/N/S. Trigger-only T retains original B_G4 on
nontriggers. Original Direct also retains B_G4 on nontriggers and emits HF on
triggers. T_H3 is not PLL-free. Multi-window scoring uses numeric lookup tables
obtained by joining selected texts and aligning with complete references.
Window edits are never summed. Export code is inspectable in `export_reference/`;
rerunning export requires the author's private cached data and is not required
for numeric replay. Identity checks do not reauthenticate those private sources.

## Findings and scope

CV27 T_HR4 minus T_H4 is +0.721162 pp; S_H3 minus S_H4 is +2.248267 pp.
The Bonferroni individual 97.5% intervals are [0.400659,1.163920] and
[2.156723,2.338274], respectively, for a nominal two-comparison 95% family.
Ordinary individual 95% intervals are also in `expected/primary_comparisons.json`.
Policies are paired by language-internal client/reference component and all
three checkpoints share each draw. FLEURS results are descriptive.

Every refitted acceptor improves over its own B. Original Direct still has
lower mean CV27 WER than H4 S. H4 is slightly worse than G4 on FLEURS.
The H3 comparison includes a changed beam-only/nontrigger baseline; it is
not a pure triggered-acceptance effect or a universal necessity claim for PLL.
No new runtime or peak-memory measurement exists. H3 predictor omission of p
does not establish a measured end-to-end PLL-free speed advantage.
The original confirmation supports original G4 only.

## V148 descriptive addition

The [branch audit](branch_audit/README.md) checks the unchanged numeric banks and
partitions the H3/H4 complete-policy difference. It does not repeat these fits or
the original default replay. All original 49-penalty records and results remain.
