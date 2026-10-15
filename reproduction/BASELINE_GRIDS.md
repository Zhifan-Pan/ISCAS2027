Implementation definitions moved from V116 body to accompanying reproduction notes. All configurations and frozen inference unchanged.

Four features are mean decoder log-probability $a$, XLM-R-base pseudo-log-likelihood (PLL) $p$~\cite{xlmr,mlmscoring}, log length $t=\log(1+T)$, and repetition $r$. Here $T$ excludes prefix, padding and end-of-sequence tokens. Decoder scores use teacher-forced log-softmax. PLL averages individually masked token log probabilities in centered 510-subword windows, batches of 32; short texts use full context. Within-word masking is studied in~\cite{kauf2023}. PLL uses original candidate strings. Empty raw features are $a=p=t=r=0$; empties remain eligible after deduplication.

Confidence controls~\cite{jiang2005} use top-two decoder gap, negative softmax entropy ($T=1$) or standard deviation of mean decoder scores.

A linear \emph{benefit} control~\cite{chowdhury2023ewer3} predicts acquisition edit reduction from nine features: log duration/bank size, gap, entropy, decoder-score standard deviation/range, length/repetition ranges and mean absolute decoder-score difference. A 12-feature control adds raw top-beam CR, absolute top-beam repetition and maximum beam repetition. Both use the same nested folds and quantiles.

NormFusion fixes the RMS-scaled decoder coefficient to one; PLL weights are $\{0,0.1,0.3,1,3,10,30\}$ and length weights $\{-3,-1,-0.3,0,0.3,1,3\}$.

Hard-WER adapts minimum error rate training~\cite{och2003} with a 17-point coordinate grid on $[-1,1]$, 17 starts and up to eight passes; RankNet4 adapts pairwise logistic ranking~\cite{ranknet2005}. Fits share features/bank.

Sampling uses a deterministic per-window random seed derived with SHA-256 from the checkpoint, dataset split, language, recording ID and window index.

Five CV27 DEV folds group within-language recordings connected by client or normalized reference. Risk fits select from 49 penalties $10^{-4+j/12}$, $j=0,\ldots,48$, by held-out hard WER with fold-local RMS, then refit DEV from zero with L-BFGS-B. RankNet4 uses the same folds/penalties and inverse language-word/pair-count weights. Benefit ridge weights languages equally and selects $10^{-4},10^{-2},1$ or $100$ by DEV prediction error. Nested fitting excludes each outer fold from selector, scale, ridge and threshold estimation.
