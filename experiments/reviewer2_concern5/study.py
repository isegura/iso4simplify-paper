"""Run frozen three-example per-input retrieval; dry-run unless --execute."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MODELS = {'llama':('llama3.1:8b','llama3_1_8b'), 'mixtral':('mixtral:latest','mixtral_latest')}
OPTIONS = dict(max_new_tokens=512,num_ctx=8192,temperature=0.0,seed=42,top_k=1,top_p=1.0,
               repeat_penalty=1.1,repeat_last_n=64,num_gpu=999,require_gpu=True,timeout=900)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate():
    manifest = json.loads((HERE/'experiment_manifest.json').read_text(encoding='utf-8'))
    if len(manifest['jobs']) != 18 or sum(j['n'] for j in manifest['jobs']) != 2238 or manifest['options'] != OPTIONS:
        raise ValueError('Study design changed')
    for name, digest in manifest['source_sha256'].items():
        if sha(ROOT/name) != digest:
            raise ValueError(f'Frozen input changed: {name}')
    return manifest


def runtime(model):
    import requests
    name = MODELS[model][0]
    def get(suffix):
        response = requests.get('http://localhost:11434'+suffix, timeout=30)
        response.raise_for_status(); return response.json()
    matches = [row for row in get('/api/tags')['models'] if row.get('name') == name or row.get('model') == name]
    provenance = ROOT/'experiments/focused_ablation'/('model_provenance.json' if model == 'llama' else 'mixtral/model_provenance.json')
    if len(matches) != 1 or matches[0]['digest'] != json.loads(provenance.read_text())['digest']:
        raise ValueError('Installed model differs from the original study; no automatic download')
    response = requests.post('http://localhost:11434/api/show', json={'model':name}, timeout=30)
    response.raise_for_status(); shown = response.json()
    info = dict(model=name,digest=matches[0]['digest'],version=get('/api/version'),
                **{key:shown.get(key) for key in ['details','template','parameters','system']})
    path = HERE/'runtime'/f'{model}.json'
    path.parent.mkdir(exist_ok=True)
    if path.exists() and json.loads(path.read_text()) != info:
        raise ValueError('Runtime changed within retrieval study')
    if not path.exists():
        path.write_text(json.dumps(info,indent=2),encoding='utf-8')


def run(model, dataset=None, execute=False, generator=None):
    manifest = validate()
    jobs = [j for j in manifest['jobs'] if j['model'] == model and (dataset is None or j['dataset'] == dataset)]
    print(f'{len(jobs)} configurations / {sum(j["n"] for j in jobs)} outputs; few-shot retrieval only.',flush=True)
    if not execute:
        print('DRY RUN: no Ollama calls.'); return
    if generator is None:
        sys.path.insert(0,str(ROOT))
        from model_utils import simplify_one_ollama
        generator = simplify_one_ollama
        runtime(model)
    selections = pd.read_csv(HERE/'selected_examples.csv',keep_default_na=False,dtype={'test_text_id':str,'training_text_id':str})
    prompt_index = pd.read_csv(HERE/'prompt_index.csv',keep_default_na=False)
    for job in jobs:
        output = ROOT/job['prediction_path']
        log = HERE/'logs'/model/(job['job_id']+'.json')
        log.parent.mkdir(parents=True,exist_ok=True)
        metadata = dict(job=job,options=OPTIONS,study_manifest_sha256=sha(HERE/'experiment_manifest.json'),
                        inference_sha256=sha(ROOT/'model_utils.py'),generation_schema=1)
        if log.exists():
            if json.loads(log.read_text()) != metadata:
                raise ValueError('Run provenance changed')
        else:
            if output.exists():
                raise ValueError('Prediction exists without execution metadata')
            log.write_text(json.dumps(metadata,indent=2),encoding='utf-8')
        test = pd.read_csv(ROOT/job['test_path'],keep_default_na=False,dtype={'text_id':str})
        completed = pd.read_csv(output,keep_default_na=False,dtype={'text_id':str}) if output.exists() else test.iloc[:0]
        if len(completed) > len(test) or not completed[['text_id','original','reference']].equals(test.iloc[:len(completed)][['text_id','original','reference']]):
            raise ValueError('Resume row alignment failed')
        if len(completed) and completed.context_budget_observed_warning.astype(bool).any():
            raise ValueError('A saved output has a context warning; inspect before resuming')
        marker = log.with_suffix('.complete.json')
        if marker.exists():
            proof = json.loads(marker.read_text())
            if len(completed) != len(test) or proof != dict(status='complete',rows=len(test),prediction_sha256=sha(output)):
                raise ValueError('Completed prediction changed')
            print(f'{job["job_id"]}: complete; verified, skipped.',flush=True)
            continue
        for row_index in range(len(completed),len(test)):
            row = test.iloc[row_index]
            entry = prompt_index[(prompt_index.dataset == job['dataset']) & (prompt_index.prompt == job['prompt']) & (prompt_index.row_index == row_index)]
            if len(entry) != 1:
                raise ValueError('Missing per-input prompt')
            path = ROOT/entry.prompt_path.iloc[0]
            instructions = path.read_text(encoding='utf-8')
            prediction,_,_,_,execution = generator(texto=row.original,instrucciones=instructions,
                model_name=job['ollama_model'],marker='SIMPLIFIED TEXT:',**OPTIONS)
            chosen = selections[(selections.dataset == job['dataset']) & (selections.test_row_index == row_index)].sort_values('rank')
            if len(chosen) != 3:
                raise ValueError('Invalid frozen selection')
            record = dict(row.to_dict(),prediction=prediction,**execution,model=job['ollama_model'],dataset=job['dataset'],
                prompt_type=job['prompt'],strategy='few_retrieval',generation_seed=42,repeat_penalty=1.1,repeat_last_n=64,
                retrieval_training_rows_json=json.dumps(chosen.training_row_index.tolist()),
                retrieval_training_ids_json=json.dumps(chosen.training_text_id.tolist()),
                retrieval_cosine_scores_json=json.dumps(chosen.cosine_similarity.tolist()),
                instructions_sha256=sha(path),context_budget_observed_warning=int(execution['prompt_eval_count'])+512>8192)
            output.parent.mkdir(parents=True,exist_ok=True)
            pd.DataFrame([record]).to_csv(output,mode='a',header=not output.exists(),index=False,encoding='utf-8')
            print(f'{job["job_id"]}: {row_index+1}/{len(test)} {execution.get("done_reason")}',flush=True)
            if record['context_budget_observed_warning']:
                raise RuntimeError('Observed prompt tokens + 512 exceed context. Output preserved; inspect before proceeding, do not silently trim examples.')
        marker.write_text(json.dumps(dict(status='complete',rows=len(test),prediction_sha256=sha(output)),indent=2),encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['validate','run'])
    parser.add_argument('--model',choices=MODELS)
    parser.add_argument('--dataset',choices=['cochrane','plaba','tsar2025'])
    parser.add_argument('--execute',action='store_true')
    args = parser.parse_args()
    if args.action == 'validate':
        validate(); print('18 configurations / 2238 outputs validated. No inference.')
    else:
        if not args.model:
            parser.error('run requires --model')
        run(args.model,args.dataset,args.execute)
