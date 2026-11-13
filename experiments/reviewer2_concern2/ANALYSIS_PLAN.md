# Analysis fixed before new outputs

Specification update (2026-10-23, during generation and before inspecting new metric results): PLAN_ESTADISTICO.md fixes the joint cell-means regression, document-cluster uncertainty, seven primary and 36 secondary SARI contrasts, separate BH families, and bootstrap settings. statistics_plan/ holds metadata-only design checks. The earlier prospective paragraphs below are preserved as the initial plan; the new specification resolves their open design choices.

## Design and scope

Historical selection seed 42 plus new seeds 44 and 46; one and few-random only. Two models, three datasets, three prompt families. New generation: 72 configurations and 8952 outputs. Do not regenerate zero-shot or few-metric, or duplicate their single historical results to manufacture replication. Generation seed remains 42, repetition penalty remains 1.1. Demonstration-selection seed is a separate factor. The historical selection is not rerun.

The seeds were chosen before new outputs under an input-diversity criterion: distinct first examples for one-shot, and no shared source texts across the three selections in each dataset. Candidate seeds 42--46 and their overlaps remain documented. This is constrained selection, not an unrestricted random-seed sample. One-shot and few-shot within a seed share the first example; sets are fixed per dataset and reused for every test input, prompt family and model.

## Primary descriptive analysis

For SARI, report each of the three selection results and the mean, sample standard deviation, minimum and maximum across selections for each model/dataset/prompt/shot condition. Three selections give a limited view of variability; avoid precise variance or robustness claims. Report per-selection contrasts between prompt families, and few-random minus one-shot using the corresponding shared selection. Compare random selection against the fixed historical metric selection only for the matching few-shot condition. Do not treat the fixed metric condition as independently rerun for each seed.

Use the same full test rows, all outputs including empty and capped results, original TSAR references jointly and original validated metric implementations. Report other original metrics as secondary. Corpus BLEU must be recomputed with its corpus implementation, not averaged from sentence BLEU. Include completion, output length and cap/empty counts by selection. A complete endpoint alone does not establish meaning preservation. No output repair or post hoc seed replacement based on performance.

## Uncertainty and joint analysis

Paired test-item bootstrap intervals condition on the observed demonstration sets and do not estimate general uncertainty over possible selections. Retain row pairing and distinguish that item uncertainty from the three-set spread. PLABA repeated IDs require a documented dependence strategy before inferential analysis; do not silently treat them as independent documents.

The reviewer separately requests a joint-factor model. Its implementation remains an explicit analysis task after assembling the data, not something this generation plan claims to have completed. For a joint analysis, use per-item metric data with prompt family, model, dataset and an identifiable prompting-condition factor (zero, one-random, few-random, few-metric). Shots and selection method are not fully crossed: few-metric has no matching one-metric or zero-metric cells. Avoid an unidentifiable full factorial specification and do not duplicate fixed cells across selection seeds. Account for repeated source rows and the shared dataset-level demonstration sets. With only three sets, inference about demonstration-set variation will be limited; inspect model identifiability and report effect sizes and intervals rather than declare significance by model choice. Freeze exact inferential contrasts and any multiplicity family before fitting their tests; no new test has been run.

## Historical comparison and label corrections

The original Cochrane/PLABA third-example labels were wrong, although their source/reference texts matched seed 42. Corrected templates are used for the new selections and true training IDs are recorded. Historical prompts, hashes and outputs remain available. Do not claim that demonstration selection is the only literal input difference in the affected historical comparisons: the metadata labels were also corrected. The comparator is historical rather than a contemporaneous seed-42 control. These limitations must appear in reporting; no claim of isolating a complete causal seed effect.

## Reporting commitments

Use descriptive win counts as descriptive only. A nonsignificant contrast is not equivalence. Do not select a favorable seed or method to support conclusions. Keep raw per-selection results even if two settings look identical. This work addresses selection variability, not the full evaluation-validity/human-evaluation concern or all components of Concern 2 by itself.
