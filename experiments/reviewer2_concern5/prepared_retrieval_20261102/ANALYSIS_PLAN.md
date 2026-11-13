# Concern 5: focused per-input retrieval comparison

Updated on 2 November 2026 before any retrieval generations. The 23 October preparation is preserved separately. This is not an external preregistration. Changes below finalize context-constrained source selection, balanced TSAR references and an explicitly checked pilot; Concern 2 results are already known and its analysis is not changed.

## Scope and retrieval

Only three-demonstration few-shot: two existing models × three datasets × three prompt families = 18 configurations, 2238 response instances. No new one-shot, zero-shot, fixed-metric or fixed-random generations. Historical comparators are retained.

Retrieve using cosine similarity between source embeddings from the test input and the same dataset's training sources. Use the locally cached all-MiniLM-L6-v2 checkpoint 1110a243fdf4706b3f48f1d95db1a4f5529b4d41 on CPU, without downloads. Long sources are tokenized without truncation, split into nonoverlapping 224-token chunks, decoded only for embedding, and pooled by the token-length-weighted mean of unit chunk embeddings, normalized again. Each re-encoded chunk must fit the encoder's 256-token maximum. Generation retains the original full training source/reference text, not decoded chunks.

Candidate pools deduplicate normalized sources and exclude exact test-source matches and matching document IDs. Cochrane/PLABA retain the earlier paired-reference policy. For TSAR, assign one reference to each of its 20 training sources: 10 A2/10 B1 using sorted source IDs and numpy.PCG64 with reference-assignment seed 42. Hold this assignment fixed across target inputs/models/prompts; do not impose a level quota per prompt or a target CEFR output instruction. The source-only embeddings/ranking are independent of that assignment. Select three distinct sources/documents maximizing their sum of stored cosine similarities subject to ALL six complete prompts fitting 8192-512-64=7616 input tokens. Search triples best-first, using similarity-descending demonstration order and training-row ties. Do not force retention of the first two examples or fall back to a remote short example. Stop without generation if a search limit is reached; no limit was reached in preparation. No test references, generated outputs or simplification scores choose examples. See context_selection_20261102/METHOD.md and TSAR_REFERENCE_POLICY.md for exact rules.

Use the corrected original few-random templates; replace only the three demonstration slots. Compare their instruction prefix with few-metric ignoring whitespace; record the single blank-line difference in TSAR ISO+examples. Preserve all ISO guidance and embedded instructional examples. This is an adaptation of similarity-based retrieval, not an exact reproduction of Liu et al. and not a claim that this encoder is universally optimal.

## Generation and context

Original options: 512 new tokens, context 8192, temperature 0, generation seed 42, top_k 1, top_p 1, repeat penalty 1.1, repeat_last_n 64, same installed model digests and GPU requirement. No change to the Concern 4 diagnostic. Record raw outputs, standard execution metadata, chosen training row IDs, ranks/scores and instruction hashes. Preserve empty/capped outputs; resume only with matching provenance. No concurrent runs with Concern 2.

Complete prompts are tokenized from the exact generation-message f-string, local model templates and native vocabularies, including special tokens. The current native library is hash-pinned, templates/model manifests verified, and 108 historical prompt counts revalidated. All 2238 combinations fit the 512-output plus 64-safety reserve. At execution, verify runtime/model/template identity and compare each observed prompt_eval_count exactly to its preflight count. Save an output with any discrepancy and stop; do not silently trim, change examples or certify it complete. Offline counts do not establish what an unrelated historical execution processed.

## Evaluation and comparisons

Use the six validated metrics and historical item rounding, corpus BLEU, original pinned MeaningBERT versus source and TSAR A2/B1 jointly. Add the same output length/compression/copy descriptors as Concern 3. No evaluation while generation is appending.

Primary descriptive comparison: retrieval versus original few-metric within the 18 matched model/dataset/prompt cells. Secondary: retrieval versus the mean of the three fixed random selections (42/44/46), retaining individual seed values and SD and awaiting complete Concern 2 data. All strategies use three examples; do not generalize to one-shot. Source-only selection similarity is not the same quantity as output/reference agreement or readability.

For the planned inferential comparisons, use 18 paired SARI retrieval-minus-metric contrasts as one BH family and 18 retrieval-minus-mean-random contrasts as a separate secondary BH family. Use the document-group bootstrap and conditional cluster-robust contrast approach established in Concern 2, retaining shared PLABA IDs together, 10000 draws with seed 20261023; report pointwise CI and adjusted p separately. Fixed random seeds are averaged within each input before the second contrast; this does not estimate uncertainty over arbitrary selections. The comparison runner is a later analysis task, not yet executed or claimed complete here. Other metrics remain descriptive. Do not choose a test or family after seeing which is significant.

All comparisons use historical controls and inherit their environment and label-correction limitations. Report the scope of the retrieval encoder, chunking, reference deduplication, example order and context diagnostics. Do not claim a causal effect of per-input retrieval alone or equivalence from nonsignificance. No human evaluation and no claim of comprehensive ISO adherence.

Sources: [Liu et al. 2022](https://aclanthology.org/2022.deelio-1.10/); official [Sentence Transformers semantic search](https://www.sbert.net/examples/sentence_transformer/applications/semantic-search/README.html) and [input length documentation](https://sbert.net/examples/sentence_transformer/applications/computing-embeddings/README.html). The chunk aggregation and controls above are this study's explicit implementation choices.


The pilot comprises the first three TSAR test rows under each of the three prompts with Llama (9 outputs), in original row order. It checks execution/metadata/context rather than selecting a favorable method by quality. Saved pilot rows remain part of the full datasets and are resumed without regeneration. Only a full configuration receives a completion certificate.
