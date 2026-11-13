"""Screen all original outputs; no inference, semantic models or LaTeX writes."""
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from generate_systematic_error_analysis_512 import classify_row
from detectors import extra_flags

HELPER = ROOT/'experiments/reviewer2_concern2/evaluate_descriptors.py'
spec = importlib.util.spec_from_file_location('descriptor_measures', HELPER)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)
DEST = HERE/'screening'
LEGACY = ['empty_prediction', 'reached_generation_limit', 'too_brief_vs_reference', 'ended_abruptly',
          'format_related_marker', 'list_like_format', 'technical_or_statistical_markers', 'any_flag']
EXTRA = ['preamble_candidate', 'stop_no_terminal_punctuation_candidate', 'endpoint_screen_union',
         'acronym_without_detected_expansion_candidate', 'new_acronym_without_detected_expansion_candidate',
         'list_markers_present', 'two_or_more_list_markers', 'source_copied_verbatim']
FLAGS = LEGACY + EXTRA


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summaries(frame, fields):
    records = []
    for key, group in frame.groupby(fields, sort=True):
        if len(fields) == 1:
            key = (key,) if not isinstance(key, tuple) else key
        row = dict(zip(fields, key))
        row['n'] = len(group)
        for flag in FLAGS:
            count = int(group[flag].sum())
            row[flag+'_n'] = count
            row[flag+'_pct'] = 100*count/len(group)
        for name in ['LEN_PRED', 'compression_ratio', 'copy_rate']:
            row['mean_'+name] = float(group[name].mean())
        records.append(row)
    return pd.DataFrame(records)


def main():
    if DEST.exists():
        raise FileExistsError(f'Refusing to replace screening: {DEST}')
    audit_path = ROOT/'audits/original_paper_statistics_20261022/methodology.json'
    history = {Path(name).as_posix(): digest for name,digest in json.loads(audit_path.read_text())['source_hashes'].items()}
    descriptor_proof_path = ROOT/'experiments/reviewer2_concern3/evaluation/historical_fixed/complete.json'
    descriptor_proof = json.loads(descriptor_proof_path.read_text())
    inputs = {p.relative_to(ROOT).as_posix(): sha(p) for p in [audit_path, descriptor_proof_path, HELPER,
        ROOT/'generate_systematic_error_analysis_512.py', HERE/'detectors.py', HERE/'METHODOLOGY.md']}
    gold_path = ROOT/'data/tsar2025/tsar2025_test_200.csv'
    if sha(gold_path) != descriptor_proof['input_sha256'][gold_path.relative_to(ROOT).as_posix()]:
        raise ValueError('TSAR gold changed')
    inputs[gold_path.relative_to(ROOT).as_posix()] = sha(gold_path)
    gold = pd.read_csv(gold_path, keep_default_na=False, dtype={'text_id':str})
    gold['base_id'] = gold.text_id.str.extract(r'^(\d+)')
    records = []
    full = {}
    for model,dataset,prompt,strategy in itertools.product(['llama','mixtral'], ['cochrane','plaba','tsar2025'],
            ['minimal','iso','iso_examples'], ['zero','one','few_random','few_metric']):
        short = 'llama3_1_8b' if model == 'llama' else 'mixtral_latest'
        path = ROOT/'outputs'/f'{model}_512'/f'predictions_{short}_{dataset}_{prompt}_{strategy}.csv'
        name = path.relative_to(ROOT).as_posix()
        if sha(path) != history[name]:
            raise ValueError(f'Historical prediction hash mismatch: {name}')
        test_path = ROOT/'data'/dataset/f'{dataset}_test.csv'
        test_name = test_path.relative_to(ROOT).as_posix()
        if sha(test_path) != descriptor_proof['input_sha256'][test_name]:
            raise ValueError('Test changed')
        inputs[name], inputs[test_name] = sha(path), sha(test_path)
        frame = pd.read_csv(path, keep_default_na=False, dtype={'text_id':str})
        test = pd.read_csv(test_path, keep_default_na=False, dtype={'text_id':str})
        if not frame[['text_id','original','reference']].equals(test[['text_id','original','reference']]):
            raise ValueError(f'Test alignment mismatch: {name}')
        for i,row in frame.iterrows():
            refs = [row.reference]
            if dataset == 'tsar2025':
                g = gold[gold.base_id == row.text_id]
                if len(g) != 2 or set(g.original) != {row.original}:
                    raise ValueError('TSAR reference/source mismatch')
                refs = g.reference.tolist()
            derived = helper.measures(row.original, row.prediction, refs)
            flags = classify_row(dict(dataset=dataset), dict(row.to_dict(), **derived))
            extra = extra_flags(row.original, row.prediction, row.done_reason)
            key = f'{model}/{dataset}/{prompt}/{strategy}/{i}'
            record = dict(instance_id=key, model=model, dataset=dataset, prompt=prompt, strategy=strategy,
                row_index=i, text_id=row.text_id, source_file=name, done_reason=row.done_reason,
                **derived, **{flag:int(flags[flag]) for flag in LEGACY}, **extra)
            record['endpoint_screen_union'] = bool(flags['ended_abruptly']) or extra['stop_no_terminal_punctuation_candidate']
            for flag in FLAGS:
                record[flag] = int(record[flag])
            record['unexpanded_acronyms'] = json.dumps(extra['unexpanded_acronyms'])
            record['new_unexpanded_acronyms'] = json.dumps(extra['new_unexpanded_acronyms'])
            record['prediction_opening'] = row.prediction[:200]
            record['prediction_ending'] = row.prediction[-200:]
            records.append(record)
            full[key] = dict(original=row.original, prediction=row.prediction, references_json=json.dumps(refs, ensure_ascii=False))
    items = pd.DataFrame(records)
    if len(items) != 8952 or not items.instance_id.is_unique:
        raise ValueError('Unexpected screening scope')
    by_configuration = summaries(items, ['model','dataset','prompt','strategy'])
    if len(by_configuration) != 72:
        raise ValueError('Missing configurations')
    # Check exact reproduction of the earlier, model-specific endpoint screens.
    prior_path = ROOT/'experiments/reviewer2_concern4/abrupt_endings/all_outputs_screening.csv'
    prior = pd.read_csv(prior_path, keep_default_na=False)
    inputs[prior_path.relative_to(ROOT).as_posix()] = sha(prior_path)
    subset = items[items.model == 'mixtral'].copy()
    subset['source_file'] = subset.source_file.map(lambda name: Path(name).name)
    compared = subset.merge(prior[['source_file','row_index','existing_detector_candidate','additional_punctuation_screen_candidate']],
                            on=['source_file','row_index'], validate='one_to_one')
    if len(compared) != 4476 or not np.array_equal(compared.ended_abruptly.astype(bool), compared.existing_detector_candidate.astype(bool)):
        raise ValueError('Legacy Mixtral endpoint counts changed')
    additional = compared.stop_no_terminal_punctuation_candidate.astype(bool) & ~compared.ended_abruptly.astype(bool)
    if not np.array_equal(additional, compared.additional_punctuation_screen_candidate.astype(bool)):
        raise ValueError('Broader endpoint screen changed')
    rng = np.random.default_rng(20261023)
    samples = []
    for model,dataset,flag in itertools.product(['llama','mixtral'], ['cochrane','plaba','tsar2025'],
            ['preamble_candidate','ended_abruptly','stop_no_terminal_punctuation_candidate','acronym_without_detected_expansion_candidate']):
        pool = items[(items.model == model) & (items.dataset == dataset) & items[flag].eq(1)]
        if len(pool):
            chosen = pool.iloc[int(rng.integers(len(pool)))].to_dict()
            samples.append(dict(sampled_flag=flag, **chosen, **full[chosen['instance_id']]))
    for name,digest in inputs.items():
        if sha(ROOT/name) != digest:
            raise ValueError(f'Input changed during audit: {name}')
    DEST.mkdir(parents=True, exist_ok=False)
    items.to_csv(DEST/'all_8952_flags.csv', index=False)
    by_configuration.to_csv(DEST/'by_configuration.csv', index=False)
    summaries(items, ['model','dataset']).to_csv(DEST/'by_model_dataset.csv', index=False)
    summaries(items, ['model','prompt']).to_csv(DEST/'by_model_prompt.csv', index=False)
    summaries(items, ['model','strategy']).to_csv(DEST/'by_model_strategy.csv', index=False)
    pd.DataFrame(samples).to_csv(DEST/'spot_check_sample.csv', index=False)
    proof = dict(status='complete', configurations=72, outputs=8952, automatic_indicators_not_confirmed_errors=True,
        input_sha256=inputs, driver_sha256=sha(Path(__file__)), predictions_verified_unchanged=True,
        legacy_mixtral_4476_rows_reproduced=True, spot_check_seed=20261023, spot_check_assignments=len(samples),
        ollama_calls=0, semantic_model_calls=0, new_seed_files_read=False)
    (DEST/'complete.json').write_text(json.dumps(proof,indent=2),encoding='utf-8')
    print(by_configuration.groupby('model')[['n','empty_prediction_n','reached_generation_limit_n','ended_abruptly_n','preamble_candidate_n','acronym_without_detected_expansion_candidate_n']].sum().to_string())
    print(f'Sample assignments: {len(samples)}; distinct outputs: {len(set(s["instance_id"] for s in samples))}')


if __name__ == '__main__':
    main()
