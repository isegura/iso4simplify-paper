# prompts

This folder contains the prompt templates loaded by `main.py`.

Naming convention:

```text
<prompt_type>_zero.md
<dataset>_<prompt_type>_one.md
<dataset>_<prompt_type>_few_<sampling>.md
```

Values:

- `prompt_type`: `minimal`, `iso`, `iso_examples`.
- `dataset`: `cochrane`, `plaba`, `tsar2025`.
- `sampling`: `random`, `metric`.

Examples:

```text
minimal_zero.md
cochrane_iso_one.md
tsar2025_iso_examples_few_metric.md
```

`zero` prompts are dataset-independent. `one` and `few` prompts have dataset-specific versions.

