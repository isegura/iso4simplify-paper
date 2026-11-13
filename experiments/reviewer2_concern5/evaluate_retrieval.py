"""Evaluate certified complete retrieval outputs; validate-only by default."""
import argparse
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import sys
import time
import numpy as np
import pandas as pd
from study import HERE, ROOT, validate, sha


def load_job(job):
    path = ROOT/job['prediction_path']
    marker = HERE/'logs'/job['model']/(job['job_id']+'.complete.json')
    if not marker.exists():
        raise ValueError(f'Generation not certified complete: {job["job_id"]}')
    proof = json.loads(marker.read_text())
    if proof != dict(status='complete',rows=job['n'],prediction_sha256=sha(path)):
        raise ValueError('Generation certificate mismatch')
    frame = pd.read_csv(path,keep_default_na=False,dtype={'text_id':str})
    test = pd.read_csv(ROOT/job['test_path'],keep_default_na=False,dtype={'text_id':str})
    if len(frame) != job['n'] or not frame[['text_id','original','reference']].equals(test[['text_id','original','reference']]):
        raise ValueError('Prediction/test alignment failed')
    if frame.context_budget_observed_warning.astype(bool).any():
        raise ValueError('Context warning requires inspection before evaluation')
    refs = [[str(ref)] for ref in frame.reference]
    hashes = {p.relative_to(ROOT).as_posix():sha(p) for p in [path,marker,ROOT/job['test_path']]}
    if job['dataset'] == 'tsar2025':
        gold_path = ROOT/'data/tsar2025/tsar2025_test_200.csv'
        hashes[gold_path.relative_to(ROOT).as_posix()] = sha(gold_path)
        gold = pd.read_csv(gold_path,keep_default_na=False,dtype={'text_id':str})
        gold['base_id'] = gold.text_id.str.extract(r'^(\d+)')
        refs = []
        for row in frame.itertuples():
            group = gold[gold.base_id == row.text_id]
            if len(group) != 2 or set(group.original) != {row.original}:
                raise ValueError('TSAR alignment failed')
            refs.append(group.reference.tolist())
    return frame, refs, hashes


def evaluate(model=None,dataset=None,execute=False):
    manifest = validate()
    jobs = [j for j in manifest['jobs'] if (model is None or j['model'] == model) and (dataset is None or j['dataset'] == dataset)]
    for job in jobs:
        load_job(job)
    print(f'Validated {len(jobs)} complete retrieval configurations. No Ollama calls.',flush=True)
    if not execute:
        return
    sys.path.insert(0,str(ROOT))
    from focused_metric_runtime import configure, MODULE
    configure()
    old_validation = json.loads((ROOT/'experiments/focused_ablation/meaningbert_validation/verification.json').read_text())
    if not old_validation['all_match'] or old_validation['meaningbert_module_sha256'] != sha(MODULE):
        raise ValueError('MeaningBERT historical validation mismatch')
    def module(name,path):
        spec = importlib.util.spec_from_file_location(name,path)
        imported = importlib.util.module_from_spec(spec);spec.loader.exec_module(imported)
        return imported
    metrics = module('seed_metric_functions',ROOT/'experiments/reviewer2_concern2/evaluate_metrics.py')
    descriptors = module('descriptor_functions',ROOT/'experiments/reviewer2_concern2/evaluate_descriptors.py')
    versions = {name:importlib.metadata.version(name) for name in ['numpy','pandas','sacrebleu','evaluate','bert-score','textstat','torch','transformers']}
    code_paths = [Path(__file__),ROOT/'eval_utils.py',ROOT/'focused_metric_runtime.py',MODULE,
                  Path(metrics.__file__),Path(descriptors.__file__)]
    records = []
    for job in jobs:
        frame,refs,hashes = load_job(job)
        folder = HERE/'evaluation'/job['model']
        name = f"{job['dataset']}_{job['prompt']}_few_retrieval"
        checkpoint, item_path = folder/(name+'.json'), folder/(name+'_items.csv')
        fingerprint = dict(inputs=hashes,manifest=sha(HERE/'experiment_manifest.json'),versions=versions,
                           code={p.relative_to(ROOT).as_posix():sha(p) for p in code_paths})
        if checkpoint.exists():
            saved = json.loads(checkpoint.read_text())
            if saved['fingerprint'] != fingerprint or saved['items_sha256'] != sha(item_path):
                raise ValueError('Evaluation inputs/checkpoint changed; do not overwrite')
            records.append(saved['record']);continue
        print(f'START {job["job_id"]}',flush=True)
        start = time.perf_counter()
        items = metrics.compute_items(frame,refs)
        scores,signature = metrics.aggregate(items,frame.prediction.tolist(),refs)
        descriptions = pd.DataFrame([descriptors.measures(row.original,row.prediction,references) for row,references in zip(frame.itertuples(),refs)])
        items = pd.concat([items,descriptions],axis=1)
        items.insert(0,'text_id',frame.text_id);items.insert(0,'row_index',range(len(frame)))
        items['references_json'] = [json.dumps(r,ensure_ascii=False) for r in refs]
        items['done_reason'] = frame.done_reason
        record = dict(model=job['model'],dataset=job['dataset'],prompt=job['prompt'],strategy='few_retrieval',n=len(frame),**scores,
            empty_n=int(frame.prediction.str.strip().eq('').sum()),capped_n=int(frame.done_reason.eq('length').sum()))
        record.update({'mean_'+column:float(descriptions[column].mean()) for column in descriptions})
        if not np.isfinite(items[['SARI','BERTScore-F1','MeaningBERT','FKGL','FRE','LEN_PRED','compression_ratio','copy_rate']].to_numpy()).all():
            raise ValueError('Nonfinite evaluation scores')
        for path,digest in hashes.items():
            if sha(ROOT/path) != digest:
                raise ValueError('Prediction changed during evaluation')
        folder.mkdir(parents=True,exist_ok=True)
        items.to_csv(item_path,index=False)
        checkpoint.write_text(json.dumps(dict(status='complete',record=record,fingerprint=fingerprint,items_sha256=sha(item_path),
            bleu_signature=signature,elapsed_seconds=time.perf_counter()-start),indent=2),encoding='utf-8')
        records.append(record)
    folder = HERE/'evaluation/summaries';folder.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(records).to_csv(folder/f'{model or "all_models"}_{dataset or "all_datasets"}.csv',index=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model',choices=['llama','mixtral'])
    parser.add_argument('--dataset',choices=['cochrane','plaba','tsar2025'])
    parser.add_argument('--execute',action='store_true')
    args = parser.parse_args()
    evaluate(args.model,args.dataset,args.execute)
