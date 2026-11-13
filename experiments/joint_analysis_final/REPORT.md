# Unified main-study SARI analysis

Completed: 162 observed configurations, 90 selection-averaged structural cells, 20,142 repeated response instances, 335 source groups. All original scores retained; no inference or rescoring. This is a revision-stage extension after prior outcomes were known, not independent confirmation.

## Global contrasts

contrast_id,effect,bootstrap_ci_low,bootstrap_ci_high,q_bh
iso_minus_baseline,-0.1347410150150098,-0.3534139643039369,0.0822599216687458,0.2843755253818309
iso_examples_minus_baseline,0.0443401621621633,-0.2495915418676725,0.3416054890960961,0.7667820410405091
iso_examples_minus_iso,0.1790811771771721,-0.0110945886891786,0.373927087943402,0.1044191340138547
one_minus_zero,0.8204082482482482,0.5955560388930591,1.0480869340383647,3.6786005500621065e-11
few_random_minus_one,0.6964637637637618,0.5432628665563082,0.8528624429824556,1.2166265619290456e-15
few_metric_minus_few_random,-0.5046450750750755,-0.7205783720477071,-0.2917269208457993,1.8744379515598837e-05
few_retrieval_minus_few_random,0.0377191591591645,-0.2046654103942655,0.2816619513459069,0.7667820410405091
few_retrieval_minus_few_metric,0.5423642342342389,0.2461385424382741,0.8386370082817166,0.0009149649425944
mixtral_minus_llama,0.5969116116116164,0.1381570692824446,1.0324864354104109,0.0185139613535586

## Interpretation

Neither ISO nor ISO+examples has a detected global advantage over Baseline. ISO+examples--ISO is +0.179/q .104, replacing the earlier four-strategy +0.309/q .0047 conclusion. One--zero and random few--one remain positive globally. Retrieval (+0.542) and random (+0.505) both exceed the fixed metric heuristic globally; retrieval--random is +0.038/q .767, not equivalence. Mixtral--Llama is +0.597/q .019.

Omnibus prompt main effect q .086 does not reject, but all six two-way interactions do, as do the reported higher-order interactions in this 15-term family. These are marginal linear hypotheses, not independent causal effects or explained-variance fractions. Dataset score differences reflect these benchmarks, not general domain difficulty.

Local prompt-averaged selection comparisons favor random and retrieval over metric on PLABA for both models; retrieval is below random for Llama/TSAR. Full local results, including non-rejections, are in local_sari.csv.

## Change of estimand

Original 144 cell means and 18 retrieval means are unchanged. Prompt/model global effects change because five strategies are now averaged rather than four. The same strategy contrast effects can have different p/q values because the fit size/CR1 correction and declared BH family changed. All bootstrap intervals are pointwise; the extension uses seed 20261104, 10,000 replicates. No winner is selected for testing.

## Limits

Conditional on observed selections, models, datasets, reference policies and historical controls. Unseen demonstration sets, reader comprehension, CEFR control and ISO compliance are not inferred. No significance is claimed from comparing subgroup significance labels. Primary metric is SARI; other metrics/descriptors remain descriptive. Separate ablation and repeat-penalty studies are not pooled.
