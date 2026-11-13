"""Reproduce the frozen retrieval comparisons and materialize review artifacts.

Consumes certified scores only; never performs inference or semantic scoring.
Outputs stay inside the active prepared study, apart from the script itself.
"""
from pathlib import Path
import hashlib
import html
import json
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PLAN = HERE / 'prepared_retrieval_20261102'
DEST = PLAN / 'analysis'
sys.path.insert(0, str(ROOT / 'experiments/reviewer2_concern2'))
sys.path.insert(0, str(ROOT / 'experiments/reviewer2_concern7'))
from statistics_core import fit_clustered, test_contrasts, adjust_by_family, cluster_bootstrap
from detectors import extra_flags

METRICS = ['SARI', 'BLEU', 'BERTScore-F1', 'MeaningBERT', 'FKGL', 'FRE']
INPUTS = {}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def track(path):
    INPUTS[path.relative_to(ROOT).as_posix()] = sha(path)
    return path


def read(path):
    return pd.read_csv(track(path), keep_default_na=False, dtype={'text_id': str})


def verified_items(folder, stem):
    meta = json.loads(track(folder / (stem + '.json')).read_text())
    path = folder / (stem + '_items.csv')
    assert meta['status'] == 'complete' and sha(path) == meta['items_sha256']
    for name, digest in meta['fingerprint']['inputs'].items():
        assert sha(track(ROOT / name)) == digest, name
    return read(path), meta['record']


def aligned(frame, test):
    assert len(frame) == len(test)
    assert frame.text_id.tolist() == test.text_id.tolist()
    if 'row_index' in frame:
        assert frame.row_index.tolist() == list(range(len(test)))
    for col in ['original', 'reference']:
        if col in frame:
            assert frame[col].tolist() == test[col].tolist()


def page(title, body):
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>' + html.escape(title) + '</title><style>body{font:16px system-ui;max-width:1250px;margin:2rem auto;padding:0 1rem;color:#182433}table{border-collapse:collapse;width:100%}td,th{border:1px solid #cbd5e1;padding:.5rem;text-align:left}pre{white-space:pre-wrap;font:inherit;background:#f1f5f9;padding:1rem}summary{cursor:pointer;padding:.7rem;background:#e2e8f0}details{margin:1rem 0}a{color:#075985}.note{background:#fff7ed;padding:1rem}</style><h1>' + html.escape(title) + '</h1>' + body + '</html>'


def report_html(frame, title):
    intro = '<p class="note">Automatic scores and screening candidates are not confirmed error rates or human evaluation. All outputs are retained, including empty and token-capped outputs. Low-SARI selection is illustrative and is not a representative sample.</p><p><a href="../../index.html">Report index</a></p>'
    parts = []
    for row in frame.to_dict('records'):
        scores = ' | '.join(f'{key}: {float(row[key]):.3f}' for key in METRICS if key != 'BLEU')
        flags = row['screening_candidates']
        text = f'<details><summary>Row {row["row_index"]} | ID {html.escape(str(row["text_id"]))} | {scores} | {html.escape(row["done_reason"])}</summary><p>{html.escape(flags)}</p>'
        for label, value in [('Source', row['original'])] + [(f'Reference {i+1}', ref) for i, ref in enumerate(json.loads(row['references_json']))] + [('Prediction', row['prediction'])]:
            text += '<h3>' + label + '</h3><pre>' + html.escape(str(value)) + '</pre>'
        text += '<h3>Retrieved demonstrations</h3><pre>' + html.escape(row['demonstrations_json']) + '</pre></details>'
        parts.append(text)
    return page(title, intro + ''.join(parts))


def main():
    if (DEST / 'verification.json').exists():
        proof = json.loads((DEST / 'verification.json').read_text())
        for name, digest in {**proof['inputs'], **proof['outputs']}.items():
            assert sha(ROOT / name) == digest, name
        print('Existing analysis and all input/output hashes verified; nothing overwritten.')
        return
    manifest = json.loads(track(PLAN / 'experiment_manifest.json').read_text())
    track(PLAN / 'ANALYSIS_PLAN.md')
    track(Path(__file__))
    track(ROOT / 'experiments/reviewer2_concern2/statistics_core.py')
    track(ROOT / 'experiments/reviewer2_concern7/detectors.py')
    old_audit_path = ROOT / 'audits/original_paper_statistics_20261022/methodology.json'
    old_hashes = json.loads(track(old_audit_path).read_text())['source_hashes']
    old_hashes = {Path(k).as_posix(): v for k, v in old_hashes.items()}
    selections = read(PLAN / 'selected_examples.csv')
    summaries, comparisons, flag_rows, report_links, cluster_frames = [], [], [], [], []
    cluster_keys = []
    tests = {}
    for dataset in ['cochrane', 'plaba', 'tsar2025']:
        test = read(ROOT / f'data/{dataset}/{dataset}_test.csv')
        tests[dataset] = test
        cluster_keys.extend((dataset, str(tid)) for tid in test.text_id.drop_duplicates())
    lookup = {key: i for i, key in enumerate(cluster_keys)}
    sums = np.zeros((len(cluster_keys), 54))
    counts = np.zeros_like(sums)
    contrasts, weights, dfs = [], [], []
    for cell, job in enumerate(manifest['jobs']):
        model, dataset, prompt = job['model'], job['dataset'], job['prompt']
        test = tests[dataset]
        predicted = read(ROOT / job['prediction_path'])
        aligned(predicted, test)
        cert = PLAN / 'logs' / model / (job['job_id'] + '.complete.json')
        assert json.loads(track(cert).read_text()) == dict(status='complete', rows=len(test), prediction_sha256=sha(ROOT / job['prediction_path']))
        assert (predicted.prompt_eval_count == predicted.preflight_prompt_tokens).all()
        assert not predicted.context_budget_observed_warning.astype(str).str.lower().isin(['true', '1']).any()
        items, record = verified_items(PLAN / 'evaluation' / model, f'{dataset}_{prompt}_few_retrieval')
        aligned(items, test)
        assert np.isclose(items.SARI.mean(), record['SARI'], atol=1e-10)
        short = 'llama3_1_8b' if model == 'llama' else 'mixtral_latest'
        fixed_path = ROOT / f'outputs/{model}_512/predictions_{short}_{dataset}_{prompt}_few_metric.csv'
        assert sha(fixed_path) == old_hashes[fixed_path.relative_to(ROOT).as_posix()]
        fixed = read(fixed_path)
        aligned(fixed, test)
        random_items, random_records = [], []
        for seed in [42, 44, 46]:
            ri, rr = verified_items(ROOT / f'experiments/reviewer2_concern2/evaluation/metrics/{model}/seed_{seed}', f'{dataset}_{prompt}_few_random')
            aligned(ri, test)
            random_items.append(ri)
            random_records.append(rr)
            summaries.append(dict(model=model, dataset=dataset, prompt=prompt, strategy=f'few_random_{seed}', n=len(test), **{k: rr[k] for k in METRICS}))
        summaries.append(dict(model=model, dataset=dataset, prompt=prompt, strategy='few_retrieval', n=len(test), **{k: record[k] for k in METRICS}))
        # Historical corpus BLEU is computed from the saved strings, not averaged sentence BLEU.
        import sacrebleu
        refs = [json.loads(v) for v in items.references_json]
        ref_streams = [[r[i] for r in refs] for i in range(len(refs[0]))]
        corpus_bleu = sacrebleu.corpus_bleu(fixed.prediction.tolist(), ref_streams).score
        fixed_scores = {k: float(fixed[k].mean()) for k in METRICS if k != 'BLEU'}
        fixed_scores['BLEU'] = corpus_bleu
        summaries.append(dict(model=model, dataset=dataset, prompt=prompt, strategy='few_metric', n=len(test), **fixed_scores))
        avg_scores = {k: float(np.mean([r[k] for r in random_records])) for k in METRICS}
        sd_scores = {k + '_sd': float(np.std([r[k] for r in random_records], ddof=1)) for k in METRICS}
        summaries.append(dict(model=model, dataset=dataset, prompt=prompt, strategy='few_random_mean', n=len(test), **avg_scores, **sd_scores))
        arrays = [items.SARI.to_numpy(float), fixed.SARI.to_numpy(float), np.mean([r.SARI.to_numpy(float) for r in random_items], axis=0)]
        for local, values in enumerate(arrays):
            for tid, value in zip(test.text_id, values):
                idx = lookup[(dataset, str(tid))]
                sums[idx, 3*cell+local] += value
                counts[idx, 3*cell+local] += 1
        for local, family in [(1, 'retrieval_minus_metric'), (2, 'retrieval_minus_mean_random')]:
            vector = np.zeros(54)
            vector[3*cell] = 1
            vector[3*cell+local] = -1
            weights.append(vector)
            dfs.append(test.text_id.nunique()-1)
            contrasts.append(dict(model=model, dataset=dataset, prompt=prompt, family=family, n=len(test), clusters=test.text_id.nunique()))
        merged = predicted.copy()
        merged.insert(0, 'row_index', range(len(merged)))
        for col in items:
            if col not in ['text_id', 'row_index', 'done_reason']:
                merged[col] = items[col].to_numpy()
        flags, demo_texts = [], []
        for row in merged.itertuples():
            flag = extra_flags(row.original, row.prediction, row.done_reason)
            flag.update(empty_output=not row.prediction.strip(), generation_limit=row.done_reason == 'length')
            flag_rows.append(dict(model=model, dataset=dataset, prompt=prompt, row_index=row.row_index, text_id=row.text_id, **flag))
            flags.append(', '.join(k for k, v in flag.items() if isinstance(v, bool) and v))
            chosen = selections[(selections.dataset == dataset) & (selections.test_row_index == row.row_index)].sort_values('rank')
            assert len(chosen) == 3
            assert json.loads(row.retrieval_training_ids_json) == chosen.training_text_id.tolist()
            demo_texts.append(chosen[['rank', 'training_text_id', 'original', 'reference', 'cosine_similarity', 'reference_cefr']].to_json(orient='records', indent=2, force_ascii=False))
        merged['screening_candidates'] = flags
        merged['demonstrations_json'] = demo_texts
        folder = DEST / 'error_analysis' / model / dataset
        folder.mkdir(parents=True, exist_ok=True)
        stem = Path(job['prediction_path']).stem
        merged.to_csv(folder / (stem + '_all_items.csv'), index=False)
        lowest = merged.nsmallest(15, 'SARI', keep='first')
        lowest.to_json(folder / (stem + '_lowest_sari.json'), orient='records', indent=2, force_ascii=False)
        for suffix, frame in [('_all.html', merged), ('_lowest_sari.html', lowest)]:
            out = folder / (stem + suffix)
            out.write_text(report_html(frame, f'{model} / {dataset} / {prompt} / retrieval ({len(frame)} rows)'), encoding='utf-8')
            report_links.append((job['job_id'] + suffix, out.relative_to(DEST / 'error_analysis').as_posix()))
        cluster_frames.append(merged[['row_index', 'text_id', 'SARI']].assign(model=model, dataset=dataset, prompt=prompt))
        print('Validated and rendered', job['job_id'], flush=True)
    means, covariance = fit_clustered(sums, counts)
    weights = np.asarray(weights)
    result = test_contrasts(means, covariance, weights, dfs)
    draws, intervals = cluster_bootstrap(sums, counts, np.array([d for d, _ in cluster_keys]), weights, repetitions=10000, seed=20261023)
    effects = pd.DataFrame(contrasts)
    for key, value in result.items():
        effects[key] = value
    effects['q_bh'] = adjust_by_family(effects.p, effects.family)
    effects['bootstrap_ci_low'], effects['bootstrap_ci_high'] = intervals
    effects['reject_bh_005'] = effects.q_bh < .05
    assert effects.groupby('family').size().tolist() == [18, 18]
    # Verify direct paired means independently of the regression machinery.
    for cell in range(18):
        for local in [1, 2]:
            expected = means[3*cell] - means[3*cell+local]
            assert np.isclose(effects.iloc[2*cell+local-1].effect, expected)
    summary = pd.DataFrame(summaries)
    summary.to_csv(DEST / 'descriptive_comparisons.csv', index=False)
    effects.to_csv(DEST / 'sari_contrasts.csv', index=False)
    np.savez_compressed(DEST / 'bootstrap_draws.npz', effects=draws, weights=weights, cluster_sums=sums, cluster_counts=counts)
    pd.DataFrame(cluster_keys, columns=['dataset', 'text_id']).to_csv(DEST / 'source_clusters.csv', index=False)
    flags = pd.DataFrame(flag_rows)
    flags.to_csv(DEST / 'error_analysis/screening_candidates.csv', index=False)
    boolean_cols = [c for c in flags if flags[c].dtype == bool]
    flag_summary = flags.groupby(['model', 'dataset', 'prompt'])[boolean_cols].sum().reset_index()
    flag_summary.to_csv(DEST / 'error_analysis/screening_by_configuration.csv', index=False)
    body = '<p>18 configurations; 2,238 outputs. Each configuration has a complete report and a report of its 15 lowest-SARI instances (270 selected instances across reports). Selection is illustrative. Indicators are unvalidated screening candidates.</p><ul>'
    body += ''.join(f'<li><a href="{html.escape(path)}">{html.escape(label)}</a></li>' for label, path in report_links) + '</ul>'
    (DEST / 'error_analysis/index.html').write_text(page('Retrieval output review', body), encoding='utf-8')
    for name, digest in INPUTS.items():
        assert sha(ROOT / name) == digest, 'Input changed during analysis: ' + name
    proof = dict(status='complete', configurations=18, output_instances=2238, contrasts=36, bh_families=2, bootstrap_repetitions=10000, bootstrap_seed=20261023, clusters=len(cluster_keys),
                 html_reports=36, selected_low_sari_instances=270, inference_calls=0, semantic_scoring_calls=0, inputs=INPUTS,
                 outputs={f.relative_to(ROOT).as_posix(): sha(f) for f in DEST.rglob('*') if f.is_file() and f.name != 'verification.json'})
    (DEST / 'verification.json').write_text(json.dumps(proof, indent=2), encoding='utf-8')
    print(effects.groupby('family').agg(positive=('effect', lambda s: int((s > 0).sum())), significant=('reject_bh_005', 'sum')).to_string())
    print('Analysis complete:', DEST)


if __name__ == '__main__':
    main()
