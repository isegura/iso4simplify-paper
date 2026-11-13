# Concern 5: focused per-input retrieval comparison

Prepared before retrieval outcomes on 23 October 2026. This is a separate study from Concern 2; it does not change its frozen seeds or statistical families.

## Scope and retrieval

Only three-demonstration few-shot: two existing models × three datasets × three prompt families = 18 configurations, 2238 response instances. No new one-shot, zero-shot, fixed-metric or fixed-random generations. Historical comparators are retained.

Retrieve using cosine similarity between source embeddings from the test input and the same dataset's training sources. Use the locally cached all-MiniLM-L6-v2 checkpoint 1110a243fdf4706b3f48f1d95db1a4f5529b4d41 on CPU, without downloads. Long sources are tokenized without truncation, split into nonoverlapping 224-token chunks, decoded only for embedding, and pooled by the token-length-weighted mean of unit chunk embeddings, normalized again. Each re-encoded chunk must fit the encoder's 256-token maximum. Generation retains the original full training source/reference text, not decoded chunks.

Candidate pools deduplicate normalized training sources, keeping the first original row. This avoids two near-identical demonstrations with different references. For TSAR, where two CEFR references exist for a source, this deliberately fixes the first training row rather than selecting a CEFR level or a reference by quality; the resulting level mix must be reported. PLABA duplicate sources use the same rule. Normalization is Unicode NFKC, case folding and whitespace collapse. Exclude sources matching any test source exactly after normalization; within each query also exclude a matching document ID. Select three distinct source texts and document IDs, sorted by decreasing cosine, ties by original training row index. No test simplifications, FRE gains, generated outputs or simplification metrics determine ranks. The same input uses the same ordered demonstrations across all prompts and both models. Duplicate PLABA query sources share the same retrieval result.

Use the corrected original few-random templates; replace only the three demonstration slots. Compare their instruction prefix with few-metric ignoring whitespace; record the single blank-line difference in TSAR ISO+examples. Preserve all ISO guidance and embedded instructional examples. This is an adaptation of similarity-based retrieval, not an exact reproduction of Liu et al. and not a claim that this encoder is universally optimal.

## Generation and context

Original options: 512 new tokens, context 8192, temperature 0, generation seed 42, top_k 1, top_p 1, repeat penalty 1.1, repeat_last_n 64, same installed model digests and GPU requirement. No change to the Concern 4 diagnostic. Record raw outputs, standard execution metadata, chosen training row IDs, ranks/scores and instruction hashes. Preserve empty/capped outputs; resume only with matching provenance. No concurrent runs with Concern 2.

Prompt lengths vary under retrieval. Preparation records characters against the original few-shot ranges, not an exact model-token count. Such counts cannot establish absence of silent input truncation. Do not trim texts, reduce examples, change their ranks or increase context silently to make a result fit. Runtime records prompt_eval_count; if observed prompt tokens plus 512 exceed 8192, preserve the output and stop for inspection. This guard does not rule out upstream silent truncation. Review the length diagnostics before launching and the first completed block before proceeding; any necessary methodological change must be recorded separately before continuing, preserving this preparation.

## Evaluation and comparisons

Use the six validated metrics and historical item rounding, corpus BLEU, original pinned MeaningBERT versus source and TSAR A2/B1 jointly. Add the same output length/compression/copy descriptors as Concern 3. No evaluation while generation is appending.

Primary descriptive comparison: retrieval versus original few-metric within the 18 matched model/dataset/prompt cells. Secondary: retrieval versus the mean of the three fixed random selections (42/44/46), retaining individual seed values and SD and awaiting complete Concern 2 data. All strategies use three examples; do not generalize to one-shot. Source-only selection similarity is not the same quantity as output/reference agreement or readability.

If inferential comparisons are included, predefine 18 paired SARI retrieval-minus-metric contrasts as one BH family and 18 retrieval-minus-mean-random contrasts as a separate secondary BH family. Use the document-group bootstrap and conditional cluster-robust contrast approach established in Concern 2, retaining shared PLABA IDs together, 10000 draws with seed 20261023; report pointwise CI and adjusted p separately. Fixed random seeds are averaged within each input before the second contrast; this does not estimate uncertainty over arbitrary selections. The comparison runner is a later analysis task, not yet executed or claimed complete here. Other metrics remain descriptive. Do not choose a test or family after seeing which is significant.

All comparisons use historical controls and inherit their environment and label-correction limitations. Report the scope of the retrieval encoder, chunking, reference deduplication, example order and context diagnostics. Do not claim a causal effect of per-input retrieval alone or equivalence from nonsignificance. No human evaluation and no claim of comprehensive ISO adherence.

Sources: [Liu et al. 2022](https://aclanthology.org/2022.deelio-1.10/); official [Sentence Transformers semantic search](https://www.sbert.net/examples/sentence_transformer/applications/semantic-search/README.html) and [input length documentation](https://sbert.net/examples/sentence_transformer/applications/computing-embeddings/README.html). The chunk aggregation and controls above are this study's explicit implementation choices.
