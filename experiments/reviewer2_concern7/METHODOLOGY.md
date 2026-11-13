# Concern 7: systematic automatic screening

Scope fixed before this screening: all 72 original configurations, 8952 outputs. Selection seeds 44/46, ablations and penalty diagnostics are excluded. Original prediction files are read-only; historic SHA-256 checks and source/reference row alignment precede screening. Output rows are response instances, not independent documents, particularly for repeated PLABA sources.

Indicators reuse the unchanged original `classify_row` rules and add the explicit rules in `detectors.py`. No model is run and no claim of detector validation is made.

- **Empty / generation limit:** observed empty text and `done_reason=length`, separately. A token-limit event is not itself a confirmed incomplete sentence; `stop` does not prove completeness.
- **Abrupt-ending candidate (legacy):** original numeric-ending regex, or at most ten words without .!?, with `done_reason=stop`. Numeric cutoffs can be missed and complete numeric/list endings can be marked.
- **Broader ending screen:** nonempty `stop` output without terminal .!? after removing closing quote/emphasis characters. Complete lists, parenthetical notes, titles and URLs can trigger it. Report separately and also its union with the legacy screen; do not add overlapping counts.
- **Preamble candidate:** beginning anchored to “Here is/are/Here's”, “Sure,” or simplified/rewritten/revised text/version/passage followed by a colon, allowing initial Markdown heading/emphasis. The existing broader format-marker search is also retained separately: structural headings and notes are not necessarily errors.
- **List markers:** one or more, and two or more Markdown/numbered/bullet line markers. Presence/absence is a formatting observation, not proof of correct organization or ISO adherence. List use can be appropriate and is requested by some prompts.
- **Acronym without detected expansion:** uppercase tokens of 2–8 letters, optionally plural s. Look for a matching parenthetical long form before/after the token, checking initials with/without common function words. Report all candidates and those absent verbatim from the source. This is not a validated “unexplained acronym” detector: familiar abbreviations, headings, units, statistics and definitions in other forms can be false positives; mixed-case acronyms can be missed.
- **Length/compression/copy:** identical whitespace/token-set definitions to Concern 3. “Too brief vs reference” retains the legacy threshold below half the mean reference word count. This is not a validated meaning-loss threshold. Copy overlap and verbatim copying do not establish quality, fidelity or misunderstanding.

TSAR references A2/B1 are used jointly for reference length, consistently with the evaluation pipeline. Every Cochrane/PLABA reference row remains separate. No rows are filtered on SARI or on output quality.

Output: per-instance flags and counts/percentages for every configuration and broader groupings. No single “error rate” is constructed from the union of formatting, technical language and endpoint indicators. The legacy any_flag is retained only for comparability, explicitly not an error label.

Exploratory spot check: sample at most one positive instance per model/dataset for each of four indicators (preamble, legacy abrupt ending, broader ending, acronym without detected expansion), seed 20261023. Sampling depends on flags, not SARI. Deduplicate instances for reading but retain their sampled indicator assignments. Inspect the full output and consult the source when needed. This is an assistant review, not the human evaluation the author has declined, not independent/blinded annotation, and not an estimate of sensitivity/specificity or general precision. Keep both clear cases and false/uncertain candidates. Do not modify detector thresholds after inspecting this sample.

The prior assistant inspection of 446 Mixtral endpoint candidates remains in Concern 4 and is linked as additional existing evidence, not newly independent validation. New automatic rates must be distinguished from those contextual judgments.
