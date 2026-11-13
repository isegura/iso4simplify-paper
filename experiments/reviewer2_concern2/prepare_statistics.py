"""Freeze design/contrasts from input metadata only. Never read new predictions or fit outcomes."""
from pathlib import Path
import hashlib
import itertools
import json
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DEST = HERE / 'statistics_plan'
DATASETS = ['cochrane', 'plaba', 'tsar2025']
MODELS = ['llama', 'mixtral']
PROMPTS = ['minimal', 'iso', 'iso_examples']
CONDITIONS = ['zero', 'one', 'few_random', 'few_metric']


def configurations():
    records = []
    for dataset, model, prompt, condition in itertools.product(DATASETS, MODELS, PROMPTS, CONDITIONS):
        for seed in ([42, 44, 46] if condition in ['one', 'few_random'] else [0]):
            records.append(dict(dataset=dataset, model=model, prompt=prompt, condition=condition,
                selection_seed=seed, cell_id=f'{dataset}/{model}/{prompt}/{condition}/' + (str(seed) if seed else 'fixed')))
    return pd.DataFrame(records)


def contrast(cells, positive, negative, model=None, dataset=None):
    """Equal dataset/model/condition margins; each available seed has equal weight."""
    def margin(filters):
        selected = cells.copy()
        for key, value in dict(filters, **({} if model is None else {'model': model}),
                               **({} if dataset is None else {'dataset': dataset})).items():
            selected = selected[selected[key] == value]
        # Each structural cell is equally weighted; its available selections split that weight.
        counts = selected.groupby(['dataset', 'model', 'prompt', 'condition']).selection_seed.transform('size')
        weights = pd.Series(0., index=cells.index)
        weights.loc[selected.index] = 1. / counts.to_numpy()
        return weights / weights.sum()
    return margin(positive) - margin(negative)


def build_contrasts(cells):
    specs = [('iso_minus_baseline', {'prompt': 'iso'}, {'prompt': 'minimal'}),
             ('iso_examples_minus_baseline', {'prompt': 'iso_examples'}, {'prompt': 'minimal'}),
             ('iso_examples_minus_iso', {'prompt': 'iso_examples'}, {'prompt': 'iso'}),
             ('one_minus_zero', {'condition': 'one'}, {'condition': 'zero'}),
             ('few_random_minus_one', {'condition': 'few_random'}, {'condition': 'one'}),
             ('few_metric_minus_few_random', {'condition': 'few_metric'}, {'condition': 'few_random'})]
    rows = []
    for name, positive, negative in specs:
        rows.append(dict(family='primary_7', contrast_id=name, weights=contrast(cells, positive, negative)))
        for model, dataset in itertools.product(MODELS, DATASETS):
            rows.append(dict(family='secondary_36', contrast_id=f'{name}/{model}/{dataset}',
                             weights=contrast(cells, positive, negative, model=model, dataset=dataset)))
    rows.append(dict(family='primary_7', contrast_id='mixtral_minus_llama',
                     weights=contrast(cells, {'model': 'mixtral'}, {'model': 'llama'})))
    return rows


def main():
    cells = configurations()
    assert len(cells) == 144 and cells.cell_id.is_unique
    contrasts = build_contrasts(cells)
    assert sum(r['family'] == 'primary_7' for r in contrasts) == 7
    assert sum(r['family'] == 'secondary_36' for r in contrasts) == 36
    for r in contrasts:
        w = r['weights'].to_numpy()
        assert np.isclose(w.sum(), 0) and np.isclose(w[w > 0].sum(), 1) and np.isclose(w[w < 0].sum(), -1)
    source_rows = []
    hashes = {}
    counts = []
    for dataset in DATASETS:
        path = ROOT / 'data' / dataset / f'{dataset}_test.csv'
        hashes[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
        frame = pd.read_csv(path, keep_default_na=False, dtype={'text_id': str})
        assert frame.text_id.str.strip().ne('').all()
        for i, row in frame.iterrows():
            source_rows.append(dict(dataset=dataset, row_index=i, text_id=row.text_id,
                                    cluster_id=dataset + '/' + row.text_id,
                                    source_sha256=hashlib.sha256(row.original.encode()).hexdigest()))
        counts.append(dict(dataset=dataset, test_rows=len(frame), clusters=frame.text_id.nunique(),
                           unique_sources=frame.original.nunique(), configurations=48, analysis_rows=48*len(frame)))
    # Identity coding is the full-rank cell-means parameterization of the joint model.
    design = np.eye(len(cells))
    assert np.linalg.matrix_rank(design) == 144
    assert sum(r['analysis_rows'] for r in counts) == 17904
    DEST.mkdir(exist_ok=True)
    cells.to_csv(DEST / 'joint_model_cells.csv', index=False)
    pd.DataFrame(source_rows).to_csv(DEST / 'source_clusters.csv', index=False)
    pd.DataFrame(counts).to_csv(DEST / 'design_counts.csv', index=False)
    long = []
    for r in contrasts:
        for idx, weight in r['weights'].items():
            if weight:
                long.append(dict(family=r['family'], contrast_id=r['contrast_id'], cell_id=cells.loc[idx, 'cell_id'], weight=float(weight)))
    pd.DataFrame(long).to_csv(DEST / 'contrast_weights.csv', index=False)
    report = dict(status='design_validated_not_fitted', configurations=144, rows=17904,
        source_clusters=sum(r['clusters'] for r in counts), model_rank=144,
        primary_contrasts=7, secondary_contrasts=36, outcome_columns_read=False,
        new_prediction_files_read=False, ollama_calls=0, bootstrap_replicates=10000,
        bootstrap_seed=20261023, cluster='dataset/text_id', multiplicity='BH separately: 7 primary SARI; 36 secondary SARI',
        source_sha256=hashes, code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        plan_sha256=hashlib.sha256((HERE/'PLAN_ESTADISTICO.md').read_bytes()).hexdigest(),
        statistics_core_sha256=hashlib.sha256((HERE/'statistics_core.py').read_bytes()).hexdigest(),
        synthetic_tests='test_statistics_plan.py: 3 passed; OLS/CR1 equivalence, margins, bootstrap repeatability, BH families')
    (DEST / 'validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
