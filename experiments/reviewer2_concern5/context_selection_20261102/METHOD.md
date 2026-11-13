# Context-constrained retrieval — rule fixed before this search

2026-11-02. Keep the existing source-only encoder, training-pool/reference policy, exclusion rules and three complete examples. TSAR reference policy remains provisional and unchanged in this step. No inference or metric optimization.

Objective: maximize the sum (equivalently mean) of the three stored source-embedding cosine similarities, subject to distinct eligible documents/sources and exact complete-prompt counts <=7616 for BOTH models and ALL THREE prompt types. This reserves 512 output tokens and 64 additional tokens within num_ctx=8192. The selected documents are shared across all six combinations. No instruction, source, demonstration or reference is trimmed.

Enumerate eligible triples best-first in descending sum of cosine, with deterministic training-row ordering for ties. Neighbors increment one ordered rank while preserving i<j<k. Because scores cannot increase along any edge and every triple is reachable, the first feasible triple maximizes the stored score subject to the measured constraints. Feasibility itself need not be additive or monotone: every acceptance uses native token counts. Scores and comparisons use stored float64 arithmetic, not claims of exact real-number precision. Do not force retention of the first one or two documents and do not select a far-away short example as a fallback.

Computational guard: 5000 distinct triple evaluations per query. If reached before a feasible set, stop and report the case; do not silently change the algorithm or claim optimality. This limit is not chosen from simplification scores.

The installed tokenizer runtime changed since October. Pin the new native DLL/ABI in a separate wrapper, verify templates/model manifests and recheck the same 108 recorded prompt counts before the search. Load only vocabulary, not inference tensors; no backend context or GPU sampling. Save complete candidate prompts, selected rows, all 2238 exact counts and a comparison to the original top-3 and provisional prefix-preserving attempt. Keep the old study manifest/prompts unchanged. This step is not authorization to launch generation.
