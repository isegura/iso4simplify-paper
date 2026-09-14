# data

This folder contains the datasets used in the project.

## Sources And Licenses

- Cochrane: [original corpus repository](https://github.com/AshOlogn/Paragraph-level-Simplification-of-Medical-Texts),
  accompanying Devaraj et al. (2021), [paper](https://aclanthology.org/2021.naacl-main.395/).
  The repository declares [CC BY 4.0](https://github.com/AshOlogn/Paragraph-level-Simplification-of-Medical-Texts/blob/main/LICENSE.md).
- PLABA: [original repository](https://github.com/attal-kush/PLABA) and
  [data record](https://osf.io/rnpmf/). CC BY was indicated by the dataset contact;
  the exact version has not been confirmed.
- TSAR 2025: [shared-task repository](https://github.com/tsar-workshop/tsar-2025-shared-task),
  which declares [CC BY-NC 4.0](https://github.com/tsar-workshop/tsar-2025-shared-task/blob/main/LICENSE).

Upstream repositories declare CC BY 4.0 for the Cochrane resource and CC BY-NC
4.0 for TSAR 2025. Correspondence provided on 2026-09-11 supports continued CC BY
use for PLABA while an NLM policy inquiry is pending; the precise version and
license notice remain to be recorded. Exact local file
provenance and third-party text permissions must be resolved before publication;
these statements are not a blanket license for all files in this folder.

Main datasets used in the paper:

- `cochrane`
- `plaba`
- `tsar2025`

`main.py` expects the test file to follow this path:

```text
data/<dataset>/<dataset>_test.csv
```

Expected columns for Cochrane and PLABA:

- `text_id`
- `original`
- `reference`

TSAR2025 uses a multi-reference format. The A2 and B1 references are loaded from:

```text
data/tsar2025/tsar2025_test_200.csv
```

Historical datasets outside the paper's scope are not included in this candidate.
