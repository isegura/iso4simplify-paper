# Retrieval — completed results and limitations

18 configurations and 2,238 outputs are certified and evaluated. No observed/preflight input-token mismatch exists. Llama has 22 capped responses; Mixtral has 28 plus one empty response. All are retained.

## Comparisons

Retrieval exceeds each comparator descriptively in 11/18 cells. Against metric selection: four adjusted positive and one adjusted negative SARI contrasts. Against mean random: one positive (Llama Baseline/Cochrane, +1.0325) and one negative (Llama ISO+examples/TSAR, -1.5820). Remaining adjusted contrasts are not evidence of equivalence. Pointwise bootstrap intervals can exclude zero when adjusted q is above .05; use q for the planned significance decision.

## Screening scope

36 HTML reports cover all 2,238 outputs and the 15 lowest-SARI instances in each configuration (270 illustrative instances). Transparent rules are reused from Concern 7 without claiming detector validation, human evaluation, or semantic-error prevalence. Separate candidate counts:

- preamble_candidate: 53/2238.
- stop_no_terminal_punctuation_candidate: 128/2238.
- acronym_without_detected_expansion_candidate: 1060/2238.
- new_acronym_without_detected_expansion_candidate: 90/2238.
- list_markers_present: 94/2238.
- two_or_more_list_markers: 88/2238.
- source_copied_verbatim: 2/2238.
- empty_output: 1/2238.
- generation_limit: 50/2238.

Indicators can overlap. List markers/acronyms are not intrinsically errors; no-terminal-punctuation candidates are not automatically truncations. The low-SARI sample is selected after scoring for inspection, not used to choose the retrieval procedure or the inferential family.

## Historical-control limits

One encoder, a shared context-constrained triple, and a fixed TSAR training-reference policy are evaluated. Controls are historical and cannot identify a pure causal retrieval effect. No general ranking, human comprehension benefit, CEFR control, or comprehensive ISO compliance follows.
