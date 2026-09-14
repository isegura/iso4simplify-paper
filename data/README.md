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

