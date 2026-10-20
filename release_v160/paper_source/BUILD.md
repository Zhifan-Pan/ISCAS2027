# V160 manuscript source

Build from this directory with a standard TeX Live installation:

~~~sh
latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error main.tex
~~~

The bibliography is in `references.tex`; no BibTeX database, model, private data
or network access is required to build the manuscript. `IEEEtran.cls`, the
author-supplied vector Figure 1, and the local CTAN `cmap` files and license
notice are included. Keep `cmap` before `fontenc`; `glyphtounicode` and
`pdfgentounicode=1` restore the mathematical text layer. See `CMAP_README.txt`.

The delivered PDF has four technical pages and a fifth page containing all 35
references. Template font sizes and margins, authorship, affiliations, funding,
Figure 1, models, parameters, folds and original primary results are retained.
V160 clarifies the n-gram count and the original recording-level Direct branch,
repairs float flow, restores the reranking-system cost framing, and adds three
bounded CPU analyses of existing caches. It does not change the original policy.

The additional Direct and Native WER values on the original confirmation panel
are explicitly post-lock retrospective diagnostics. The original confirmation
identity applies only to its original frozen policies. HWR4 cannot be evaluated
on that panel from the persisted selected outputs alone. The fixed nonempty
guard and window-local Direct are cached counterfactuals, with no new fitting,
model forwards, confidence intervals or live RNG-skipping claims.

Table III separates study A (four paths, three checkpoints, three paired rounds)
from study B (seven paths, one checkpoint, three paired rounds). Both use the
existing 727-recording stratified sample; no new GPU timing was performed for
V160. Population-stratum weights are retained, with equal checkpoint weights in
A. The census was defined at the first checkpoint as trigger OR
Native-output-changing. Positive ordinary-stratum inclusion probabilities permit
population estimation, but the realized sample misses some later-checkpoint
triggers. Reported bootstrap intervals are conditional on the sampled recordings,
checkpoints and hardware sessions; they do not remove that tail-coverage limit.

Memory is the observed peak allocated memory with Whisper and XLM-R resident,
not a standalone deployment footprint or a confidence bound. The author return
contains inherited per-path intervals, reserved-memory maxima, actual stage
profiles on a separate fixed 50-recording subset, and the trigger-coverage audit.
Policy-time subtraction does not identify an isolated PLL or fallback stage.
Complete H4/H3 and trigger/uncertainty-selective PLL costs remain unmeasured.

The formal conference submission candidate is the main PDF. The private author
return, numerical archive and technical note are not conference supplementary
material. Code is indexed separately at https://github.com/Zhifan-Pan/ISCAS2027.
Formal conference submission remains the author's decision.
